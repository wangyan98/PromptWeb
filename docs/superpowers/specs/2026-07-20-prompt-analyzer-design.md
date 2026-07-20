# Prompt Analyzer Skill Design

## Overview

A Claude Code skill that reads prompt data files (xlsx/csv/json), uses AI to analyze English text-to-image prompts — splitting into semantic segments, assigning statement types, providing Chinese translations (only when missing from source), and extracting difficult English vocabulary — then batch-imports everything into the PromptWeb database via API.

## Skill Location

`skills/prompt-analyzer/SKILL.md`

## Architecture

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

**Responsibilities:**

| Component | What it does |
|-----------|-------------|
| `SKILL.md` | Orchestration — tells AI when to run each script, guides the semantic analysis |
| `parse_file.py` | Reads any file format, auto-detects columns, outputs clean JSON — deterministic, no AI needed |
| `fetch_context.py` | Hits the API for statement types and existing prompts — returns dedup info |
| `import_batch.py` | Takes the AI-generated analysis JSON and bulk-imports everything into the DB |
| **AI (Claude)** | The one intelligent step — reads parsed rows + statement types, splits English into semantic segments, assigns types, translates to Chinese (when missing), extracts difficult words with positions |

**Why scripts for API calls:** Deterministic, reusable, consistent error handling. AI focuses on what only AI can do — semantic understanding of the English prompts.

## Trigger

- User mentions "analyze prompt", "import prompts", "split prompt", or provides a path to a data file containing prompts
- User explicitly invokes `/prompt-analyzer`

## Process

### Step 1: Parse file → `python scripts/parse_file.py <file_path>`

Reads the file, auto-detects format and columns, outputs clean JSON array of prompt rows:

```json
[
  {
    "title": "建于悬崖的巨型神庙废墟",
    "text_en_full": "Generate epic Unreal Engine 5...",
    "text_zh_full": "建于悬崖的巨型神庙废墟",
    "category": "远古遗迹"
  }
]
```

### Step 2: Fetch context → `python scripts/fetch_context.py`

Calls the API for statement types and existing prompts, outputs:

```json
{
  "statement_types": [{"id": 1, "name": "固定开头"}, ...],
  "existing_prompts": [{"id": 1, "text_en_full": "...", "has_statements": true}, ...]
}
```

### Step 3: AI analysis

Claude uses the outputs from steps 1 and 2 to intelligently:
- Identify which rows are new (skip deduped prompts)
- Split each English prompt into semantic segments
- Assign statement types, provide Chinese translations, extract difficult words
- Output structured analysis JSON:

```json
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
            {
              "word_en": "colossal",
              "word_zh": "巨大的",
              "position_start": 105,
              "position_end": 113
            }
          ]
        }
      ]
    }
  ]
}
```

### Step 4: Import → `python scripts/import_batch.py <analysis_json>`

Batch-creates prompts, statements, and words via the API. Outputs import summary.

### Batch Optimization
- File parsing and API calls are handled by scripts — fast, deterministic, one-shot
- AI analysis happens in a single pass over all new prompts
- `import_batch.py` uses all available batch endpoints to minimize roundtrips
- Typical workflow: 3 script runs + 1 AI pass = complete

## Key Rules

### Chinese Translation
- If the source file provides `text_zh_full`, use it as-is — AI does NOT re-translate
- For individual statement segments, AI always provides Chinese translations (source files only have full-text Chinese, not segment-level)

### Deduplication
- `fetch_context.py` checks which prompts already exist in the DB
- AI skips prompts that already have statements (they've been analyzed before)
- Only new/unsplit prompts are analyzed and imported

### Batch Efficiency
- Entire workflow: 4 steps — 3 script runs + 1 AI pass
- `import_batch.py` consolidates all API writes into minimal calls

## API Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/statement-types` | GET | Get available statement types |
| `/api/prompts` | GET | List existing prompts (for dedup check) |
| `/api/import/confirm` | POST | Batch create prompts |
| `/api/prompts/{id}/statements` | POST | Batch create statements for a prompt |
| `/api/statements/{id}/words` | POST | Batch create words for a statement |

## Configuration

- `PROMPT_API_URL` environment variable — default `http://localhost:8000`

## File Format Support

| Format | Detection | Notes |
|--------|-----------|-------|
| `.xlsx` / `.xls` | Extension | Multi-sheet; auto-detect data sheet |
| `.csv` | Extension | Auto-detect delimiter and encoding |
| `.json` | Extension | Array of prompt objects |

Column mapping is always auto-detected — no hardcoded column names.

## Error Handling

- Missing required columns → report error with column suggestions
- API unreachable → report and exit, don't retry indefinitely
- Partial failure during import → report which items succeeded and which failed
- Duplicate prompts → skip with count reported in summary
