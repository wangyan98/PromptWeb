---
name: prompt-analyzer
description: Analyze text-to-image prompt files (xlsx/csv/json) — split English prompts into semantic segments, label them with statement types, provide Chinese translations (only when source lacks them), extract difficult English vocabulary, and batch-import everything into PromptWeb. Use when the user mentions analyzing prompts, importing prompt data, splitting prompts, or provides a path to a prompt data file. Also use when the user wants to extract difficult English words from prompts, build Chinese-English prompt mappings, or batch-process a file of image generation prompts.
---

# Prompt Analyzer

Analyze text-to-image prompt data files — semantic splitting, Chinese-English mapping, difficult word extraction — then batch-import into the PromptWeb database.

## Workflow

This skill follows a 4-step pipeline. Run each step in order.

### Step 1: Inspect, confirm columns, and extract

**This is a three-phase step. Do NOT rush to extraction — always confirm with the user first.**

#### Phase 1a: Inspect the file structure

```bash
python skills/prompt-analyzer/scripts/parse_file.py --inspect "<file_path>"
```

This prints a compact metadata JSON — format, sheet name, headers, first 5 sample rows, total row count. Show the headers and 2 sample rows to the user.

#### Phase 1b: CONFIRM column mapping with the user (REQUIRED)

**NEVER extract without asking.** After inspect, present your column analysis to the user in a table like this:

```
| 索引 | 表头 | 映射建议 |
|------|------|---------|
| 0 | 编号 | 跳过 |
| 1 | 类别 | --cat |
| 2 | 场景主题 | --title |
| 3 | 提示词（英文） | --en ← 英文prompt |
| 4 | 提示词（中文） | --zh |
```

**Key risks to call out:**
- If the file has MULTIPLE English columns (e.g., "视频提示词" AND "图片提示词"), highlight this ambiguity — the user must pick which one they want.
- If any column seems ambiguous, describe what the sample data looks like and ask.
- For xlsx files with multiple sheets, confirm the auto-detected sheet is correct.

Wait for the user to say "yes" or correct your mapping before proceeding.

#### Phase 1c: Extract with confirmed column choices

```bash
python skills/prompt-analyzer/scripts/parse_file.py --extract "<file_path>" \
  --en <N> --zh <M> --title <P> --cat <Q> > /tmp/prompt_parsed.json
```

Only `--en` is required. After extracting, verify the first row looks correct:

```bash
python3 -c "import json; d=json.load(open('/tmp/prompt_parsed.json')); print(f'rows={len(d)}, en_col_sample={d[0][\"text_en_full\"][:100]}')"
```

Share this one-line verification with the user before moving to Step 2.

#### Alternative: Directory of single-prompt-per-file xlsx (e.g. SD prompt collections)

Some prompt collections store **one prompt per xlsx file** in a directory tree. Each file has label-value pairs (col C=key, col D=value) rather than a table of rows. The key field is `正向提示词` (positive prompt in col C). Category is derived from the subdirectory name.

For these, use `--dir` mode:

```bash
# Test with a sample first (always do this):
python skills/prompt-analyzer/scripts/parse_file.py --dir "<directory_path>" --limit 5

# After confirming format looks correct, run full extract:
python skills/prompt-analyzer/scripts/parse_file.py --dir "<directory_path>" > /tmp/prompt_parsed.json
```

`--dir` mode:
- Walks directory recursively, finds all `.xlsx` files
- Extracts `正向提示词` → `text_en_full`, category from parent dir, title from filename (cleaned)
- Auto-splits English prompt at commas into statement segments
- Deduplicates by `text_en_full`
- Sets `text_zh_full` to empty (translations generated in Step 3)

**Always test with `--limit 5` first** and show the user sample titles, categories, and statement counts. After the user confirms, run without `--limit`.

### Step 2: Fetch DB context

```bash
python skills/prompt-analyzer/scripts/fetch_context.py
```

This outputs JSON with:
- `statement_types`: available types from the DB (id, name, color)
- `existing_prompts`: prompts already in the DB, each with `has_statements` flag

If the API is unreachable, remind the user to start the PromptWeb backend and set `PROMPT_API_URL` if not using the default `http://localhost:8000`.

### Step 3: AI analysis

**This is the core intelligence step.** You (Claude) do ALL translation, type classification, and word extraction for natural-language prompts. No hardcoded data — every analysis is generated fresh based on your language understanding.

**For SD-style comma-separated tag prompts** (from `--dir` mode or similar), use the SD tag analyzer:

```bash
python skills/prompt-analyzer/scripts/ai_analyze_sd.py < /tmp/prompt_parsed.json > /tmp/prompt_analysis.json
```

`ai_analyze_sd.py` handles the mechanical parts of SD tag analysis:
- Rule-based type classification (quality→画质风格, lighting→光照氛围, subject→场景主体, etc.)
- Dictionary-based Chinese translation for common SD tags
- Specialized word extraction (artist names, art/photography terminology, uncommon words)

For natural-language English prompts, always do the analysis yourself. For SD tag prompts, `ai_analyze_sd.py` provides consistent, high-coverage results. If the dictionary misses common tags, add them to the script.

The `ai_translate.py` script is a **batch I/O helper only** — it does zero intelligence. Use it for splitting large files and validating output.

**Deduplication first:** Compare parsed rows against existing_prompts from Step 2. A prompt is already analyzed if there's an existing prompt with matching `text_en_full` AND `has_statements: true`. Skip those.

#### Small batch workflow (≤30 new prompts)

Read the parsed JSON from Step 1 and context from Step 2 directly. Produce the analysis JSON yourself and write it to `/tmp/prompt_analysis.json`.

#### Large batch workflow (>30 new prompts)

Use the batch helper to split, then analyze batch by batch:

```bash
# 1. Split parsed prompts into batches of 30
python skills/prompt-analyzer/scripts/ai_translate.py --split 30 < /tmp/prompt_parsed.json
# → writes batch-001.json ... batch-00N.json to /tmp/prompt-batches/

# 2. For EACH batch file, dispatch a sub-agent (or process yourself).
#    CRITICAL: every batch output file MUST pass per-batch validation (see below).

# 3. Merge all batch outputs
python skills/prompt-analyzer/scripts/ai_translate.py --merge
# → writes /tmp/prompt_analysis.json

# 4. Validate the merged output
python skills/prompt-analyzer/scripts/ai_translate.py --validate /tmp/prompt_analysis.json
```

#### BATCH OUTPUT FORMAT CONTRACT (READ CAREFULLY)

Every batch output file MUST use this EXACT structure. Field names are
case-sensitive and immutable. The merge and import scripts depend on these
exact keys.

**Top-level:**
```json
{
  "new_prompts": [ ... ]
}
```

The top-level key is `"new_prompts"` — NOT `"prompts"`, NOT `"results"`.

**Each prompt object MUST include ALL of these top-level fields:**
| Field | Required | Source |
|-------|----------|--------|
| `title` | yes | copied from batch input |
| `text_en_full` | yes | copied verbatim from batch input |
| `text_zh_full` | yes | copied from batch input (preserve as-is; do NOT regenerate) |
| `category` | yes | copied from batch input |
| `source_file` | yes | copied from batch input |
| `statements` | yes | array — AI-generated |

**Each statement object MUST include ALL of these fields:**
| Field | Required | Type |
|-------|----------|------|
| `text_en` | **YES** | string — copied from batch input's pre-split segment |
| `text_zh` | **YES** | string — AI-generated Chinese translation |
| `sort_order` | **YES** | integer — copied from batch input |
| `type_id` | **YES** | integer or null — AI-assigned |
| `words` | **YES** | array — AI-extracted (can be `[]`) |

**Each word object MUST use these EXACT field names:**
```json
{"word_en": "cinematic", "word_zh": "电影级的", "position_start": 0, "position_end": 9}
```

The field names are: `word_en` `word_zh` `position_start` `position_end`.
NOT `en`/`zh`/`start`/`end`. NOT `difficult_words`. NOT `difficult_word` as the array key — the array key is `"words"`.

#### PER-BATCH VALIDATION (MANDATORY)

After writing EACH batch output file, validate it immediately with this check:

```bash
python3 -c "
import json
d = json.load(open('/tmp/prompt-batches/batch-NNN-out.json'))
prompts = d['new_prompts']
print(f'prompts: {len(prompts)}')
for i, p in enumerate(prompts):
    assert p.get('text_en_full'), f'prompt {i}: missing text_en_full'
    assert p.get('title') is not None, f'prompt {i}: missing title'
    stmts = p.get('statements', [])
    for j, s in enumerate(stmts):
        assert s.get('text_en'), f'prompt {i} stmt {j}: missing text_en'
        assert s.get('sort_order') is not None, f'prompt {i} stmt {j}: missing sort_order'
        assert s.get('type_id') is not None, f'prompt {i} stmt {j}: missing type_id'
        assert isinstance(s.get('words'), list), f'prompt {i} stmt {j}: words is not a list'
        for k, w in enumerate(s['words']):
            assert w.get('word_en'), f'prompt {i} stmt {j} word {k}: missing word_en'
            assert w.get('position_start') is not None, f'prompt {i} stmt {j} word {k}: missing position_start'
    wc = sum(len(s['words']) for s in stmts)
    print(f'  [{i}] {p[\"title\"]}: {len(stmts)} stmts, {wc} words')
print('VALID — all checks passed')
"
```

If this check fails for ANY batch, fix that batch before proceeding to the next one or to merge. A failed batch means invalid fields that will silently drop data during merge.

**NEVER skip per-batch validation.** It catches the #1 cause of data loss: sub-agents using slightly different field names (e.g., `difficult_words` instead of `words`, or omitting `text_en`/`sort_order` from statements).

#### Analysis rules

For each new prompt, do the following:

**3a. Split into semantic segments**

Split the English prompt at natural semantic boundaries — commas, conjunctions, or where the topic shifts. Each segment should be a meaningful phrase. Typically 3-8 segments per prompt. Preserve original whitespace and punctuation exactly.

**3b. Assign statement types**

For each segment, pick the best-matching `type_id` from the available statement types returned by Step 2. Match semantically:
- Segments about lighting/atmosphere → "光照氛围" type
- Segments about camera/framing → "镜头构图" type
- Segments about the main subject → "场景主体" type
- If no existing type fits well, leave `type_id` as `null`.

**3c. Translate each segment to Chinese**

Provide a faithful Chinese translation for every segment. This is always needed — source files only have full-text Chinese (`text_zh_full`), not segment-level translations. Make translations natural and idiomatic in Chinese.

**3d. Translate the full prompt (text_zh_full)**

If the source file already provides `text_zh_full` and it's not empty, use it as-is. Only generate a new `text_zh_full` when the source has none — in that case, compose a natural Chinese paragraph from the segment translations.

**3e. Extract difficult words**

For each segment, identify words that are:
- **Uncommon or specialized** (e.g., "colossal", "overcast", "cinematic", "canopy", "dune")
- **Art/photography terminology** (e.g., "bokeh", "depth of field", "volumetric", "ambient occlusion")
- **NOT basic words**: skip articles, prepositions, conjunctions, common verbs (be/have/do/modal), pronouns, numbers

For each difficult word:
- `word_en`: the English word exactly as it appears in the text
- `word_zh`: Chinese translation/explanation
- `position_start`: character index in the FULL `text_en_full` string (0-based)
- `position_end`: character index in the FULL `text_en_full` (exclusive)

**CRITICAL**: Calculate positions against the original `text_en_full` field, not the segment text.

#### Output format

The final output goes to `/tmp/prompt_analysis.json`:

```json
{
  "new_prompts": [
    {
      "title": "建于悬崖的巨型神庙废墟",
      "text_en_full": "Generate epic Unreal Engine 5 fantasy landscape, stormy overcast daylight...",
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
            {"word_en": "epic", "word_zh": "史诗的", "position_start": 9, "position_end": 13}
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

- **Confirm column mapping with the user in Step 1.** Never extract without asking — especially when the file has multiple English columns. Show a mapping table and wait for confirmation.
- **Per-batch validation is MANDATORY.** Run the validation snippet on every `batch-NNN-out.json` before proceeding. A single field name mismatch (`difficult_words` vs `words`, missing `text_en`, missing `sort_order`) will silently drop all words or statements during merge.
- **The field name is `"words"`, NOT `"difficult_words"`.** The array key on each statement is `words`. Each word object uses `word_en`/`word_zh`/`position_start`/`position_end` — nothing else.
- **Every statement MUST have `text_en`, `text_zh`, `sort_order`, `type_id`, and `words`.** Copy `text_en` and `sort_order` from the batch input's pre-split segments — do NOT omit them.
- **Every prompt MUST have `title`, `text_en_full`, `text_zh_full`, `category`, and `source_file`.** Copy these verbatim from the batch input.
- **Words must reference positions in the FULL English text,** not the segment. Wrong positions will break the UI word highlighting.
- **Never hardcode translations or word lists.** All translations, classifications, and word extraction must be done fresh by Claude.
- **Validate before importing.** Always run `ai_translate.py --validate` on the merged JSON before Step 4.
- **Check word counts before importing.** If the merge reports 0 words but you expected words, stop — a batch format issue caused data loss. Fix and re-merge.
- **For `--dir` mode, Step 3 (AI analysis) is NOT optional.** The source files have no Chinese translations and no word annotations. You MUST run Step 3 to generate `text_zh_full`, statement `text_zh`, and `words` before importing. Skipping Step 3 produces empty translations and zero highlighted words.
- **Do NOT create ad-hoc /tmp scripts to bypass the skill pipeline.** If the data format doesn't fit, extend `parse_file.py` in the skill directory. The skill's 4-step pipeline (parse → fetch context → AI analysis → import) must always run end-to-end.
