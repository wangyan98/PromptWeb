#!/usr/bin/env python3
"""Parse a prompt data file (xlsx/csv/json) — file-reading only, no column detection.

All intelligence (column mapping, key identification) comes from Claude.
This script is a dumb I/O tool with three modes:

  --inspect <file>     Read file, print a compact profile: headers, sample rows, row count.
                       Claude reads this output and decides which columns are which.

  --extract <file>     Read file, extract rows using column indices provided via CLI flags:
                       --en N --zh M --title P --cat Q --sheet NAME
                       --zh is required (Chinese prompt). --en is optional (English prompt).
                       Outputs clean JSON array to stdout.

  --dir <dir_path>     Scan directory recursively for single-prompt-per-file xlsx files
                       (label-value format: col C=key, col D=value).
                       Extracts category from subdirectory name, title from filename.
                       Supports --limit N for testing.

Usage:
  python parse_file.py --inspect data.xlsx
      → prints metadata JSON with headers and first 5 rows

  python parse_file.py --extract data.xlsx --en 1 --zh 2 --title 0
      → prints prompt JSON array using Claude's column choices

  python parse_file.py --dir ./SD-prompts/ --limit 5
      → prints parsed JSON for first 5 files found
"""

import json
import sys
import os
import csv
import re
from pathlib import Path


# ── shared file reading ────────────────────────────────────────────

def read_xlsx_raw(filepath):
    """Read xlsx, return (sheet_name, headers, all_rows)."""
    try:
        import openpyxl
    except ImportError:
        print("Error: openpyxl not installed. Run: pip install openpyxl", file=sys.stderr)
        sys.exit(1)

    wb = openpyxl.load_workbook(filepath, data_only=True)
    sheets_data = {}
    for sn in wb.sheetnames:
        ws = wb[sn]
        rows = []
        for row in ws.iter_rows(values_only=True):
            if any(cell is not None for cell in row):
                rows.append([str(cell) if cell is not None else '' for cell in row])
        if rows:
            sheets_data[sn] = rows

    if not sheets_data:
        print("Error: no data found in any sheet", file=sys.stderr)
        sys.exit(1)

    # Pick data sheet: the one with most rows, skipping obvious meta sheets
    skip_kw = ['封面', '说明', '公式', '模板', 'template', 'cover', 'summary', 'intro', 'readme']
    candidates = {n: r for n, r in sheets_data.items()
                  if not any(kw in n.lower() for kw in skip_kw)}
    if not candidates:
        candidates = sheets_data
    best_sheet = max(candidates, key=lambda n: len(candidates[n]))
    rows = candidates[best_sheet]

    if len(rows) < 2:
        print(f"Error: sheet '{best_sheet}' has no data rows", file=sys.stderr)
        sys.exit(1)

    headers = rows[0]
    data_rows = rows[1:]
    return best_sheet, sheets_data, headers, data_rows


def read_csv_raw(filepath):
    """Read csv, return (None, None, headers, all_rows)."""
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1']
    rows = None
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                rows = list(csv.reader(f))
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    if rows is None:
        print("Error: could not decode CSV with any encoding", file=sys.stderr)
        sys.exit(1)
    if len(rows) < 2:
        print("Error: CSV has no data rows", file=sys.stderr)
        sys.exit(1)
    return None, None, rows[0], rows[1:]


def read_json_raw(filepath):
    """Read json, return normalized rows. JSON is its own header — no inspect needed."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, dict):
        for key in ['prompts', 'data', 'items']:
            if key in data and isinstance(data[key], list):
                data = data[key]
                break
        else:
            data = [data]
    if not isinstance(data, list):
        print("Error: JSON must be an array or object with array field", file=sys.stderr)
        sys.exit(1)

    # For JSON, we just list all unique top-level keys
    keys = set()
    for item in data[:10]:
        if isinstance(item, dict):
            keys.update(item.keys())
    return list(keys), data


# ── inspect mode ────────────────────────────────────────────────────

def cmd_inspect(filepath):
    """Print a compact profile Claude can read to decide column mapping."""
    ext = Path(filepath).suffix.lower()

    if ext == '.json':
        keys, data = read_json_raw(filepath)
        samples = []
        for item in data[:5]:
            if isinstance(item, dict):
                samples.append({k: str(v)[:120] if v else '' for k, v in item.items()})
        result = {
            'format': 'json',
            'total_rows': len(data),
            'keys': sorted(keys),
            'sample_rows': samples,
        }
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        return

    if ext in ('.xlsx', '.xls'):
        sheet, all_sheets, headers, data_rows = read_xlsx_raw(filepath)
        other_sheets = [s for s in all_sheets if s != sheet]
    elif ext == '.csv':
        sheet, all_sheets, headers, data_rows = read_csv_raw(filepath)
        other_sheets = []
    else:
        print(f"Error: unsupported file type: {ext}. Supported: .xlsx, .xls, .csv, .json", file=sys.stderr)
        sys.exit(1)

    samples = []
    for row in data_rows[:5]:
        samples.append([str(c)[:200] if c else '' for c in row])

    result = {
        'format': ext.lstrip('.'),
        'sheet': sheet,
        'other_sheets': other_sheets if all_sheets else [],
        'total_rows': len(data_rows),
        'headers': [str(h).strip() if h else '' for h in headers],
        'sample_rows': samples,
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


# ── extract mode ────────────────────────────────────────────────────

def split_en_into_statements(en_text):
    """Split English prompt by commas and parentheses (SD-style tags), preserving whitespace."""
    # Split on commas, (, and ) — keep meaningful fragments
    parts = [s.strip() for s in re.split(r'[,()]', en_text) if s.strip()]
    return [{'text_en': text, 'sort_order': i + 1} for i, text in enumerate(parts)]


def cmd_extract(filepath, en_idx, zh_idx, title_idx, cat_idx, sheet_name):
    """Extract rows using Claude-chosen column indices, output prompt JSON."""
    ext = Path(filepath).suffix.lower()

    if ext == '.json':
        _, data = read_json_raw(filepath)
        prompts = []
        for item in data:
            if not isinstance(item, dict):
                continue
            keys = sorted(item.keys())

            def pick(idx, field_keys):
                if idx is not None and 0 <= idx < len(field_keys):
                    val = item.get(field_keys[idx], '')
                    return str(val).strip() if val else ''
                # try positional index against keys list
                if idx is not None and idx < len(keys):
                    val = item.get(keys[idx], '')
                    return str(val).strip() if val else ''
                return ''

            en_text = pick(en_idx, []) or item.get('text_en_full', item.get('text_en', item.get('prompt', '')))
            zh_text = pick(zh_idx, []) or item.get('text_zh_full', item.get('text_zh', item.get('chinese', '')))
            if not zh_text:
                continue
            title = pick(title_idx, []) or item.get('title', item.get('name', ''))
            category = pick(cat_idx, []) or item.get('category', item.get('cat', ''))

            prompts.append({
                'title': str(title).strip() if title else '',
                'text_en_full': str(en_text).strip(),
                'text_zh_full': str(zh_text).strip() if zh_text else '',
                'category': str(category).strip() if category else '',
                'statements': split_en_into_statements(str(en_text)),
            })

        json.dump(prompts, sys.stdout, ensure_ascii=False, indent=2)
        return

    # xlsx / csv
    if ext in ('.xlsx', '.xls'):
        actual_sheet, all_sheets, headers, data_rows = read_xlsx_raw(filepath)
        if sheet_name and sheet_name in all_sheets:
            rows = all_sheets[sheet_name]
            if len(rows) >= 2:
                headers = rows[0]
                data_rows = rows[1:]
    elif ext == '.csv':
        _, _, headers, data_rows = read_csv_raw(filepath)
    else:
        print(f"Error: unsupported file type: {ext}", file=sys.stderr)
        sys.exit(1)

    def get_cell(row, idx):
        if idx is not None and 0 <= idx < len(row):
            return str(row[idx]).strip()
        return ''

    prompts = []
    for row in data_rows:
        if all(not c or not str(c).strip() for c in row):
            continue
        en_text = get_cell(row, en_idx)
        zh_text = get_cell(row, zh_idx)
        # Skip only rows that have neither English nor Chinese prompt text
        # (allows collections that provide only an English column).
        if not en_text and not zh_text:
            continue
        title = get_cell(row, title_idx)
        category = get_cell(row, cat_idx)

        if not title and zh_text and len(zh_text) < 40:
            title = zh_text

        prompts.append({
            'title': title or '',
            'text_en_full': en_text,
            'text_zh_full': zh_text,
            'category': category or '',
            'statements': split_en_into_statements(en_text),
        })

    json.dump(prompts, sys.stdout, ensure_ascii=False, indent=2)


# ── dir mode: single-prompt-per-file xlsx ───────────────────────────

def read_single_prompt_xlsx(filepath):
    """Read a single-prompt-per-file xlsx (label-value format: col C=key, col D=value).

    This format is common in SD prompt collections where each xlsx has:
      Row 0 (header):  [empty, empty, '模型', 'model-name', 'shop info']
      Row 1+:          [empty, empty, 'SD版本'/'sampler'/'cfgScale'/'正向提示词'/'反向提示词', value]
    """
    try:
        import openpyxl
    except ImportError:
        print("Error: openpyxl not installed. Run: pip install openpyxl", file=sys.stderr)
        sys.exit(1)

    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb[wb.sheetnames[0]]

    rows = []
    for row in ws.iter_rows(values_only=True):
        if any(cell is not None for cell in row):
            rows.append([str(cell).strip() if cell is not None else '' for cell in row])

    if len(rows) < 2:
        return None

    # Read label-value pairs from col C (index 2) and col D (index 3)
    data = {}
    for row in rows:
        if len(row) >= 3:
            label = str(row[2]).strip() if row[2] else ''
            value = str(row[3]).strip() if len(row) > 3 and row[3] else ''
            if label and label not in data:
                data[label] = value

    # Also read model from header row (row 0, col C='模型')
    if rows and len(rows[0]) >= 4 and rows[0][2] == '模型':
        data['模型'] = str(rows[0][3]).strip() if rows[0][3] else ''

    en_text = data.get('正向提示词', '')
    if not en_text:
        return None

    # Title from filename: strip common prefixes/suffixes
    filename = Path(filepath).name
    title = Path(filepath).stem
    title = re.sub(r'__?淘宝晴空创意坊$', '', title)
    title = re.sub(r'_淘宝晴空创意坊$', '', title)
    title = re.sub(r'^后补_', '', title)
    title = re.sub(r'_+$', '', title)
    title = title.strip()

    # Category from parent directory name
    category = Path(filepath).parent.name

    return {
        'title': title,
        'text_en_full': en_text,
        'text_zh_full': '',  # no Chinese in source — will be generated in Step 3
        'category': category,
        'source_file': filename,
        'statements': split_en_into_statements(en_text),
    }


def cmd_dir(dirpath, limit=None):
    """Walk directory for single-prompt-per-file xlsx, output parsed JSON."""
    if not os.path.isdir(dirpath):
        print(f"Error: directory not found: {dirpath}", file=sys.stderr)
        sys.exit(1)

    files = []
    for root, _, filenames in os.walk(dirpath):
        for fn in filenames:
            if fn.endswith('.xlsx') and not fn.startswith('~$'):
                files.append(os.path.join(root, fn))

    total_files = len(files)
    if limit and limit > 0:
        files = files[:limit]

    prompts = []
    fail_count = 0
    for fp in files:
        try:
            p = read_single_prompt_xlsx(fp)
            if p:
                prompts.append(p)
        except Exception as e:
            fail_count += 1
            if fail_count <= 3:
                print(f"WARN: {os.path.basename(fp)}: {e}", file=sys.stderr)

    # Deduplicate by text_en_full
    seen = set()
    unique = []
    for p in prompts:
        key = p['text_en_full']
        if key not in seen:
            seen.add(key)
            unique.append(p)

    dup_count = len(prompts) - len(unique)
    if dup_count:
        print(f"Removed {dup_count} duplicates", file=sys.stderr)

    msg = f"Scanned {total_files} files → {len(unique)} unique prompts"
    if fail_count:
        msg += f" ({fail_count} parse failures)"
    print(msg, file=sys.stderr)

    json.dump(unique, sys.stdout, ensure_ascii=False, indent=2)


# ── main ─────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[1]

    if mode == '--inspect':
        if len(sys.argv) < 3:
            print("Usage: parse_file.py --inspect <file_path>", file=sys.stderr)
            sys.exit(1)
        filepath = sys.argv[2]
        if not os.path.exists(filepath):
            print(f"Error: file not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        cmd_inspect(filepath)

    elif mode == '--extract':
        # Parse named arguments
        en_idx = zh_idx = title_idx = cat_idx = None
        sheet_name = None
        filepath = None
        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == '--en' and i + 1 < len(sys.argv):
                en_idx = int(sys.argv[i + 1]); i += 2
            elif arg == '--zh' and i + 1 < len(sys.argv):
                zh_idx = int(sys.argv[i + 1]); i += 2
            elif arg == '--title' and i + 1 < len(sys.argv):
                title_idx = int(sys.argv[i + 1]); i += 2
            elif arg == '--cat' and i + 1 < len(sys.argv):
                cat_idx = int(sys.argv[i + 1]); i += 2
            elif arg == '--sheet' and i + 1 < len(sys.argv):
                sheet_name = sys.argv[i + 1]; i += 2
            elif not arg.startswith('--'):
                filepath = arg; i += 1
            else:
                i += 1

        if not filepath:
            print("Error: no file path provided", file=sys.stderr)
            sys.exit(1)
        if not os.path.exists(filepath):
            print(f"Error: file not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        cmd_extract(filepath, en_idx, zh_idx, title_idx, cat_idx, sheet_name)

    elif mode == '--dir':
        # Parse: --dir <dir_path> [--limit N]
        filepath = None
        limit = None
        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == '--limit' and i + 1 < len(sys.argv):
                limit = int(sys.argv[i + 1]); i += 2
            elif not arg.startswith('--'):
                filepath = arg; i += 1
            else:
                i += 1

        if not filepath:
            print("Error: no directory path provided", file=sys.stderr)
            sys.exit(1)
        cmd_dir(filepath, limit)

    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
