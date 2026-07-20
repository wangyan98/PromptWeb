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
