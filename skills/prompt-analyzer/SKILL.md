---
name: prompt-analyzer
description: Analyze text-to-image prompt files (xlsx/csv/json) — split English prompts into semantic segments, label them with statement types, provide Chinese translations (only when source lacks them), extract difficult English vocabulary, and batch-import everything into PromptWeb. Use when the user mentions analyzing prompts, importing prompt data, splitting prompts, or provides a path to a prompt data file. Also use when the user wants to extract difficult English words from prompts, build Chinese-English prompt mappings, or batch-process a file of image generation prompts.
---

# Prompt Analyzer

Analyze text-to-image prompt data files — semantic splitting, Chinese-English mapping, difficult word extraction — then batch-import into the PromptWeb database.

## Workflow

This skill follows a 4-step pipeline. Run each step in order.

### Step 1: Inspect and extract the file

**This is a two-phase step where Claude does the column mapping.**

#### Phase 1a: Inspect the file structure

```bash
python skills/prompt-analyzer/scripts/parse_file.py --inspect "<file_path>"
```

This prints a compact metadata JSON — format, sheet name, headers, first 5 sample rows, total row count. It does NO column detection or mapping. That's your job.

**You (Claude) must read this output and decide:**
- Which column index contains the English prompt text? (required)
- Which column index contains the Chinese translation? (optional)
- Which column index contains the title/short name? (optional)
- Which column index contains the category? (optional)
- For xlsx files with multiple sheets, does the auto-detected sheet look correct, or should `--sheet` override?

#### Phase 1b: Extract with Claude's column choices

```bash
python skills/prompt-analyzer/scripts/parse_file.py --extract "<file_path>" \
  --en <N> --zh <M> --title <P> --cat <Q>
```

Only `--en` is required. Use `--sheet NAME` if the auto-detected sheet is wrong.

This outputs the standard prompt JSON array to stdout — redirect to a file:

```bash
python skills/prompt-analyzer/scripts/parse_file.py --extract "data.xlsx" \
  --en 3 --zh 4 --title 2 --cat 1 > /tmp/prompt_parsed.json
```

**Example:** From an inspect output with headers like:
```
["编号", "类别", "场景主题（中文）", "视频提示词（英文）", "视频提示词（中文）"]
```
You'd choose: `--en 3 --zh 4 --title 2 --cat 1`

**For JSON files**, the inspect output shows all top-level keys — you identify which keys map to which fields, and pass their positional indices to `--extract`. Alternatively, if the JSON already uses standard keys (`text_en_full`, `text_zh_full`, `title`), you can run `--extract` without any column flags and it will auto-detect from known keys.

If the script fails:
- Check that the file exists and is .xlsx/.csv/.json
- If openpyxl is needed: `pip install openpyxl`
- For unusual formats, you may read the file yourself and construct the JSON manually

### Step 2: Fetch DB context

```bash
python skills/prompt-analyzer/scripts/fetch_context.py
```

This outputs JSON with:
- `statement_types`: available types from the DB (id, name, color)
- `existing_prompts`: prompts already in the DB, each with `has_statements` flag

If the API is unreachable, remind the user to start the PromptWeb backend and set `PROMPT_API_URL` if not using the default `http://localhost:8000`.

### Step 3: AI analysis

**This is the core intelligence step.** You (Claude) do ALL translation, type classification, and word extraction. No hardcoded data — every analysis is generated fresh based on your language understanding.

The `ai_translate.py` script is a **batch I/O helper only** — it does zero intelligence. Use it for splitting large files and validating output. All semantic work happens in this step, by you.

**Deduplication first:** Compare parsed rows against existing_prompts from Step 2. A prompt is already analyzed if there's an existing prompt with matching `text_en_full` AND `has_statements: true`. Skip those.

#### Small batch workflow (≤30 new prompts)

Read the parsed JSON from Step 1 and context from Step 2 directly. Produce the analysis JSON yourself and write it to `/tmp/prompt_analysis.json`.

#### Large batch workflow (>30 new prompts)

Use the batch helper to split, then analyze batch by batch:

```bash
# 1. Split parsed prompts into batches of 30
python skills/prompt-analyzer/scripts/ai_translate.py --split 30 < /tmp/prompt_parsed.json
# → writes batch-001.json ... batch-00N.json to /tmp/prompt-batches/

# 2. For EACH batch file, read it, analyze the prompts in it,
#    and write batch-NNN-out.json with the SAME structure.
#    (You do this — see "Analysis rules" below.)

# 3. Merge all batch outputs
python skills/prompt-analyzer/scripts/ai_translate.py --merge
# → writes /tmp/prompt_analysis.json

# 4. Validate the merged output
python skills/prompt-analyzer/scripts/ai_translate.py --validate /tmp/prompt_analysis.json
```

Each batch output file must have this structure (same as the final format, just scoped to that batch):
```json
{
  "new_prompts": [ ... ]
}
```

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

- **Batch large files.** For >30 new prompts, use `ai_translate.py --split` to create manageable chunks. Process each chunk in one AI turn, writing `batch-NNN-out.json`. Then `--merge` and `--validate`.
- **Words must reference positions in the FULL English text,** not the segment. Wrong positions will break the UI word highlighting.
- **Never hardcode translations or word lists.** All translations, classifications, and word extraction must be done fresh by Claude. The old approach of embedding 650+ hardcoded Chinese translations in the script is forbidden.
- **Validate before importing.** Always run `ai_translate.py --validate` on the final merged JSON before Step 4.
- **Verify each step's output** before proceeding to the next step.
