---
name: prompt-split
description: Split an English text-to-image prompt into semantic segments with type labels and extract difficult vocabulary words
---

# Prompt Split Skill

Analyze a single English text-to-image prompt, split it into semantic sentence segments, label each segment with a type, and extract difficult vocabulary words.

## Input

A JSON object:
```json
{
  "prompt_id": 1,
  "text_en_full": "Generate epic Unreal Engine 5 fantasy landscape, stormy overcast daylight, cinematic environmental photography, ancient colossal temple ruins built into a cliff face...",
  "text_zh_full": "建于悬崖的巨型神庙废墟",
  "statement_types": [
    {"id": 1, "name": "固定开头"},
    {"id": 2, "name": "光照氛围"},
    ...
  ]
}
```

## Process

### Step 1: Split into sentences

Split the English prompt at natural semantic boundaries (commas, semicolons, periods, question/exclamation marks, and their Chinese equivalents). Each segment should be a meaningful phrase. Typically 3-8 segments.

For each segment:
- Extract the English text
- Provide a Chinese translation
- Assign a `type_id` from the available statement types
- Set `sort_order` (1-based index)

### Step 2: Extract difficult vocabulary

For each segment, identify words that are:
- Uncommon or specialized (e.g., "colossal", "overcast", "cinematic")
- NOT basic function words (the, a, an, in, on, at, of, to, for, with, and, or, but, is, are, was, were, be, been, being, have, has, had, do, does, did, will, would, can, could, shall, should, may, might, must, it, its, this, that, these, those)

For each difficult word:
- Provide the word in English
- Provide the Chinese translation
- Record `position_start` and `position_end` (character indices in the full English text)

### Step 3: Call the PromptWeb API

1. POST statements to `POST /api/prompts/{prompt_id}/statements`
2. For each statement, POST its words to `POST /api/statements/{statement_id}/words`

## Output Format

```json
{
  "prompt_id": 1,
  "statements": [
    {
      "text_en": "Generate epic Unreal Engine 5 fantasy landscape",
      "text_zh": "生成史诗级虚幻引擎5奇幻场景",
      "sort_order": 1,
      "type_id": 1
    },
    ...
  ],
  "words": [
    {
      "statement_index": 2,
      "word_en": "colossal",
      "word_zh": "巨大的",
      "position_start": 105,
      "position_end": 113
    },
    ...
  ]
}
```
