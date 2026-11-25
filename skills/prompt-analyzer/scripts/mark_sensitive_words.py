#!/usr/bin/env python3
"""Flag sensitive (NSFW) words with the is_hidden status bit.

Nothing is deleted: only prompt_words.is_hidden is updated.

The word book is streamed from PostgreSQL via COPY, so all rows are never
held in memory at once. Run without --apply first to inspect the matches.

Usage:
    python mark_sensitive_words.py                 # dry-run, shows samples
    python mark_sensitive_words.py --apply         # flips the status bit
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_API = os.environ.get("PROMPT_API_URL", "http://localhost:8000")

# English tag names: whole-word / stem matching, case-insensitive.
EN_PATTERNS = [
    r"\b(nsfw|explicit|porn\w*|hentai|erotic\w*|erotica|ecchi)\b",
    r"\b(nude|nudity|naked|topless|bottomless|undressed|exposed)\b",
    r"\b(breasts?|boobs?|tits?|nipples?|areola\w*)\b",
    r"\b(genital\w*|penis|phallus|dick|cock|erection|testicle\w*|scrotum)\b",
    r"\b(vagina\w*|pussy|vulva|clitoris|labia|pubic)\b",
    r"\b(sex|sexual|sexy|intercourse|copulation|coitus|fornication)\b",
    r"\b(fetish\w*|bdsm|bondage|sadism|masochism|dominatrix|submission)\b",
    r"\b(masturbat\w*|orgasm\w*|ejaculat\w*|cumshot|cum|cumming)\b",
    r"\b(fellatio|cunnilingus|blowjob|handjob|footjob|titfuck|paizuri|rimjob|anal|anus|oral)\b",
    r"\b(orgy|gangbang|threesome|foursome|rape|raping|molest\w*|incest)\b",
    r"\b(futanari|shemale|transsexual|lolicon|shotacon|loli|shota|toddlercon)\b",
    r"\b(scat|watersport\w*|peeing|piss\w*|enema)\b",
    r"\b(striptease|stripper|lingerie|panties|thong|no.bra|no.panties)\b",
]
EN_RE = [re.compile(p, re.IGNORECASE) for p in EN_PATTERNS]

# Chinese translations: substring matching.
ZH_KEYWORDS = [
    "全裸", "裸体", "裸身", "赤裸", "露点", "上空", "色情", "情色", "淫",
    "性交", "性行为", "性虐", "性器", "春药", "勃起", "阴茎", "阴道",
    "阴毛", "乳头", "乳晕", "射精", "精液", "自慰", "口交", "肛交",
    "群交", "乱伦", "强奸", "高潮脸", "成人向", "虐恋",
]


def match_reason(word_en: str, word_zh: str) -> str:
    for pattern in EN_RE:
        if pattern.search(word_en):
            return pattern.pattern
    for keyword in ZH_KEYWORDS:
        if keyword in word_zh:
            return f"中文:{keyword}"
    return ""


def stream_words() -> subprocess.Popen:
    sql = (
        "COPY (SELECT id, word_en, word_zh, source FROM prompt_words "
        "WHERE is_hidden = false) TO STDOUT WITH CSV"
    )
    return subprocess.Popen(
        [
            "docker", "compose", "exec", "-T", "postgres", "psql",
            "-U", "promptweb", "-d", "promptweb", "-c", sql,
        ],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )


def api_patch(url: str, word_ids: list[int], hidden: bool, retries: int = 3) -> int:
    body = json.dumps({"word_ids": word_ids, "hidden": hidden}).encode("utf-8")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="PATCH",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") != 0:
                raise RuntimeError(f"API error: {result}")
            return int(result["data"]["updated"])
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            if attempt == retries - 1:
                raise
            print(f"  retry {attempt + 1}: {exc}", file=sys.stderr)
            time.sleep(1 + attempt)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="actually flip is_hidden")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--sample-size", type=int, default=40)
    parser.add_argument("--limit", type=int, default=0, help="stop after N scanned rows")
    args = parser.parse_args()

    proc = stream_words()
    assert proc.stdout is not None
    scanned = 0
    matched_ids: list[int] = []
    samples: list[tuple[str, str, str, str]] = []
    by_source: dict[str, int] = {}

    reader = csv.reader(proc.stdout)
    for row in reader:
        if len(row) != 4:
            continue
        word_id, word_en, word_zh, source = row
        scanned += 1
        reason = match_reason(word_en, word_zh)
        if reason:
            matched_ids.append(int(word_id))
            by_source[source] = by_source.get(source, 0) + 1
            if len(samples) < args.sample_size:
                samples.append((word_en, word_zh, source, reason))
        if args.limit and scanned >= args.limit:
            break

    proc.stdout.close()
    stderr = proc.stderr.read() if proc.stderr else ""
    returncode = proc.wait()
    if returncode != 0:
        print(f"psql failed ({returncode}): {stderr[-1000:]}", file=sys.stderr)
        return 1

    print(f"扫描 {scanned:,} 个未隐藏词，命中 {len(matched_ids):,} 个：{by_source}")
    print("样例：")
    for word_en, word_zh, source, reason in samples:
        print(f"  [{source}] {word_en} / {word_zh}  <- {reason}")

    if not args.apply:
        print("\n[dry-run] 未修改任何数据。确认后加 --apply 执行。")
        return 0

    url = f"{DEFAULT_API.rstrip('/')}/api/words/hidden"
    updated = 0
    for i in range(0, len(matched_ids), args.batch_size):
        updated += api_patch(url, matched_ids[i:i + args.batch_size], True)
        if (i // args.batch_size + 1) % 20 == 0:
            print(f"  updated={updated:,}/{len(matched_ids):,}", flush=True)
    print(f"[applied] 已隐藏 {updated:,} 个词（仅修改 is_hidden，未删除）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
