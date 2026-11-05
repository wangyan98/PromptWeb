#!/usr/bin/env python3
"""把「角色设定」里多行混合描述按行拆成独立语句，便于按部位细分分类。

步骤：
  export : 导出待分类片段（拆行后）+ 片段与原文的映射 → /tmp/rolejob/pieces.jsonl
  apply  : 按 AI 分类结果写库：原语句替换为多个片段语句，并重排 sort_order

用法：
  python split_role_stmts.py export
  python split_role_stmts.py apply --dry-run
  python split_role_stmts.py apply --write
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys

CWD = "/Users/wangyan/Desktop/PromptWeb"
PSQL = ["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "promptweb", "-d", "promptweb"]
WORK = "/tmp/rolejob"
SRC_TYPE = "角色设定"
MIN_PIECE = 2  # 短于此长度的片段并入上一片


def sh(args):
    return subprocess.run(args, cwd=CWD, capture_output=True, text=True)


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def cmd_export(a):
    os.makedirs(WORK, exist_ok=True)
    sql = (
        "select json_agg(x)::text from (select s.id, s.prompt_id, s.sort_order, "
        f"s.text_zh from statements s join statement_types t on t.id=s.type_id where t.name='{SRC_TYPE}' "
        "order by s.prompt_id, s.sort_order) x;"
    )
    r = sh(PSQL + ["-t", "-A", "-c", sql])
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        sys.exit(1)
    rows = json.loads(r.stdout.strip() or "[]")
    print(f"角色设定语句 {len(rows)} 条", file=sys.stderr)

    # 拆行 → 片段
    plan = []        # [{id, prompt_id, sort_order, pieces:[text,...]}]
    piece_texts = set()
    for row in rows:
        text = row["text_zh"]
        lines = [ln.strip() for ln in text.split("\n")]
        lines = [ln for ln in lines if ln]
        # 合并极短行到前一片
        merged = []
        for ln in lines:
            if merged and len(ln) < MIN_PIECE:
                merged[-1] = merged[-1] + ln
            else:
                merged.append(ln)
        if len(merged) <= 1:
            merged = [text.strip()]
        plan.append({"id": row["id"], "prompt_id": row["prompt_id"],
                     "sort_order": row["sort_order"], "pieces": merged})
        for p in merged:
            piece_texts.add(p)

    total_pieces = sum(len(p["pieces"]) for p in plan)
    split_cnt = sum(1 for p in plan if len(p["pieces"]) > 1)
    print(f"拆行后片段 {total_pieces} 个（唯一 {len(piece_texts)}），需拆分语句 {split_cnt}/{len(plan)}",
          file=sys.stderr)

    with open(os.path.join(WORK, "plan.json"), "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=1)
    with open(os.path.join(WORK, "pieces.jsonl"), "w", encoding="utf-8") as f:
        for txt in sorted(piece_texts):
            f.write(json.dumps({"h": md5(txt), "t": txt[:400] if len(txt) > 400 else txt},
                               ensure_ascii=False) + "\n")
    print(json.dumps({"pieces": total_pieces, "unique": len(piece_texts), "dir": WORK}))


def cmd_apply(a):
    plan = json.load(open(os.path.join(WORK, "plan.json"), encoding="utf-8"))
    outdir = os.path.join(WORK, "out")
    mapping = {}
    for fn in sorted(os.listdir(outdir)):
        if fn.endswith(".json"):
            mapping.update(json.load(open(os.path.join(outdir, fn), encoding="utf-8")))
    print(f"分类映射 {len(mapping)} 条", file=sys.stderr)

    r = sh(PSQL + ["-t", "-A", "-F", "\t", "-c", "select id, name from statement_types;"])
    tid = {}
    for ln in r.stdout.strip().split("\n"):
        if "\t" in ln:
            i, nm = ln.split("\t", 1)
            tid[nm] = int(i)

    # 建缺失分类（插到「角色设定」之后）
    new_names = sorted({v for v in mapping.values() if v not in tid})
    if new_names:
        base = sh(PSQL + ["-t", "-A", "-c",
                          f"select sort_order from statement_types where name='{SRC_TYPE}';"]).stdout.strip()
        base = int(base) if base.isdigit() else 100
        sh(PSQL + ["-q", "-c",
                   f"update statement_types set sort_order = sort_order + {len(new_names)} where sort_order > {base};"])
        colors = ["#b0bec5", "#d7ccc8", "#f0f4c3", "#dcedc8", "#c5cae9", "#ffccbc", "#f8bbd0"]
        for i, nm in enumerate(new_names):
            esc = nm.replace("'", "''")
            sh(PSQL + ["-q", "-c",
                       f"insert into statement_types(name,color,sort_order) values('{esc}','{colors[i % len(colors)]}',{base + i + 1}) "
                       f"on conflict (name) do nothing;"])
        r = sh(PSQL + ["-t", "-A", "-F", "\t", "-c", "select id, name from statement_types;"])
        tid = {}
        for ln in r.stdout.strip().split("\n"):
            if "\t" in ln:
                i, nm = ln.split("\t", 1)
                tid[nm] = int(i)
        print(f"新建分类 {len(new_names)} 个: {', '.join(new_names)}")

    missing = 0
    for p in plan:
        for piece in p["pieces"]:
            if md5(piece) not in mapping:
                missing += 1
    print(f"缺分类片段 {missing}", file=sys.stderr)
    if a.dry_run:
        return
    if missing:
        print("存在缺分类片段，终止。", file=sys.stderr)
        sys.exit(1)

    # 逐 prompt 重建 sort_order
    by_prompt = {}
    for p in plan:
        by_prompt.setdefault(p["prompt_id"], []).append(p)

    sqls = []
    for pid, items in by_prompt.items():
        items.sort(key=lambda x: x["sort_order"])
        # 取出该 prompt 全部语句（含非角色类），按原顺序重排
        rr = sh(PSQL + ["-t", "-A", "-c",
                        f"select id, sort_order from statements where prompt_id={pid} order by sort_order, id;"])
        allst = []
        for ln in rr.stdout.strip().split("\n"):
            if "|" in ln:
                i, so = ln.split("|")
                allst.append(int(i))
        role_map = {p["id"]: p for p in items}
        new_order = []
        for sid in allst:
            if sid in role_map:
                new_order.extend(role_map[sid]["pieces"])
            else:
                new_order.append(("keep", sid))
        # 删除被拆的原语句，插入片段，重排
        del_ids = [p["id"] for p in items if len(p["pieces"]) > 1]
        # 单行语句：仅更新分类
        for p in items:
            if len(p["pieces"]) == 1:
                piece = p["pieces"][0]
                sqls.append(f"update statements set type_id={tid[mapping[md5(piece)]]} where id={p['id']};")
        final = []
        for item in new_order:
            if isinstance(item, tuple):
                final.append(("keep", item[1]))
            else:
                final.append(("new", item))
        # 执行：删除被拆语句
        if del_ids:
            sqls.append("delete from statements where id in (" + ",".join(map(str, del_ids)) + ");")
        # 插入新片段（先占位最后）
        for idx, item in enumerate(final):
            if item[0] == "new":
                txt = item[1].replace("'", "''")
                sqls.append(
                    f"insert into statements(prompt_id,text_en,text_zh,sort_order,type_id) values"
                    f"({pid},'{txt}','{txt}',{100000 + idx * 10},{tid[mapping[md5(item[1])]]});")
            else:
                sqls.append(f"update statements set sort_order={100000 + idx * 10} where id={item[1]};")
        # 统一回正
        sqls.append(
            "update statements s set sort_order = sub.rn from (select id, row_number() over "
            "(order by sort_order, id) * 10 as rn from statements where prompt_id=" + str(pid) +
            ") sub where sub.id = s.id;")

    script = "\n".join(["begin;"] + sqls + ["commit;"])
    path = os.path.join(WORK, "apply.sql")
    with open(path, "w", encoding="utf-8") as f:
        f.write(script)
    rr = subprocess.run(PSQL + ["-v", "ON_ERROR_STOP=1", "-q", "-f", "-"],
                        cwd=CWD, input=script, capture_output=True, text=True)
    if rr.returncode != 0:
        print("写库失败:", rr.stderr[:800], file=sys.stderr)
        sys.exit(1)
    print("写库完成")
    r = sh(PSQL + ["-t", "-A", "-c",
                   f"select count(*) from statements s join statement_types t on t.id=s.type_id where t.name='{SRC_TYPE}';"])
    print("角色设定语句数:", r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.set_defaults(func=cmd_export)
    p = sub.add_parser("apply")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--write", action="store_true")
    p.set_defaults(func=cmd_apply)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
