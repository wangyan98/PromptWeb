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
