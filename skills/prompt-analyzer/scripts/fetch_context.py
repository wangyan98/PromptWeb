#!/usr/bin/env python3
"""Fetch statement types and unprocessed prompts from the PromptWeb API.

Usage: python fetch_context.py
Env: PROMPT_API_URL (default http://localhost:8000)

Output: JSON printed to stdout:
{
  "statement_types": [{id, name, color, sort_order}],
  "unprocessed_prompts": [{id, text_en_full, title}]
}

"unprocessed_prompts" are prompts that exist in the DB but have ZERO statements
(i.e., they were imported but not yet analyzed/split).
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

    # 2. Fetch all existing prompts and check which have NO statements
    unprocessed = []
    page = 1
    page_size = 100

    while True:
        prompts_data = api_get(f'/api/prompts?page={page}&page_size={page_size}')
        if prompts_data is None:
            break

        items = prompts_data.get('items', [])
        if not items:
            break

        # For each prompt, check if it has statements by fetching detail
        for item in items:
            detail = api_get(f'/api/prompts/{item["id"]}')
            if detail:
                statements = detail.get('statements', [])
                if len(statements) == 0:
                    unprocessed.append({
                        'id': item['id'],
                        'title': item.get('title', ''),
                        'text_en_full': item.get('text_en_full', ''),
                        'text_zh_full': item.get('text_zh_full', ''),
                    })

        total = prompts_data.get('total', 0)
        if page * page_size >= total:
            break
        page += 1

    result = {
        'statement_types': statement_types,
        'unprocessed_prompts': unprocessed,
    }

    print(f"Found {len(unprocessed)} unprocessed prompts (no statements yet)", file=sys.stderr)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
