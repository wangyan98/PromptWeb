#!/usr/bin/env python3
"""Download image and mp4 assets listed in 万物生.json.

The generated mapping file maps each local saved path to the original source
URL, which is useful when replacing remote URLs with local files later.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import ssl
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


DEFAULT_JSON = "\u4e07\u7269\u751f.json"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".avif"}
VIDEO_EXTS = {".mp4", ".webm", ".mov", ".m4v"}
CHUNK_SIZE = 1024 * 1024
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)

# Optional override used when a source host serves a broken/expired TLS chain.
SSL_CONTEXT: ssl.SSLContext | None = None


def use_insecure_ssl() -> None:
    """Skip TLS verification for hosts whose certificate chain is broken."""
    global SSL_CONTEXT
    SSL_CONTEXT = ssl._create_unverified_context()


def classify_url(url: str) -> str | None:
    """Return image/video when the URL points to a media file."""
    parsed = urlparse(url)
    path = unquote(parsed.path).lower()
    ext = Path(path).suffix
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    return None


def collect_media_urls(value: object) -> list[tuple[str, str]]:
    """Find unique image/video URLs anywhere in the JSON document."""
    found: list[tuple[str, str]] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)
        elif isinstance(node, str):
            url = node.strip()
            if not url.startswith(("http://", "https://")):
                return
            kind = classify_url(url)
            if kind is not None:
                found.append((url, kind))

    walk(value)

    unique: list[tuple[str, str]] = []
    seen: set[str] = set()
    for url, kind in found:
        if url not in seen:
            seen.add(url)
            unique.append((url, kind))
    return unique


def safe_filename(url: str, kind: str) -> str:
    """Build a stable, unique local filename for a source URL."""
    parsed_path = unquote(urlparse(url).path)
    original_name = Path(parsed_path).name
    stem = Path(original_name).stem if original_name else ""
    ext = Path(original_name).suffix.lower() if original_name else ""

    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._")
    if not safe_stem:
        safe_stem = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

    if ext not in IMAGE_EXTS and ext not in VIDEO_EXTS:
        ext = ".png" if kind == "image" else ".mp4"

    short_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    return f"{safe_stem}-{short_hash}{ext}"


def download_one(item: tuple[str, str, Path, float]) -> dict[str, object]:
    url, kind, local_path, timeout = item

    if local_path.is_file() and local_path.stat().st_size > 0:
        return {
            "url": url,
            "kind": kind,
            "local_path": str(local_path),
            "status": "skipped",
        }

    local_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = local_path.with_name(local_path.name + ".part")
    parsed = urlparse(url)
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": f"{parsed.scheme}://{parsed.netloc}/",
        "Accept": "*/*",
    }

    try:
        request = Request(url, headers=headers)
        with urlopen(
            request, timeout=timeout, context=SSL_CONTEXT
        ) as response, temp_path.open("wb") as out:
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                out.write(chunk)

        if temp_path.stat().st_size == 0:
            raise RuntimeError("downloaded file is empty")

        os.replace(temp_path, local_path)
        return {
            "url": url,
            "kind": kind,
            "local_path": str(local_path),
            "status": "downloaded",
        }
    except Exception as exc:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        return {
            "url": url,
            "kind": kind,
            "local_path": str(local_path),
            "status": "failed",
            "error": str(exc),
        }


def write_mapping(mapping_path: Path, mapping: dict[str, str]) -> None:
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(mapping, ensure_ascii=False, indent=2) + "\n"
    mapping_path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download image/mp4 assets and write a local->source mapping."
    )
    parser.add_argument(
        "--json",
        default=DEFAULT_JSON,
        help="Input JSON file (default: 万物生.json).",
    )
    parser.add_argument(
        "--output-dir",
        default="downloads",
        help="Directory that will contain images/ and videos/ (default: downloads).",
    )
    parser.add_argument(
        "--mapping",
        default="downloads/media_mapping.json",
        help="Output mapping file: local path -> source URL.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel downloads (default: 4).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-download timeout in seconds (default: 60).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Download only the first N unique URLs; 0 means no limit.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Skip TLS certificate verification (for hosts with broken certs).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.workers < 1:
        print("--workers must be at least 1", file=sys.stderr)
        return 2
    if args.insecure:
        use_insecure_ssl()

    json_path = Path(args.json)
    if not json_path.is_file():
        print(f"JSON file not found: {json_path}", file=sys.stderr)
        return 1

    try:
        data = json.loads(json_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Failed to read {json_path}: {exc}", file=sys.stderr)
        return 1

    media = collect_media_urls(data)
    if args.limit > 0:
        media = media[: args.limit]

    output_dir = Path(args.output_dir)
    tasks: list[tuple[str, str, Path, float]] = []
    image_count = 0
    video_count = 0
    for url, kind in media:
        local_path = output_dir / kind / safe_filename(url, kind)
        tasks.append((url, kind, local_path, args.timeout))
        if kind == "image":
            image_count += 1
        else:
            video_count += 1

    results: list[dict[str, object]] = []
    if args.workers == 1:
        for task in tasks:
            results.append(download_one(task))
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(download_one, task) for task in tasks]
            for future in as_completed(futures):
                results.append(future.result())

    mapping: dict[str, str] = {}
    failures: list[dict[str, object]] = []
    downloaded = 0
    skipped = 0
    for result in results:
        status = str(result["status"])
        if status == "failed":
            failures.append(result)
        else:
            mapping[str(result["local_path"])] = str(result["url"])
            if status == "downloaded":
                downloaded += 1
            else:
                skipped += 1

    mapping_path = Path(args.mapping)
    write_mapping(mapping_path, mapping)

    print(f"Collected {len(tasks)} unique media URLs: {image_count} images, {video_count} videos")
    print(f"Downloaded: {downloaded}, skipped existing: {skipped}, failed: {len(failures)}")
    print(f"Mapping written to: {mapping_path}")

    if failures:
        print("\nFailed downloads:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure['url']}: {failure['error']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
