#!/usr/bin/env python3
"""Import media (images/videos) for videoprompt prompts already in PromptWeb.

Reads videoprompt/media_manifest.json (built by build_import.py --manifest),
resolves each URL (download) or local file (via media_mapping.json), and
uploads through the PromptWeb API.

Usage:
  python3 import_media.py --library 万物生 --kind image            # 导入图片
  python3 import_media.py --library 万物生 --kind video           # 视频(需后端支持)
  python3 import_media.py --all --kind image --dry-run            # 预览
  python3 import_media.py --prompt-id 14700 --kind image          # 单个 prompt

Notes:
- images: POST /api/prompts/{id}/images (已支持)
- videos: 后端 PromptImage 目前无媒体类型字段，视频暂存 manifest 中，
  待后端扩展 media_type 后把 upload_one 的 kind='video' 分支打开即可。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
API = "http://localhost:8000"
MANIFEST = BASE / "media_manifest.json"
MAPPING = BASE / "media_mapping.json"

MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".webp": "image/webp", ".gif": "image/gif", ".mp4": "video/mp4",
        ".webm": "video/webm", ".mov": "video/quicktime"}


def api_get(path):
    return json.load(urlopen(API + path))["data"]


def resolve_media(entry: dict, kind: str) -> list[tuple[str, str, str]]:
    """Return [(source, local_path_or_None, url)] for the requested kind."""
    url_to_local = {v: k for k, v in json.load(open(MAPPING)).items()}
    out = []
    for url in entry.get(f"{kind}_urls", []):
        local = url_to_local.get(url)
        if local and not Path(local).is_absolute():
            # mapping 里的相对路径是 Windows 风格 (库\image\xxx.png)
            cand = BASE / local.replace("\\", "/")
            local = str(cand) if cand.exists() else local
        if local and not Path(local).exists():
            local = None  # 本地缺失，退回下载
        out.append((url, local, url))
    return out


def download(url: str) -> str:
    ext = Path(urlparse(url).path).suffix or ".bin"
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=60) as resp, open(tmp.name, "wb") as f:
        while chunk := resp.read(1 << 20):
            f.write(chunk)
    return tmp.name


def upload_one(prompt_id: int, file_path: str, kind: str) -> dict:
    ext = Path(file_path).suffix.lower()
    mime = MIME.get(ext, "application/octet-stream")
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{API}/api/prompts/{prompt_id}/images",
         "-F", f"file=@{file_path};type={mime}"],
        capture_output=True, text=True, timeout=120)
    return json.loads(r.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--library")
    ap.add_argument("--prompt-id", type=int)
    ap.add_argument("--kind", choices=["image", "video"], default="image")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    manifest = json.load(open(MANIFEST))
    targets = {}
    for pid, entry in manifest.items():
        if args.prompt_id and int(pid) != args.prompt_id:
            continue
        if args.library and entry["library"] != args.library:
            continue
        if not (args.all or args.prompt_id or args.library):
            continue
        if args.kind == "video" and not entry.get("video_urls"):
            continue
        targets[pid] = entry

    print(f"targets: {len(targets)} prompts, kind={args.kind}")
    if args.dry_run:
        for pid, e in list(targets.items())[:10]:
            n = len(e.get(f"{args.kind}_urls", []))
            print(f"  {pid} [{e['kind']}] {e['library']}: {n} {args.kind}(s)")
        return

    ok = fail = skipped = 0
    for i, (pid, entry) in enumerate(targets.items()):
        existing = api_get(f"/api/prompts/{pid}").get("images") or []
        if existing:
            skipped += 1
            continue
        media = resolve_media(entry, args.kind)
        for url, local, _ in media[:6]:  # 每个 prompt 最多挂 6 张/段
            try:
                tmp = None
                path = local or (tmp := download(url))
                resp = upload_one(int(pid), path, args.kind)
                if resp.get("code") == 0:
                    ok += 1
                else:
                    fail += 1
                    print(f"  FAIL {pid}: {str(resp)[:120]}")
                if tmp:
                    Path(tmp).unlink(missing_ok=True)
            except Exception as exc:
                fail += 1
                print(f"  ERROR {pid} {url[:60]}: {exc}")
        if args.limit and i + 1 >= args.limit:
            break
    print(f"done: ok={ok}, fail={fail}, skipped(had media)={skipped}")


if __name__ == "__main__":
    sys.exit(main())
