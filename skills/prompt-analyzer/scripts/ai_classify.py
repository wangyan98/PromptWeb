#!/usr/bin/env python3
"""AI 语句分类流水线（替代关键词规则分类）。

流程：
  1. split  : 从未分类语句导出唯一文本 → 切成批次文件（供 AI 逐条判断）
  2. apply  : 读 AI 输出 → 汇总分类名 → 建缺失类型 → 回写数据库

用法：
  # 导出批次（每批 500 条，单条截断 400 字符）
  python ai_classify.py split --batch-size 500 --max-chars 400

  # 查看批次清单
  python ai_classify.py split --list

  # 汇总 AI 结果（先 dry-run 看分布）
  python ai_classify.py apply --dry-run

  # 真正写入（自动创建不存在的新分类）
  python ai_classify.py apply --write
"""

import argparse
import json
import os
import subprocess
import sys

WORK = "/tmp/typejob"
OUT = os.path.join(WORK, "out")
PSQL = ["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "promptweb", "-d", "promptweb"]
CWD = "/Users/wangyan/Desktop/PromptWeb"

# 已存在的分类（用于给 AI 参考、apply 时判断是否需要新建）
EXISTING = [
    "固定开头", "光照氛围", "镜头构图", "场景主体", "材质细节", "画质风格",
    "色彩色调", "环境背景", "分镜", "动作", "构图", "运镜", "光影",
    "导演风格", "特效", "全局设定", "角色技能", "负面提示词", "参考画师",
    "参考素材", "音效台词", "角色设定",
    "结构标记", "参数设置", "画面文字", "设定图", "情绪表情", "图像编辑",
    "使用说明", "氛围基调",
]

# 新分类配色池（按顺序取用）
COLORS = ["#7986cb", "#4fc3f7", "#ffb74d", "#81c784", "#e57373", "#ba68c8",
          "#90a4ae", "#f06292", "#4db6ac", "#ff7043", "#ffd54f", "#4dd0e1",
          "#7e57c2", "#b0bec5", "#d4e157", "#ef9a9a", "#64b5f6", "#ffab91",
          "#78909c", "#8d6e63", "#26a69a", "#ec407a", "#5c6bc0"]


def sh(args, **kw):
    return subprocess.run(args, cwd=CWD, capture_output=True, text=True, **kw)


def type_filter_sql(a):
    """生成 WHERE 片段：按源分类名过滤，默认未分类。"""
    if a.from_types:
        names = ",".join("'" + n.replace("'", "''") + "'" for n in a.from_types.split(","))
        return (f" s join statement_types t on t.id=s.type_id where t.name = any(array[{names}]) ",
                f" s.type_id in (select id from statement_types where name = any(array[{names}])) ")
    return " s where s.type_id is null ", " s.type_id is null "


def cmd_split(a):
    work = a.work
    out = os.path.join(work, "out")
    os.makedirs(work, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    where, _ = type_filter_sql(a)
    sql = (
        "select md5(s.text_zh) || E'\\t' || replace(regexp_replace(s.text_zh, '[\\r\\n\\t]+', ' ', 'g'), "
        f"'\\\\', '/') from statements{where} group by 1 order by 1;"
    )
    r = sh(PSQL + ["-t", "-A", "-c", sql])
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        sys.exit(1)
    rows = [ln for ln in r.stdout.split("\n") if "\t" in ln]
    print(f"未分类唯一文本: {len(rows)} 条", file=sys.stderr)

    bs = a.batch_size
    n = 0
    for i in range(0, len(rows), bs):
        chunk = rows[i:i + bs]
        idx = i // bs + 1
        path = os.path.join(work, f"batch-{idx:03d}.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for ln in chunk:
                h, txt = ln.split("\t", 1)
                txt = txt.strip()
                if len(txt) > a.max_chars:
                    txt = txt[:a.max_chars] + "…"
                f.write(json.dumps({"h": h, "t": txt}, ensure_ascii=False) + "\n")
        n = idx
    print(json.dumps({"batches": n, "dir": work, "size": bs}))


def cmd_apply(a):
    out = os.path.join(a.work, "out")
    files = sorted(f for f in os.listdir(out) if f.endswith(".json")) if os.path.isdir(out) else []
    mapping = {}
    bad = []
    for fn in files:
        try:
            d = json.load(open(os.path.join(out, fn), encoding="utf-8"))
        except Exception as e:
            bad.append((fn, str(e)))
            continue
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, str) and v.strip():
                    mapping[k.strip()] = v.strip()
    print(f"结果文件 {len(files)} 个，映射 {len(mapping)} 条，坏文件 {len(bad)}", file=sys.stderr)
    for fn, e in bad:
        print(f"  坏: {fn} {e}", file=sys.stderr)

    from collections import Counter
    cnt = Counter(mapping.values())
    print("\n分类分布（按条数）:")
    for name, c in cnt.most_common():
        mark = "" if name in EXISTING else "  [新]"
        print(f"  {c:6d}  {name}{mark}")
    print(f"\n不同分类名: {len(cnt)}，其中新增: {sum(1 for k in cnt if k not in EXISTING)}")

    if a.dry_run:
        return

    # 1. 建缺失分类
    r = sh(PSQL + ["-t", "-A", "-c", "select name, sort_order from statement_types order by sort_order;"])
    exist = {}
    maxsort = 0
    for ln in r.stdout.strip().split("\n"):
        if "|" in ln:
            nm, so = ln.rsplit("|", 1)
            exist[nm] = int(so)
            maxsort = max(maxsort, int(so))
    added = []
    ci = 0
    # 可选：把新分类插到某个已有分类之后（后续分类顺次后移）
    base_sort = None
    if a.insert_after:
        rr = sh(PSQL + ["-t", "-A", "-c",
                        f"select sort_order from statement_types where name='{a.insert_after.replace(chr(39), chr(39)*2)}';"])
        if rr.stdout.strip().isdigit():
            base_sort = int(rr.stdout.strip())
    new_names = [n for n in cnt if n not in exist]
    if base_sort is not None and new_names:
        sh(PSQL + ["-q", "-c",
                   f"update statement_types set sort_order = sort_order + {len(new_names)} where sort_order > {base_sort};"])
        for idx, name in enumerate(new_names):
            esc = name.replace("'", "''")
            color = COLORS[ci % len(COLORS)]
            ci += 1
            sql = (f"insert into statement_types(name,color,sort_order) values('{esc}','{color}',{base_sort + idx + 1}) "
                   f"on conflict (name) do nothing;")
            rr = sh(PSQL + ["-q", "-c", sql])
            if rr.returncode != 0:
                print(f"建分类失败 {name}: {rr.stderr}", file=sys.stderr)
            else:
                added.append(name)
    else:
        for name in new_names:
            maxsort += 1
            color = COLORS[ci % len(COLORS)]
            ci += 1
            esc = name.replace("'", "''")
            sql = (f"insert into statement_types(name,color,sort_order) values('{esc}','{color}',{maxsort}) "
                   f"on conflict (name) do nothing;")
            rr = sh(PSQL + ["-q", "-c", sql])
            if rr.returncode != 0:
                print(f"建分类失败 {name}: {rr.stderr}", file=sys.stderr)
            else:
                added.append(name)
    print(f"新建分类 {len(added)} 个: {', '.join(added)}")

    # 2. 写回语句（按文本 md5 匹配，一次 update 全部同文本语句；仅限源分类内）
    r = sh(PSQL + ["-t", "-A", "-F", "\t", "-c", "select id, name from statement_types;"])
    tid = {}
    for ln in r.stdout.strip().split("\n"):
        if "\t" in ln:
            i, nm = ln.split("\t", 1)
            tid[nm] = int(i)

    _, cond = type_filter_sql(a)
    lines = []
    for h, name in mapping.items():
        t = tid.get(name)
        if t is None or "'" in h:
            continue
        lines.append(f"('{h}'::text,{t}::int)")
    chunk = 2000
    total = 0
    for i in range(0, len(lines), chunk):
        vals = ",".join(lines[i:i + chunk])
        sql = (f"update statements s set type_id = v.t from (values {vals}) as v(h,t) "
               f"where md5(s.text_zh) = v.h and{cond};")
        rr = sh(PSQL + ["-q", "-c", sql])
        if rr.returncode != 0:
            print(f"更新失败: {rr.stderr[:300]}", file=sys.stderr)
            sys.exit(1)
        total += chunk
    print(f"已写入 {min(total, len(lines))} 个文本映射")

    r = sh(PSQL + ["-t", "-A", "-c", "select count(*) filter (where type_id is null), count(*) from statements;"])
    print("剩余未分类/总语句:", r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split")
    s.add_argument("--batch-size", type=int, default=500)
    s.add_argument("--max-chars", type=int, default=400)
    s.add_argument("--from-types", help="逗号分隔的源分类名（默认导出未分类语句）")
    s.add_argument("--work", default="/tmp/typejob", help="批次工作目录")
    s.set_defaults(func=cmd_split)
    p = sub.add_parser("apply")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--write", action="store_true")
    p.add_argument("--from-types", help="只回写这些源分类内的语句（默认只动未分类）")
    p.add_argument("--insert-after", help="新分类插入到该分类名之后（后续 sort 顺移）")
    p.add_argument("--work", default="/tmp/typejob", help="批次工作目录")
    p.set_defaults(func=cmd_apply)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
