# Prompt Analyzer Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a Claude Code skill that reads prompt data files (xlsx/csv/json), uses AI to analyze English text-to-image prompts, and batch-imports results into the PromptWeb database.

**Architecture:** Four components — three Python scripts handle deterministic work (file parsing, API context fetching, batch import); SKILL.md orchestrates them and guides AI through the one intelligent step (semantic analysis of English prompts).

**Tech Stack:** Python 3 (openpyxl, requests), Claude Code skill framework

## Global Constraints

- API base URL from `PROMPT_API_URL` env var, default `http://localhost:8000`
- Deduplication: skip prompts that already have statements in the DB
- Chinese translation: use source file values if present, AI generates only when missing
- Batch import: use `/api/import/confirm` for prompt creation, `/api/prompts/{id}/statements` for statements+words in one call

---

## File Structure

```
skills/prompt-analyzer/
├── SKILL.md                  ← main skill instructions
├── scripts/
│   ├── parse_file.py         ← parse xlsx/csv/json → JSON rows
│   ├── fetch_context.py      ← GET /api/statement-types + /api/prompts → dedup info
│   └── import_batch.py       ← POST /api/import/confirm + /api/prompts/{id}/statements (with words)
└── references/
    └── api-spec.md           ← PromptWeb API reference
```

### Interface Contracts

**parse_file.py** — Input: file path (arg). Output: JSON array `[{title, text_en_full, text_zh_full, category}]` printed to stdout.

**fetch_context.py** — Input: API URL (env). Output: JSON object `{statement_types: [{id, name, color, sort_order}], existing_prompts: [{id, text_en_full, has_statements}]}` printed to stdout.

**import_batch.py** — Input: path to analysis JSON file (arg), API URL (env). Output: JSON object `{created: int, skipped: int, errors: [{index, error}]}` printed to stdout.

---

### Task 1: Create directory structure and references

**Files:**
- Create: `skills/prompt-analyzer/references/api-spec.md`

**Interfaces:**
- Produces: Reference doc consumed by SKILL.md

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p skills/prompt-analyzer/scripts skills/prompt-analyzer/references
```

- [ ] **Step 2: Write API reference document**

Write `skills/prompt-analyzer/references/api-spec.md`:

```markdown
# PromptWeb API Reference

Base URL: `$PROMPT_API_URL` (default `http://localhost:8000`)

All responses follow `{code: 0, data: ..., message: "ok"}` format.

## GET /api/statement-types

Returns all statement types.

Response `data`: `[{id, name, color, sort_order}, ...]`

## GET /api/prompts

List prompts. Query params: `page`, `page_size` (max 100), `search`, `category`.

Response `data`: `{items: [{id, title, text_en_full, text_zh_full, category, ...}], total, page, page_size}`

## GET /api/prompts/{prompt_id}

Get a single prompt with full relations (statements, words, images).

Response `data`: `{id, title, text_en_full, text_zh_full, category, statements: [{id, text_en, text_zh, sort_order, type_id, words: [...]}], ...}`

## POST /api/import/confirm

Batch create prompts. Body: `[{title, text_en_full, text_zh_full, category, source_file}]`

Response `data`: `{imported: N, items: [{id, title}, ...]}`

## POST /api/prompts/{prompt_id}/statements

Batch create statements for a prompt. Body: `[{text_en, text_zh, sort_order, type_id}]`

Response `data`: `[{id, prompt_id, text_en, text_zh, sort_order, type_id}, ...]`

## POST /api/statements/{statement_id}/words

Batch create words for a statement. Body: `[{word_en, word_zh, position_start, position_end}]`

Response `data`: `[{id, prompt_id, statement_id, word_en, word_zh, position_start, position_end}, ...]`
```

- [ ] **Step 3: Commit**

```bash
git add skills/prompt-analyzer/
git commit -m "feat(prompt-analyzer): add directory structure and api-spec reference"
```

---

### Task 2: Create parse_file.py

**Files:**
- Create: `skills/prompt-analyzer/scripts/parse_file.py`

**Interfaces:**
- Produces: `python parse_file.py <file_path>` → JSON array to stdout
- Output schema: `[{title: str, text_en_full: str, text_zh_full: str, category: str}]`

- [ ] **Step 1: Write parse_file.py**

```python
#!/usr/bin/env python3
"""Parse a prompt data file (xlsx/csv/json) into a clean JSON array.

Usage: python parse_file.py <file_path>
Output: JSON array printed to stdout. Each element has keys:
  title, text_en_full, text_zh_full, category
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
            if '描述' in h_str or '场景' in h_str or '主题' in h_str:
                if mapping['title_col'] is None:
                    mapping['title_col'] = idx
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

    return mapping


def parse_xlsx(filepath):
    """Parse .xlsx/.xls file, return list of prompt dicts."""
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

        # If zh_col wasn't found separately but we have a title col with Chinese, use it as zh_full
        if not zh_text and title:
            pass  # keep zh_text empty; AI will know file has no full Chinese translation

        # If title wasn't found but zh_col has short Chinese, use that as title
        if not title and zh_text and len(zh_text) < 40:
            title = zh_text

        prompts.append({
            'title': title or '',
            'text_en_full': en_text,
            'text_zh_full': zh_text,
            'category': category or '',
        })

    print(f"Parsed sheet '{data_sheet}': {len(prompts)} rows", file=sys.stderr)
    return prompts


def parse_csv(filepath):
    """Parse .csv file, return list of prompt dicts."""
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

        prompts.append({
            'title': get(mapping['title_col']) or get(mapping['zh_col'])[:40] if get(mapping['zh_col']) else '',
            'text_en_full': en_text,
            'text_zh_full': get(mapping['zh_col']),
            'category': get(mapping['cat_col']),
        })

    print(f"Parsed CSV: {len(prompts)} rows", file=sys.stderr)
    return prompts


def parse_json_file(filepath):
    """Parse .json file, return list of prompt dicts.

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

        if prompt['text_en_full']:
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
```

- [ ] **Step 2: Test with the xlsx file**

```bash
cd /Users/wangyan/Desktop/PromptWeb && python3 skills/prompt-analyzer/scripts/parse_file.py "100条史诗奇幻场景提示词.xlsx" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Count: {len(d)}'); print(json.dumps(d[0], ensure_ascii=False, indent=2))"
```

Expected: prints 100 rows and the first prompt object with title, text_en_full, text_zh_full, category.

- [ ] **Step 3: Test with the second xlsx file**

```bash
cd /Users/wangyan/Desktop/PromptWeb && python3 skills/prompt-analyzer/scripts/parse_file.py "100套奇幻视频提示词.xlsx" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Count: {len(d)}'); print(json.dumps(d[0], ensure_ascii=False, indent=2))"
```

Expected: prints 100 rows.

- [ ] **Step 4: Commit**

```bash
git add skills/prompt-analyzer/scripts/parse_file.py
git commit -m "feat(prompt-analyzer): add parse_file.py script"
```

---

### Task 3: Create fetch_context.py

**Files:**
- Create: `skills/prompt-analyzer/scripts/fetch_context.py`

**Interfaces:**
- Consumes: `PROMPT_API_URL` env var
- Produces: JSON to stdout `{statement_types: [...], existing_prompts: [...]}`

- [ ] **Step 1: Write fetch_context.py**

```python
#!/usr/bin/env python3
"""Fetch statement types and existing prompts from the PromptWeb API.

Usage: python fetch_context.py
Env: PROMPT_API_URL (default http://localhost:8000)

Output: JSON printed to stdout:
{
  "statement_types": [{id, name, color, sort_order}],
  "existing_prompts": [{id, text_en_full, has_statements}]
}
"""

import json
import os
import sys
import urllib.request
import urllib.error


API_URL = os.environ.get('PROMPT_API_URL', 'http://localhost:8000')


def api_get(path):
    """Make a GET request and return the decoded JSON data."""
    url = f"{API_URL}{path}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            body = json.loads(resp.read().decode('utf-8'))
            if body.get('code', 0) != 0:
                print(f"API error on {path}: {body.get('message', 'unknown')}", file=sys.stderr)
                return None
            return body.get('data')
    except urllib.error.URLError as e:
        print(f"Connection error: {e}. Is the API server running at {API_URL}?", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON response from {path}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    # 1. Fetch statement types
    types_data = api_get('/api/statement-types')
    if types_data is None:
        print("Failed to fetch statement types", file=sys.stderr)
        sys.exit(1)

    statement_types = [
        {'id': t['id'], 'name': t['name'], 'color': t.get('color', '#4fc3f7'), 'sort_order': t.get('sort_order', 0)}
        for t in types_data
    ]

    # 2. Fetch all existing prompts (with pagination)
    existing_prompts = []
    page = 1
    page_size = 100

    while True:
        prompts_data = api_get(f'/api/prompts?page={page}&page_size={page_size}')
        if prompts_data is None:
            break

        items = prompts_data.get('items', [])
        if not items:
            break

        # For each prompt, check if it already has statements
        for item in items:
            existing_prompts.append({
                'id': item['id'],
                'text_en_full': item.get('text_en_full', ''),
                'has_statements': False,  # will check by fetching detail
            })

        total = prompts_data.get('total', 0)
        if page * page_size >= total:
            break
        page += 1

    # 3. Check which prompts already have statements (fetch detail for each)
    # We batch this by checking in the list endpoint response; if statements count
    # isn't available, we fetch each prompt detail. To save time, fetch first page
    # prompts individually.
    for p in existing_prompts:
        detail = api_get(f'/api/prompts/{p["id"]}')
        if detail:
            statements = detail.get('statements', [])
            p['has_statements'] = len(statements) > 0

    result = {
        'statement_types': statement_types,
        'existing_prompts': existing_prompts,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Commit**

```bash
git add skills/prompt-analyzer/scripts/fetch_context.py
git commit -m "feat(prompt-analyzer): add fetch_context.py script"
```

---

### Task 4: Create import_batch.py

**Files:**
- Create: `skills/prompt-analyzer/scripts/import_batch.py`

**Interfaces:**
- Consumes: path to analysis JSON file (arg), `PROMPT_API_URL` env var
- Produces: Import summary JSON to stdout

- [ ] **Step 1: Write import_batch.py**

```python
#!/usr/bin/env python3
"""Batch-import analyzed prompts into the PromptWeb database.

Usage: python import_batch.py <analysis_json_path>
Env: PROMPT_API_URL (default http://localhost:8000)

Input JSON format:
{
  "new_prompts": [
    {
      "title": "...",
      "text_en_full": "...",
      "text_zh_full": "...",
      "category": "...",
      "statements": [
        {
          "text_en": "...",
          "text_zh": "...",
          "sort_order": 1,
          "type_id": 1,
          "words": [
            {"word_en": "...", "word_zh": "...", "position_start": 0, "position_end": 10}
          ]
        }
      ]
    }
  ]
}

Output: import summary printed to stdout as JSON.
"""

import json
import os
import sys
import urllib.request
import urllib.error


API_URL = os.environ.get('PROMPT_API_URL', 'http://localhost:8000')


def api_post(path, body):
    """Make a POST request with JSON body, return decoded response data."""
    url = f"{API_URL}{path}"
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            if result.get('code', 0) != 0:
                print(f"API error on POST {path}: {result.get('message', 'unknown')}", file=sys.stderr)
                return None
            return result.get('data')
    except urllib.error.URLError as e:
        print(f"Connection error on POST {path}: {e}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Invalid JSON response from POST {path}: {e}", file=sys.stderr)
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python import_batch.py <analysis_json_path>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        analysis = json.load(f)

    prompts_data = analysis.get('new_prompts', analysis.get('prompts', []))
    if not prompts_data:
        print("No prompts to import", file=sys.stderr)
        print(json.dumps({'created': 0, 'skipped': 0, 'errors': []}))
        return

    created_count = 0
    skipped_count = 0
    errors = []

    # Step 1: Batch create all prompts via /api/import/confirm
    import_items = []
    for p in prompts_data:
        import_items.append({
            'title': p.get('title', ''),
            'text_en_full': p.get('text_en_full', ''),
            'text_zh_full': p.get('text_zh_full', ''),
            'category': p.get('category', ''),
            'source_file': p.get('source_file', ''),
        })

    result = api_post('/api/import/confirm', import_items)
    if result is None:
        print("Error: failed to create prompts", file=sys.stderr)
        sys.exit(1)

    created_items = result.get('items', [])
    print(f"Created {len(created_items)} prompts", file=sys.stderr)

    # Step 2: For each created prompt, batch create statements and words
    for i, prompt_result in enumerate(created_items):
        prompt_id = prompt_result['id']
        prompt_source = prompts_data[i] if i < len(prompts_data) else None

        if not prompt_source:
            continue

        statements = prompt_source.get('statements', [])
        if not statements:
            continue

        # Create statements batch
        stmt_bodies = []
        for s in statements:
            stmt_bodies.append({
                'text_en': s.get('text_en', ''),
                'text_zh': s.get('text_zh', ''),
                'sort_order': s.get('sort_order', 0),
                'type_id': s.get('type_id'),
            })

        stmt_result = api_post(f'/api/prompts/{prompt_id}/statements', stmt_bodies)
        if stmt_result is None:
            errors.append({'prompt_id': prompt_id, 'error': 'failed to create statements'})
            continue

        # Step 3: For each created statement, batch create words
        for j, stmt_created in enumerate(stmt_result):
            statement_id = stmt_created['id']
            words = statements[j].get('words', []) if j < len(statements) else []

            if not words:
                continue

            word_bodies = []
            for w in words:
                word_bodies.append({
                    'word_en': w.get('word_en', ''),
                    'word_zh': w.get('word_zh', ''),
                    'position_start': w.get('position_start'),
                    'position_end': w.get('position_end'),
                })

            word_result = api_post(f'/api/statements/{statement_id}/words', word_bodies)
            if word_result is None:
                errors.append({'statement_id': statement_id, 'error': 'failed to create words'})

        created_count += 1

    summary = {
        'created': created_count,
        'total_statements': sum(len(p.get('statements', [])) for p in prompts_data),
        'total_words': sum(
            len(s.get('words', []))
            for p in prompts_data
            for s in p.get('statements', [])
        ),
        'skipped': skipped_count,
        'errors': errors,
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Commit**

```bash
git add skills/prompt-analyzer/scripts/import_batch.py
git commit -m "feat(prompt-analyzer): add import_batch.py script"
```

---

### Task 5: Create SKILL.md

**Files:**
- Create: `skills/prompt-analyzer/SKILL.md`

**Interfaces:**
- Consumes: scripts from Tasks 2-4, reference from Task 1
- Produces: Complete skill ready for Claude to use

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: prompt-analyzer
description: Analyze text-to-image prompt files (xlsx/csv/json) — split English prompts into semantic segments, label them with statement types, provide Chinese translations (only when source lacks them), extract difficult English vocabulary, and batch-import everything into PromptWeb. Use when the user mentions analyzing prompts, importing prompt data, splitting prompts, or provides a path to a prompt data file. Also use when the user wants to extract difficult English words from prompts, build Chinese-English prompt mappings, or batch-process a file of image generation prompts.
---

# Prompt Analyzer

Analyze text-to-image prompt data files — semantic splitting, Chinese-English mapping, difficult word extraction — then batch-import into the PromptWeb database.

## Workflow

This skill follows a 4-step pipeline. Run each step in order.

### Step 1: Parse the file

Run the parse script on the user's file path:

```bash
python skills/prompt-analyzer/scripts/parse_file.py "<file_path>"
```

This outputs a JSON array of prompt rows with keys: `title`, `text_en_full`, `text_zh_full`, `category`.

If the script fails:
- Check that the file exists and is .xlsx/.csv/.json
- If openpyxl is needed: `pip install openpyxl`
- If column detection fails, read the file yourself and identify the columns manually

### Step 2: Fetch DB context

```bash
python skills/prompt-analyzer/scripts/fetch_context.py
```

This outputs JSON with:
- `statement_types`: available types from the DB (id, name, color)
- `existing_prompts`: prompts already in the DB, each with `has_statements` flag

If the API is unreachable, remind the user to start the PromptWeb backend and set `PROMPT_API_URL` if not using the default `http://localhost:8000`.

### Step 3: AI analysis

This is the core intelligence step. You (Claude) must analyze each new prompt that doesn't already have statements in the DB.

**Deduplication first:** Compare parsed rows against existing_prompts. A prompt is already analyzed if there's an existing prompt with matching `text_en_full` AND `has_statements: true`. Skip those.

**For each new prompt, do the following:**

#### 3a. Split into semantic segments

Split the English prompt at natural semantic boundaries — commas, conjunctions, or where the topic shifts. Each segment should be a meaningful phrase. Typically 3-8 segments per prompt.

Good split example:
- "Generate epic Unreal Engine 5 fantasy landscape,"
- "stormy overcast daylight,"
- "cinematic environmental photography,"
- "ancient colossal temple ruins built into a cliff face"

Bad split (too granular):
- "Generate", "epic", "Unreal", "Engine", "5"...

#### 3b. Assign statement types

For each segment, pick the best-matching `type_id` from the available statement types. If no existing type fits well, you may leave `type_id` as `null` and the user can categorize later. Use your judgment — match semantically (e.g., a segment about lighting → "光照氛围" type; a segment about camera composition → "镜头构图" type).

#### 3c. Translate each segment to Chinese

Provide a faithful Chinese translation for every segment. This is always needed — source files only have full-text Chinese, not segment-level translations.

#### 3d. Extract difficult words

For each segment, identify words that are:
- **Uncommon or specialized** (e.g., "colossal", "overcast", "cinematic", "canopy", "dune")
- **Art/photography terminology** (e.g., "bokeh", "depth of field", "volumetric", "ambient occlusion")
- **NOT basic words**: skip articles (a, an, the), prepositions (in, on, at, of, to, for, with), conjunctions (and, or, but), common verbs (is, are, was, were, be, been, being, have, has, had, do, does, did, will, would, can, could), common pronouns (it, its, this, that, these, those)

For each difficult word:
- `word_en`: the English word/phrase exactly as it appears
- `word_zh`: Chinese translation/explanation
- `position_start`: character index in the FULL `text_en_full` string where this word starts (0-based)
- `position_end`: character index where this word ends (exclusive)

IMPORTANT: Calculate positions against the original `text_en_full` field, not the segment text. Use `text_en_full.find(word_en)` and `text_en_full.find(word_en) + len(word_en)`.

#### 3e. Chinese translation rule

If the source file already provides `text_zh_full` and it's not empty, use it as-is in the output — do NOT re-translate. Only provide AI-generated `text_zh_full` when the source file has none.

### Output format for Step 3

Write the analysis result to a temporary JSON file (e.g., `/tmp/prompt_analysis.json`):

```json
{
  "new_prompts": [
    {
      "title": "建于悬崖的巨型神庙废墟",
      "text_en_full": "Generate epic Unreal Engine 5 fantasy landscape, stormy overcast daylight, cinematic environmental photography, ancient colossal temple ruins built into a cliff face...",
      "text_zh_full": "建于悬崖的巨型神庙废墟",
      "category": "远古遗迹",
      "source_file": "100条史诗奇幻场景提示词.xlsx",
      "statements": [
        {
          "text_en": "Generate epic Unreal Engine 5 fantasy landscape",
          "text_zh": "生成史诗级虚幻引擎5奇幻场景",
          "sort_order": 1,
          "type_id": 1,
          "words": [
            {"word_en": "epic", "word_zh": "史诗的", "position_start": 9, "position_end": 13},
            {"word_en": "Unreal Engine 5", "word_zh": "虚幻引擎5", "position_start": 14, "position_end": 28}
          ]
        },
        {
          "text_en": "stormy overcast daylight",
          "text_zh": "暴风雨阴天光线",
          "sort_order": 2,
          "type_id": 2,
          "words": [
            {"word_en": "stormy", "word_zh": "暴风雨的", "position_start": 66, "position_end": 72},
            {"word_en": "overcast", "word_zh": "阴天的", "position_start": 73, "position_end": 81}
          ]
        }
      ]
    }
  ]
}
```

### Step 4: Batch import

```bash
python skills/prompt-analyzer/scripts/import_batch.py /tmp/prompt_analysis.json
```

This creates all prompts, statements, and words in the database. It prints an import summary with counts.

## Important notes

- **Process ALL new prompts in one AI pass.** Don't analyze one-by-one — batch them all in the analysis JSON.
- **If the file is large (>50 prompts),** consider splitting the analysis into chunks of ~30 prompts each to stay within context limits, but still process each chunk completely (all 4 steps per chunk).
- **Words must reference positions in the FULL English text,** not the segment. Wrong positions will break the UI word highlighting.
- Verify each step's output before proceeding to the next step.
```

- [ ] **Step 2: Commit**

```bash
git add skills/prompt-analyzer/SKILL.md
git commit -m "feat(prompt-analyzer): add SKILL.md with full workflow"
```

---

### Task 6: End-to-end smoke test

**Files:**
- None (test only)

- [ ] **Step 1: Test parse script with all supported formats**

```bash
# Test xlsx
cd /Users/wangyan/Desktop/PromptWeb
python3 skills/prompt-analyzer/scripts/parse_file.py "100条史诗奇幻场景提示词.xlsx" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d) == 100, f'Expected 100, got {len(d)}'; print('OK: 100 promots parsed from xlsx')"

# Test second xlsx
python3 skills/prompt-analyzer/scripts/parse_file.py "100套奇幻视频提示词.xlsx" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d) == 100, f'Expected 100, got {len(d)}'; print('OK: 100 promots parsed from second xlsx')"
```

- [ ] **Step 2: Verify SKILL.md structure**

```bash
# Check frontmatter
head -5 skills/prompt-analyzer/SKILL.md
# Should show valid YAML frontmatter with name and description
```

- [ ] **Step 3: Verify all files are in place**

```bash
ls -la skills/prompt-analyzer/SKILL.md
ls -la skills/prompt-analyzer/scripts/parse_file.py
ls -la skills/prompt-analyzer/scripts/fetch_context.py
ls -la skills/prompt-analyzer/scripts/import_batch.py
ls -la skills/prompt-analyzer/references/api-spec.md
```

- [ ] **Step 4: Commit final state**

```bash
git add skills/prompt-analyzer/
git commit -m "chore(prompt-analyzer): verify all components in place"
```

---

## Self-Review

**1. Spec coverage:**
- File parsing (xlsx/csv/json) → Task 2 (parse_file.py)
- Auto-detect columns → Task 2 (detect_column function)
- Fetch statement types + existing prompts → Task 3 (fetch_context.py)
- AI semantic analysis → Task 5 (SKILL.md Step 3)
- Chinese translation rule (use source if present) → Task 5 (SKILL.md Step 3e)
- Deduplication → Task 5 (SKILL.md Step 3)
- Batch import → Task 4 (import_batch.py)
- API reference → Task 1 (api-spec.md)
- `PROMPT_API_URL` env var → All scripts use `os.environ.get('PROMPT_API_URL', 'http://localhost:8000')`
- Error handling → Each script has explicit error messages and non-zero exits
- Not constraining file type → Skill doc says "any .xlsx/.csv/.json" and scripts handle unknown gracefully

**2. Placeholder scan:** No TBD, TODO, or vague instructions. All code is concrete.

**3. Type consistency:**
- `parse_file.py` outputs `[{title: str, text_en_full: str, text_zh_full: str, category: str}]`
- `fetch_context.py` outputs `{statement_types: [{id, name, color, sort_order}], existing_prompts: [{id, text_en_full, has_statements}]}`
- `import_batch.py` consumes analysis JSON with `new_prompts[{title, text_en_full, text_zh_full, category, statements[{text_en, text_zh, sort_order, type_id, words[{word_en, word_zh, position_start, position_end}]}]}]`
- SKILL.md references all these exact field names — consistent throughout.
