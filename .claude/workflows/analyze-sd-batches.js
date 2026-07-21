export const meta = {
  name: 'analyze-sd-batches',
  description: 'AI-analyze SD prompt batches: translate to Chinese, classify type_id, extract difficult words with positions. Each batch = 5 prompts.',
  phases: [
    { title: 'Analyze', detail: 'AI analysis and validation per batch' },
  ]
}

const BATCHES = args.batches
const BATCH_DIR = '/tmp/prompt-batches'

const STMT_TYPES = `Statement Types (type_id):
1=固定开头(quality tags like score_9, masterpiece, best quality - fixed opening boilerplate)
2=光照氛围(lighting, atmosphere, time of day, weather)
3=镜头构图(camera angle, composition, framing, POV, shot type)
4=场景主体(main subject, character, object, action, what is depicted)
5=材质细节(material, texture, detail, surface properties, rendering quality)
6=画质风格(art style, quality renderer, aesthetic tags, artist references)
7=色彩色调(color palette, tone, saturation, color temperature)
8=环境背景(environment, background, setting, location, scene context)`

const ANALYSIS_PROMPT = (inputFile, outputFile, batchLabel) => `You are an SD prompt analysis specialist. Process batch ${batchLabel} with HIGH QUALITY — every statement MUST have a proper Chinese translation and a type_id.

## STEP 1: Read Input

Read ${inputFile}. It contains 5 SD prompts, each pre-split into comma/paren-separated statement segments with text_en and sort_order already filled in.

## STEP 2: Analyze Each Prompt

For EVERY statement in EVERY prompt, you MUST provide:
- **text_zh**: Natural, idiomatic Chinese translation of the English SD tag. For common SD tags use standard translations (e.g., "masterpiece"→"杰作", "depth of field"→"景深", "cinematic lighting"→"电影级布光", "intricate details"→"精细细节", "8k resolution"→"8K分辨率"). For artist names, translate as "由[Name]绘制". For Lora tags like "<lora:name:weight>", translate as "Lora模型[name,权重:weight]". Leave BREAK, score tags in Chinese too ("BREAK"→"分隔", "score_9"→"质量分9").
- **type_id**: One of 1-8 (or null if truly unclassifiable). See types below.
- **words**: Array of difficult/uncommon words from this statement. Extract artist names, technical photography/art terms, uncommon SD tags, specialized vocabulary. For each word provide word_en (exact text from the statement), word_zh (Chinese translation), position_start and position_end (0-based character indices in the FULL text_en_full, NOT the segment text).

${STMT_TYPES}

## STEP 3: Write Output

Write the output to ${outputFile}. Use this EXACT structure:

\`\`\`json
{
  "new_prompts": [
    {
      "title": "original title here",
      "text_en_full": "full original english",
      "text_zh_full": "",
      "category": "category name",
      "source_file": "original filename.xlsx",
      "statements": [
        {
          "text_en": "segment text",
          "text_zh": "Chinese translation here",
          "sort_order": 1,
          "type_id": 6,
          "words": [
            {"word_en": "difficult_term", "word_zh": "中文翻译", "position_start": 12, "position_end": 26}
          ]
        }
      ]
    }
  ]
}
\`\`\`

CRITICAL RULES:
- Copy text_en, sort_order, title, text_en_full, text_zh_full, category, source_file VERBATIM from input
- EVERY statement MUST have text_zh (Chinese translation) — never leave it empty
- EVERY statement MUST have a type_id — never null unless truly impossible to classify
- words position_start/position_end are 0-based indices in text_en_full (the FULL English text), NOT within the segment
- words array can be empty [] if no difficult words, but it MUST be present
- **CRITICAL: Each word MUST be a JSON OBJECT {\"word_en\":..., \"word_zh\":..., \"position_start\":..., \"position_end\":...} — NEVER use an array/list [\"text\", \"translation\", start, end]. Using an array instead of an object WILL cause data loss during import.**
- artist names (e.g., "by Greg Rutkowski") ARE difficult words worth extracting
- For Lora/model tags like "<lora:PersonaCutIn_XLPD_V2:0.8>", extract as a word with translation like "Lora:PersonaCutIn(权重0.8)"
- Make the Chinese translations CONCISE (2-8 characters each for simple tags, full phrase translation for descriptive tags)

## STEP 4: Validate Output

Run this validation immediately after writing:
\`\`\`bash
python3 -c "
import json
d = json.load(open('${outputFile}'))
prompts = d['new_prompts']
print(f'prompts: {len(prompts)}')
for i, p in enumerate(prompts):
    assert p.get('text_en_full'), f'prompt {i}: missing text_en_full'
    assert p.get('title') is not None, f'prompt {i}: missing title'
    stmts = p.get('statements', [])
    for j, s in enumerate(stmts):
        assert s.get('text_en'), f'prompt {i} stmt {j}: missing text_en'
        assert s.get('text_zh'), f'prompt {i} stmt {j}: missing text_zh'
        assert s.get('sort_order') is not None, f'prompt {i} stmt {j}: missing sort_order'
        assert s.get('type_id') is not None, f'prompt {i} stmt {j}: missing type_id'
        assert isinstance(s.get('words'), list), f'prompt {i} stmt {j}: words not list'
        for k, w in enumerate(s['words']):
            assert isinstance(w, dict), f'prompt {i} stmt {j} word {k}: NOT a dict — got {type(w).__name__}. Use OBJECT format {{\"word_en\":...,\"word_zh\":...,\"position_start\":...,\"position_end\":...}}, NOT a list/array.'
            assert w.get('word_en'), f'prompt {i} stmt {j} word {k}: missing word_en'
            assert w.get('position_start') is not None, f'prompt {i} stmt {j} word {k}: missing position_start'
    wc = sum(len(s['words']) for s in stmts)
    print(f'  [{i}] {p[\"title\"]}: {len(stmts)} stmts, {wc} words')
print('VALID — all checks passed')
\`\`\`

If validation FAILS, fix the output and re-validate. Do NOT proceed until it passes.
If validation PASSES, report the summary: "batch-XXXX: N prompts, M statements, W words — VALID"`

// If only a single batch, process it directly
if (BATCHES.length === 1) {
  const padded = String(BATCHES[0]).padStart(4, '0')
  const inputFile = `${BATCH_DIR}/batch-${padded}.json`
  const outputFile = `${BATCH_DIR}/batch-${padded}-out.json`
  const result = await agent(ANALYSIS_PROMPT(inputFile, outputFile, padded), {
    label: `batch-${padded}`,
    phase: 'Analyze',
  })
  log(result || `batch-${padded}: agent returned empty`)
} else {
  // Process all batches concurrently (with internal concurrency cap)
  const results = await parallel(
    BATCHES.map(batchNum => () => {
      const padded = String(batchNum).padStart(4, '0')
      const inputFile = `${BATCH_DIR}/batch-${padded}.json`
      const outputFile = `${BATCH_DIR}/batch-${padded}-out.json`
      return agent(ANALYSIS_PROMPT(inputFile, outputFile, padded), {
        label: `batch-${padded}`,
        phase: 'Analyze',
      })
    })
  )

  const succeeded = results.filter(r => r && r.includes('VALID')).length
  const total = results.length
  log(`Completed: ${succeeded}/${total} batches validated successfully`)
  if (succeeded < total) {
    log(`WARNING: ${total - succeeded} batches may have issues — check output files`)
  }
}
