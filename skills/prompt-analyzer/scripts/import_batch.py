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
                ps = w.get('position_start')
                pe = w.get('position_end')
                # Skip words with invalid positions
                if ps is None or pe is None:
                    continue
                word_bodies.append({
                    'word_en': w.get('word_en', ''),
                    'word_zh': w.get('word_zh', ''),
                    'position_start': int(ps),
                    'position_end': int(pe),
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
