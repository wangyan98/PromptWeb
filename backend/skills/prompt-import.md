---
name: prompt-import
description: Analyze Excel files containing text-to-image prompts, auto-detect columns, and import into PromptWeb database
---

# Prompt Import Skill

Analyze an Excel file containing text-to-image prompts and import them into the PromptWeb database.

## Input

- Path to an `.xlsx` or `.xls` file
- The file may have multiple sheets and varying column structures

## Process

### Step 1: Parse the Excel file

Read all sheets using `openpyxl`. Identify which sheet contains prompt data (skip summary/instruction sheets).

### Step 2: Auto-detect columns

For the data sheet, scan the header row and first 3-5 data rows. Identify:
- **English prompt column**: contains long English text with photography/art keywords like "Generate", "epic", "Unreal Engine", "cinematic", "8K", etc.
- **Chinese/title column**: contains Chinese text describing scenes
- **Category column**: contains short classification labels like "远古遗迹", "森林自然", etc.

Return the column mapping as JSON.

### Step 3: Extract data rows

For each data row, extract:
```json
{
  "title": "scene title in Chinese",
  "text_en_full": "full English prompt",
  "text_zh_full": "Chinese translation or description",
  "category": "category label",
  "source_file": "original filename"
}
```

### Step 4: Call the PromptWeb API

POST each extracted prompt to `POST /api/import/confirm` with the array of items.

## Output Format

Return a JSON summary:
```json
{
  "sheet_used": "Sheet2",
  "total_rows": 100,
  "imported": 100,
  "column_mapping": {
    "en_column": "完整提示词（英文 · 可直接复制）",
    "zh_column": "场景主题（中文）",
    "cat_column": "类别"
  }
}
```
