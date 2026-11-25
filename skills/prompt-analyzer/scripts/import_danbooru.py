#!/usr/bin/env python3
"""Stream-import the Danbooru tag dictionary into the word book.

The source file is a large JSON array (~32.7万 entries). It is parsed
incrementally in small chunks and posted to the backend in batches, so the
whole file is never loaded into memory.

Usage:
    python import_danbooru.py --dry-run --limit 10
    python import_danbooru.py
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FILE = REPO_ROOT / "dataset" / "Danbooru词库-全量JSON(32.7万条).json"
DEFAULT_API = os.environ.get("PROMPT_API_URL", "http://localhost:8000")


def iter_json_array(path: Path, chunk_size: int = 1 << 16) -> Iterator[dict]:
    """Yield objects from a (possibly pretty-printed) JSON array, streaming."""
    decoder = json.JSONDecoder()
    buf = ""
    pos = 0
    started = False
    finished = False

    with path.open(encoding="utf-8") as fh:
        while True:
            while pos < len(buf):
                ch = buf[pos]
                if ch.isspace():
                    pos += 1
                    continue
                if not started:
                    if ch != "[":
                        raise ValueError(f"expected '[' at start, got {ch!r}")
                    started = True
                    pos += 1
                    continue
                if ch == ",":
                    pos += 1
                    continue
                if ch == "]":
                    pos += 1
                    finished = True
                    break
                if ch != "{":
                    raise ValueError(f"unexpected character {ch!r}")
                try:
                    obj, end = decoder.raw_decode(buf, pos)
                except ValueError:
                    break  # object spans chunks; read more before retrying
                yield obj
                pos = end

            if finished:
                trailing = buf[pos:].strip() + fh.read().strip()
                if trailing:
                    raise ValueError(f"unexpected trailing data after ']': {trailing[:80]!r}")
                return

            buf = buf[pos:]
            pos = 0
            chunk = fh.read(chunk_size)
            if chunk:
                buf += chunk
                continue

            if buf.strip():
                raise ValueError(f"unterminated JSON array, leftover: {buf[:80]!r}")
            return


def api_get_total(api: str, source: str = "danbooru") -> int:
    url = f"{api.rstrip('/')}/api/words/global?source={source}&page_size=1"
    with urllib.request.urlopen(url, timeout=60) as resp:
        return int(json.loads(resp.read().decode("utf-8"))["data"]["total"])


def api_post(url: str, payload: list[dict], retries: int = 3) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") != 0:
                raise RuntimeError(f"API error: {result}")
            return result["data"]
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            if attempt == retries - 1:
                raise
            print(f"  retry {attempt + 1}/{retries - 1} after error: {exc}", file=sys.stderr)
            time.sleep(1 + attempt)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    parser.add_argument("--api", default=DEFAULT_API)
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--limit", type=int, default=0, help="stop after N tags (for testing)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"file not found: {args.file}", file=sys.stderr)
        return 1

    url = f"{args.api.rstrip('/')}/api/words/import"
    batch: list[dict] = []
    parsed = 0
    inserted = 0
    batches = 0
    started_at = time.monotonic()
    previous_total = api_get_total(args.api) if not args.dry_run else None

    def flush_batch() -> None:
        nonlocal inserted, batches, previous_total, batch
        if not batch:
            return
        if args.dry_run:
            inserted += len(batch)
        else:
            data = api_post(url, batch)
            if previous_total is not None:
                inserted += max(0, data["total"] - previous_total)
            previous_total = data["total"]
        batches += 1
        batch = []
        if batches % 10 == 0:
            print(
                f"  parsed={parsed:,} batches={batches} inserted~={inserted:,} "
                f"elapsed={time.monotonic() - started_at:.1f}s",
                flush=True,
            )

    for obj in iter_json_array(args.file):
        word_en = (obj.get("name") or "").strip()
        if not word_en:
            continue
        batch.append({
            "word_en": word_en,
            "word_zh": (obj.get("cn_name") or "").strip(),
            "category": obj.get("category"),
            "post_count": obj.get("post_count"),
        })
        parsed += 1

        if args.limit and parsed >= args.limit:
            break
        if len(batch) >= args.batch_size:
            flush_batch()

    flush_batch()

    elapsed = time.monotonic() - started_at
    print(
        f"{'[dry-run] ' if args.dry_run else ''}done: parsed={parsed:,} batches={batches} "
        f"inserted={inserted:,} elapsed={elapsed:.1f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
