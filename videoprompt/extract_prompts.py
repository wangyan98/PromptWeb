#!/usr/bin/env python3
"""Extract prompts from videoprompt/*.json (canvas workflow exports + chat threads).

Outputs one extracted/<lib>.json per library, each entry:
{
  "node_id": str,          # source node/message id (for media manifest tracing)
  "kind": "video|image|text",
  "model": str,
  "label": str,
  "created_at": ms or None,
  "prompt": str,           # Chinese prompt, never translated
  "image_urls": [...],     # media refs found in node data (for later import)
  "video_urls": [...],
  "task_id": str | None,
}

Media is NOT imported here; media_manifest.json (built after DB import) plus
media_mapping.json (local path -> source URL) allow importing media later via
import_media.py.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

BASE = Path(__file__).resolve().parent
OUT = BASE / "extracted"
OUT.mkdir(exist_ok=True)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".avif"}
VIDEO_EXTS = {".mp4", ".webm", ".mov", ".m4v"}
MIN_LEN = 30

# canvas libraries: (json filename, library/category name)
CANVAS_LIBS = [
    ("万物生.json", "万物生"),
    ("万物生2.json", "万物生2"),
    ("元启录.json", "元启录"),
    ("元启录2.json", "元启录2"),
    ("浮光8.json", "浮光8"),
    ("浮光火星1.json", "浮光火星1"),
]
CHAT_LIBS = [("丧尸清道夫.json", "丧尸清道夫")]


def media_kind(url: str) -> str | None:
    path = unquote(urlparse(url).path).lower()
    ext = Path(path).suffix
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    return None


def collect_urls(value) -> tuple[list[str], list[str]]:
    """Walk a node's data and collect unique image/video URLs."""
    imgs, vids, seen = [], [], set()

    def walk(node):
        if isinstance(node, dict):
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)
        elif isinstance(node, str):
            url = node.strip()
            if not url.startswith(("http://", "https://")) or url in seen:
                return
            kind = media_kind(url)
            if kind == "image":
                seen.add(url)
                imgs.append(url)
            elif kind == "video":
                seen.add(url)
                vids.append(url)

    walk(value)
    return imgs, vids


def extract_canvas(lib_file: str, lib_name: str) -> list[dict]:
    raw = json.load(open(BASE / lib_file))
    d = raw.get("data", raw)
    nodes = d.get("nodes") or []
    entries, seen = [], set()
    for n in nodes:
        dd = n.get("data") or {}
        p = dd.get("prompt")
        kind = n.get("type")
        if not (isinstance(p, str) and len(p.strip()) > MIN_LEN):
            # text 节点的生成结果也可能整段是提示词
            if kind == "text" and isinstance(dd.get("result"), str) and len(dd["result"].strip()) > MIN_LEN:
                p = dd["result"]
            else:
                continue
        p = p.strip()
        if p in seen:
            continue
        seen.add(p)
        imgs, vids = collect_urls(dd)
        created = dd.get("createdAt")
        entries.append({
            "node_id": n.get("id"),
            "kind": kind if kind in ("video", "image") else "text",
            "model": dd.get("modelName") or dd.get("model") or "",
            "label": dd.get("label") or "",
            "created_at": created,
            "prompt": p,
            "image_urls": imgs,
            "video_urls": vids,
            "task_id": dd.get("taskId"),
        })
    # 按创建时间稳定排序
    entries.sort(key=lambda e: (e["created_at"] or 0))
    return entries


DATA_BLOB = re.compile(r'\{"prompt":"(.+?)"\}(?=["}])')


def extract_chat(lib_file: str, lib_name: str) -> list[dict]:
    """丧尸清道夫: 聊天线程, prompt 藏在 message.content[].data 的 JSON 里."""
    raw = json.load(open(BASE / lib_file))
    d = raw.get("data", raw)
    thread = d.get("thread") or {}
    entries, seen = [], set()

    def walk(node, msg_id):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "data" and isinstance(v, str):
                    try:
                        obj = json.loads(v)
                    except Exception:
                        obj = None
                    if isinstance(obj, dict) and isinstance(obj.get("prompt"), str) \
                            and len(obj["prompt"].strip()) > MIN_LEN:
                        p = obj["prompt"].strip()
                        if p not in seen:
                            seen.add(p)
                            imgs, vids = collect_urls(node)
                            entries.append({
                                "node_id": msg_id,
                                "kind": "text",
                                "model": obj.get("model") or "",
                                "label": obj.get("sub_type") or "",
                                "created_at": None,
                                "prompt": p,
                                "image_urls": imgs,
                                "video_urls": vids,
                                "task_id": None,
                            })
                walk(v, msg_id)
        elif isinstance(node, list):
            for child in node:
                walk(child, msg_id)

    for run in thread.get("run_list") or []:
        for entry in run.get("entry_list") or []:
            msg = entry.get("message") or {}
            walk(msg.get("content"), msg.get("message_id"))
    return entries


def main():
    summary = {}
    for lib_file, lib_name in CANVAS_LIBS:
        entries = extract_canvas(lib_file, lib_name)
        json.dump(entries, open(OUT / f"{lib_name}.json", "w"), ensure_ascii=False, indent=1)
        kinds = {}
        for e in entries:
            kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
        summary[lib_name] = len(entries)
        print(f"{lib_name}: {len(entries)} prompts {kinds}")
    for lib_file, lib_name in CHAT_LIBS:
        entries = extract_chat(lib_file, lib_name)
        json.dump(entries, open(OUT / f"{lib_name}.json", "w"), ensure_ascii=False, indent=1)
        summary[lib_name] = len(entries)
        print(f"{lib_name}: {len(entries)} prompts (chat)")
    print("TOTAL:", sum(summary.values()))


if __name__ == "__main__":
    main()
