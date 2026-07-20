#!/usr/bin/env python3
"""Parse a prompt data file (xlsx/csv/json) into a clean JSON array.

Usage: python parse_file.py <file_path>
Output: JSON array printed to stdout. Each element has keys:
  title, text_en_full, text_zh_full, category, statements
"""

import json
import sys
import os
import csv
import re
from pathlib import Path


def detect_xlsx_data_sheet(sheets_data):
    """Pick the sheet most likely to contain prompt data.

    Heuristic: the sheet with the most rows, skipping sheets whose name
    contains '封面','说明','公式','模板','template','cover','summary'.
    """
    skip_keywords = ['封面', '说明', '公式', '模板', 'template', 'cover', 'summary', 'intro', 'readme']
    candidates = {
        name: rows
        for name, rows in sheets_data.items()
        if not any(kw in name.lower() for kw in skip_keywords)
    }
    if not candidates:
        candidates = sheets_data
    best = max(candidates, key=lambda n: len(candidates[n]))
    return best


def detect_column(headers, rows_sample):
    """Map columns to fields based on header names and cell content heuristics.

    Returns dict with keys: title_col, en_col, zh_col, cat_col (each is an index or None).
    """
    mapping = {'title_col': None, 'en_col': None, 'zh_col': None, 'cat_col': None}

    for idx, h in enumerate(headers):
        h_str = str(h).strip().lower() if h else ''
        # English prompt detection
        if any(kw in h_str for kw in ['英文', 'english', '完整提示词', 'en', 'prompt']):
            if mapping['en_col'] is None:
                mapping['en_col'] = idx
        # Chinese / title detection
        if any(kw in h_str for kw in ['中文', 'chinese', '场景', '主题', '标题', 'title', 'zh']):
            if '完整' in h_str and '英' in h_str:
                continue  # this is the English column, already mapped
            # If header has title-like keywords, it's a title column
            is_title_col = any(kw in h_str for kw in ['场景', '主题', '标题', 'title', '名称'])
            if is_title_col:
                if mapping['title_col'] is None:
                    mapping['title_col'] = idx
                continue  # don't also set this as zh_col
            if mapping['zh_col'] is None:
                mapping['zh_col'] = idx
        # Category detection
        if any(kw in h_str for kw in ['类别', 'category', 'cat', '分类']):
            mapping['cat_col'] = idx
        # Number / 编号 column — skip
        if any(kw in h_str for kw in ['编号', '序号', 'id']):
            continue

    # Fallback: content-based detection using sample rows
    for idx in range(len(headers)):
        sample_texts = []
        for row in rows_sample:
            if idx < len(row) and row[idx]:
                sample_texts.append(str(row[idx])[:200])

        if not sample_texts:
            continue

        avg_len = sum(len(t) for t in sample_texts) / len(sample_texts)
        has_en_keywords = any(
            kw in t.lower()
            for t in sample_texts
            for kw in ['generate', 'epic', 'unreal engine', 'cinematic', '8k', 'photography', 'render']
        )
        has_chinese = any(bool(re.search(r'[一-鿿]', t)) for t in sample_texts)

        # Long English text = English prompt column
        if mapping['en_col'] is None and avg_len > 100 and has_en_keywords:
            mapping['en_col'] = idx
        # Short Chinese text (1-30 chars typical) = title
        elif mapping['title_col'] is None and has_chinese and avg_len < 80:
            mapping['title_col'] = idx
        # Long Chinese text = full Chinese translation
        elif mapping['zh_col'] is None and has_chinese and avg_len > 80:
            mapping['zh_col'] = idx
        # Short labels (2-8 chars typical) = category
        elif mapping['cat_col'] is None and avg_len < 10 and not has_en_keywords:
            mapping['cat_col'] = idx

    # Defensive: if title and zh point to the same column, it's a title, not a full translation
    if mapping['title_col'] is not None and mapping['zh_col'] == mapping['title_col']:
        mapping['zh_col'] = None

    return mapping


def split_en_into_statements(en_text):
    """Split English prompt text into statements by comma/semicolon boundaries.

    Handles merging of short trailing specs like '16:9', '8K', '4K', '6s'.
    Returns list of {text_en, sort_order} dicts.
    """
    # Split on commas and semicolons
    parts = re.split(r'[,;]', en_text)
    parts = [p.strip() for p in parts if p.strip()]

    # Merge short trailing specs (aspect ratios, resolution, duration) into previous segment
    merged = []
    for part in parts:
        stripped = part.strip()
        if merged and re.match(r'^\d+:\d+$|^\d+[kK]$|^\d+s$', stripped):
            merged[-1] = merged[-1] + ', ' + stripped
        else:
            merged.append(stripped)

    statements = []
    for i, text in enumerate(merged):
        statements.append({
            'text_en': text,
            'sort_order': i + 1,
        })

    return statements


def parse_xlsx(filepath):
    """Parse .xlsx/.xls file, return list of prompt dicts with pre-split statements."""
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

    data_sheet = detect_xlsx_data_sheet(sheets_data)
    rows = sheets_data[data_sheet]

    if len(rows) < 2:
        print(f"Error: sheet '{data_sheet}' has no data rows", file=sys.stderr)
        sys.exit(1)

    headers = rows[0]
    sample = rows[1:min(6, len(rows))]
    mapping = detect_column(headers, sample)

    if mapping['en_col'] is None:
        print("Error: could not find English prompt column", file=sys.stderr)
        print(f"Headers detected: {headers}", file=sys.stderr)
        sys.exit(1)

    prompts = []
    for row in rows[1:]:  # skip header
        if all(not c or not str(c).strip() for c in row):
            continue

        def get(col):
            if col is not None and col < len(row):
                return str(row[col]).strip()
            return ''

        en_text = get(mapping['en_col'])
        if not en_text:
            continue

        zh_text = get(mapping['zh_col'])
        title = get(mapping['title_col'])
        category = get(mapping['cat_col'])

        # If title wasn't found but zh_col has short Chinese, use that as title
        if not title and zh_text and len(zh_text) < 40:
            title = zh_text

        # If no separate Chinese full-text column, use title as Chinese display
        if not zh_text and title:
            zh_text = title

        # Pre-split English text into statements by punctuation
        statements = split_en_into_statements(en_text)

        prompts.append({
            'title': title or '',
            'text_en_full': en_text,
            'text_zh_full': zh_text,
            'category': category or '',
            'statements': statements,
        })

    print(f"Parsed sheet '{data_sheet}': {len(prompts)} rows", file=sys.stderr)
    return prompts


def parse_csv(filepath):
    """Parse .csv file, return list of prompt dicts with pre-split statements."""
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1']
    rows = None
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                reader = csv.reader(f)
                rows = list(reader)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if rows is None:
        print("Error: could not decode CSV file with any encoding", file=sys.stderr)
        sys.exit(1)

    if len(rows) < 2:
        print("Error: CSV has no data rows", file=sys.stderr)
        sys.exit(1)

    headers = rows[0]
    sample = rows[1:min(6, len(rows))]
    mapping = detect_column(headers, sample)

    if mapping['en_col'] is None:
        print("Error: could not find English prompt column", file=sys.stderr)
        sys.exit(1)

    prompts = []
    for row in rows[1:]:
        if all(not c or not c.strip() for c in row):
            continue

        def get(col):
            if col is not None and col < len(row):
                return str(row[col]).strip()
            return ''

        en_text = get(mapping['en_col'])
        if not en_text:
            continue

        zh_text = get(mapping['zh_col'])
        title = get(mapping['title_col'])

        if not title and zh_text and len(zh_text) < 40:
            title = zh_text
        if not zh_text and title:
            zh_text = title

        statements = split_en_into_statements(en_text)

        prompts.append({
            'title': title or '',
            'text_en_full': en_text,
            'text_zh_full': zh_text,
            'category': get(mapping['cat_col']),
            'statements': statements,
        })

    print(f"Parsed CSV: {len(prompts)} rows", file=sys.stderr)
    return prompts


def parse_json_file(filepath):
    """Parse .json file, return list of prompt dicts with pre-split statements.

    Normalizes known key names to: title, text_en_full, text_zh_full, category.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, dict):
        # Could be wrapped: {"prompts": [...]} or single object
        for key in ['prompts', 'data', 'items']:
            if key in data and isinstance(data[key], list):
                data = data[key]
                break
        else:
            data = [data]

    if not isinstance(data, list):
        print("Error: JSON must be an array or object with an array field", file=sys.stderr)
        sys.exit(1)

    # Normalize keys: map common variants
    key_map = {
        'title': ['title', 'name', '主题', '标题', '名称', '场景主题'],
        'text_en_full': ['text_en_full', 'text_en', 'en', 'english', '英文', '完整提示词', 'prompt', '提示词'],
        'text_zh_full': ['text_zh_full', 'text_zh', 'zh', 'chinese', '中文', '翻译', '中文提示词'],
        'category': ['category', 'cat', '类别', '分类', 'tag'],
    }

    prompts = []
    for item in data:
        prompt = {}
        for field, aliases in key_map.items():
            for alias in aliases:
                if alias in item:
                    val = item[alias]
                    prompt[field] = str(val).strip() if val else ''
                    break
            if field not in prompt:
                prompt[field] = ''

        if not prompt['text_en_full']:
            continue

        # If no zh_full, use title
        if not prompt['text_zh_full'] and prompt['title']:
            prompt['text_zh_full'] = prompt['title']

        prompt['statements'] = split_en_into_statements(prompt['text_en_full'])
        prompts.append(prompt)

    print(f"Parsed JSON: {len(prompts)} rows", file=sys.stderr)
    return prompts


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_file.py <file_path>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    ext = Path(filepath).suffix.lower()

    if ext in ('.xlsx', '.xls'):
        prompts = parse_xlsx(filepath)
    elif ext == '.csv':
        prompts = parse_csv(filepath)
    elif ext == '.json':
        prompts = parse_json_file(filepath)
    else:
        print(f"Error: unsupported file type: {ext}. Supported: .xlsx, .xls, .csv, .json", file=sys.stderr)
        sys.exit(1)

    json.dump(prompts, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
