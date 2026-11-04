#!/usr/bin/env python3
"""Convert extracted/<lib>.json into PromptWeb import_batch format and (after
import) build the media manifest for later media import.

Usage:
  python3 build_import.py 万物生            # → /tmp/vp_import_万物生.json
  python3 build_import.py 万物生 --manifest <prompt_id_json>  # build manifest entry
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
EXTRACTED = BASE / "extracted"
MARKER_LINE = re.compile(r'^[\[【][^\]】]{1,24}[\]】]$')


def make_title(lib: str, seq: int, prompt: str) -> str:
    for line in prompt.split('\n'):
        line = line.strip()
        if not line or MARKER_LINE.match(line):
            continue
        text = re.sub(r'[*#`]', '', line).strip()
        if text:
            return f"{lib}-{seq:03d}·{text[:28]}"
    return f"{lib}-{seq:03d}"


def build_import(lib: str) -> dict:
    entries = json.load(open(EXTRACTED / f"{lib}.json"))
    prompts = []
    for seq, e in enumerate(entries, 1):
        p = e["prompt"]
        paras = [re.sub(r'[ \t]+', ' ', x).strip() for x in re.split(r'\n\s*\n', p)]
        paras = [x for x in paras if x]
        if not paras:
            paras = [p.strip()]
        prompts.append({
            "title": make_title(lib, seq, p),
            "text_en_full": p,
            "text_zh_full": p,  # 中文原文不译英文（英文段也保留原样，属生产用提示词）
            "category": lib,
            "source_file": f"{lib}.json",
            "statements": [
                {"text_en": para, "text_zh": para, "sort_order": i,
                 "type_id": None, "words": []}
                for i, para in enumerate(paras, 1)
            ],
        })
    return {"new_prompts": prompts}


def build_manifest(lib: str, id_by_title: dict) -> dict:
    """media manifest: PromptWeb prompt_id → media refs (URLs + local files)."""
    entries = json.load(open(EXTRACTED / f"{lib}.json"))
    # media_mapping.json: 本地路径 → 源 URL
    mapping = json.load(open(BASE / "media_mapping.json"))
    url_to_local = {v: k for k, v in mapping.items()}

    manifest = {}
    for seq, e in enumerate(entries, 1):
        title = make_title(lib, seq, e["prompt"])
        pid = id_by_title.get(title)
        if not pid:
            continue
        urls = e["image_urls"] + e["video_urls"]
        manifest[str(pid)] = {
            "library": lib,
            "node_id": e["node_id"],
            "kind": e["kind"],
            "model": e["model"],
            "task_id": e["task_id"],
            "image_urls": e["image_urls"],
            "video_urls": e["video_urls"],
            "local_files": [url_to_local[u] for u in urls if u in url_to_local],
        }
    return manifest


if __name__ == "__main__":
    lib = sys.argv[1]
    data = build_import(lib)
    out = f"/tmp/vp_import_{lib}.json"
    json.dump(data, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"{lib}: {len(data['new_prompts'])} prompts → {out}")
