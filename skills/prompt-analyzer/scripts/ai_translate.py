#!/usr/bin/env python3
"""Step 3 helper: Batch I/O utilities for AI analysis.

This script does NO translation, classification, or word extraction.
All intelligence comes from Claude following SKILL.md Step 3 instructions.

Modes:
  --split N     Read parsed JSON, split into batches of N prompts each
  --merge       Merge batch output files into final analysis JSON
  --validate    Validate analysis JSON structure

Usage:
  python ai_translate.py --split 30 < parsed.json
      → writes batch-001.json, batch-002.json, ... to --out-dir (default /tmp/prompt-batches)

  python ai_translate.py --merge --out-dir /tmp/prompt-batches
      → reads batch-*-out.json, merges, writes /tmp/prompt_analysis.json

  python ai_translate.py --validate /tmp/prompt_analysis.json
      → prints validation report to stderr, exits 0 if valid
"""

import json
import os
import sys
import glob
import re


def cmd_split(args):
    """Split parsed prompts into manageable batches for Claude to analyze."""
    batch_size = int(args[0]) if args else 30
    out_dir = os.environ.get('BATCH_OUT_DIR', '/tmp/prompt-batches')
    os.makedirs(out_dir, exist_ok=True)

    parsed = json.load(sys.stdin)
    prompts = parsed if isinstance(parsed, list) else parsed.get('prompts', parsed.get('new_prompts', []))

    total_batches = (len(prompts) + batch_size - 1) // batch_size
    for i in range(0, len(prompts), batch_size):
        batch_idx = i // batch_size + 1
        batch = prompts[i:i + batch_size]
        path = os.path.join(out_dir, f'batch-{batch_idx:03d}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                'batch': batch_idx,
                'total_batches': total_batches,
                'start_index': i,
                'prompts': batch,
            }, f, ensure_ascii=False, indent=2)
        print(f'  batch-{batch_idx:03d}.json: prompts {i+1}-{i+len(batch)} ({len(batch)} prompts)', file=sys.stderr)

    print(f'Split {len(prompts)} prompts → {total_batches} batches in {out_dir}', file=sys.stderr)
    print(json.dumps({'batches': total_batches, 'out_dir': out_dir}))


def cmd_merge(args):
    """Merge batch output files into final analysis JSON."""
    out_dir = os.environ.get('BATCH_OUT_DIR', '/tmp/prompt-batches')
    pattern = os.path.join(out_dir, 'batch-*-out.json')
    files = sorted(glob.glob(pattern))

    if not files:
        print(f'Error: no batch output files found matching {pattern}', file=sys.stderr)
        print('Expected files like batch-001-out.json (Claude writes these after analysis)', file=sys.stderr)
        sys.exit(1)

    all_prompts = []
    for fp in files:
        with open(fp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        prompts = data.get('new_prompts', data.get('prompts', []))
        all_prompts.extend(prompts)
        print(f'  {os.path.basename(fp)}: {len(prompts)} prompts', file=sys.stderr)

    output_path = os.environ.get('ANALYSIS_OUTPUT', '/tmp/prompt_analysis.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({'new_prompts': all_prompts}, f, ensure_ascii=False, indent=2)

    total_stmts = sum(len(p.get('statements', [])) for p in all_prompts)
    total_words = sum(len(s.get('words', [])) for p in all_prompts for s in p.get('statements', []))
    print(f'Merged {len(all_prompts)} prompts, {total_stmts} statements, {total_words} words → {output_path}', file=sys.stderr)
    print(json.dumps({'total_prompts': len(all_prompts), 'output': output_path}))


def cmd_validate(args):
    """Validate the structure of an analysis JSON file."""
    filepath = args[0]
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    prompts = data.get('new_prompts', data.get('prompts', []))
    if not prompts:
        print('FAIL: no prompts found in analysis JSON', file=sys.stderr)
        sys.exit(1)

    errors = []
    warnings = []
    for i, p in enumerate(prompts):
        pid = p.get('title', f'prompt-{i}')
        if not p.get('text_en_full') and not p.get('text_zh_full'):
            errors.append(f'[{pid}] missing both text_en_full and text_zh_full')
        if not p.get('statements'):
            errors.append(f'[{pid}] missing statements')
            continue
        for j, s in enumerate(p.get('statements', [])):
            sid = f'{pid}.stmt-{j}'
            if s.get('text_en') is None:
                errors.append(f'[{sid}] missing text_en')
            if s.get('sort_order') is None:
                errors.append(f'[{sid}] missing sort_order')
            if not s.get('text_zh'):
                warnings.append(f'[{sid}] missing text_zh (will be empty in UI)')
            for k, w in enumerate(s.get('words', [])):
                wid = f'{sid}.word-{k}'
                if not w.get('word_en'):
                    errors.append(f'[{wid}] missing word_en')
                if w.get('position_start') is None or w.get('position_end') is None:
                    errors.append(f'[{wid}] missing position_start/position_end')

    if errors:
        for e in errors:
            print(f'  ERROR: {e}', file=sys.stderr)
        print(f'FAIL: {len(errors)} validation errors', file=sys.stderr)
        sys.exit(1)

    for w in warnings:
        print(f'  WARN: {w}', file=sys.stderr)

    total_stmts = sum(len(p.get('statements', [])) for p in prompts)
    total_words = sum(len(s.get('words', [])) for p in prompts for s in p.get('statements', []))
    missing_zh = sum(1 for p in prompts for s in p.get('statements', []) if not s.get('text_zh'))
    print(f'OK: {len(prompts)} prompts, {total_stmts} stmts, {total_words} words, {missing_zh} missing ZH, {len(warnings)} warnings', file=sys.stderr)
    print(json.dumps({'valid': True, 'prompts': len(prompts), 'statements': total_stmts, 'words': total_words, 'missing_zh': missing_zh}))


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[1]
    args = sys.argv[2:]

    if mode == '--split':
        cmd_split(args)
    elif mode == '--merge':
        cmd_merge(args)
    elif mode == '--validate':
        if not args:
            print("Usage: ai_translate.py --validate <analysis_json>", file=sys.stderr)
            sys.exit(1)
        cmd_validate(args)
    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
