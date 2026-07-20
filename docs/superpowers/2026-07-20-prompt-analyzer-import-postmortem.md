# Prompt Analyzer 导入复盘

> 日期：2026-07-20
> 来源：使用 prompt-analyzer skill 分析「100套奇幻视频提示词.xlsx」时遇到的一系列问题

## 背景

使用 prompt-analyzer skill 对「100套奇幻视频提示词.xlsx」执行完整的 4 步分析导入流程（inspect → fetch context → AI 分析 → 批量导入），过程中发现多个问题导致需要反复清库重跑。本文档记录问题根因及后续添加的防护措施。

---

## 问题清单

### 问题 1：列映射选错（Step 1）

**现象**：第一次运行时选了列 6（对应图片提示词），导入完成后用户指出想要的是视频提示词（列 3）。整批 100 条数据删除重跑。

**根因**：文件有多个英文列 — 列 3 是视频提示词、列 6 是图片提示词。Claude 在看到 inspect 输出后直接做了决策，没有向用户确认。

**修复**（SKILL.md Step 1 — Phase 1b 确认门）：
- 新增 **强制确认步骤**：inspect 后必须以表格展示列映射建议，明确标注"你的选择"和"替代列"，等高亮用户确认后才能执行 `--extract`
- 特别标注多英文列风险：如果文件有多个英文列，必须明确指出来让用户选

---

### 问题 2：批次输出字段名不统一（Step 3）

**现象**：子代理在生成 `batch-NNN-out.json` 时，部分批次把单词数组的 key 命名为 `difficult_words` 而非 `words`，导致 merge 后 word count = 0。第一次导入 1,158 条语句但 0 个单词。

**根因**：SKILL.md 原文只说"提取难词"、"words 字段"，但没有以绝对明确的契约形式列出必须使用的字段名。子代理自由发挥，用了语义相近但不同的 `difficult_words`。

**修复**（SKILL.md Step 3 — Batch Output Format Contract）：
- 新增 **字段名契约表**，三层结构（prompt / statement / word），每层列出所有必填字段、类型和来源
- 明确声明 `"words"` 是唯一合法的数组 key，NOT `"difficult_words"`
- word 对象字段名固定为 `word_en` / `word_zh` / `position_start` / `position_end`，不允许变体

---

### 问题 3：批次输出结构漂移（Step 3）

**现象**：部分批次输出的 statement 对象缺少 `text_en` 和 `sort_order` 字段，部分批次输出的 prompt 对象缺少 `title` 和 `text_en_full`。这些缺陷在合并后才被发现（validate 报 25+ 个 missing field 错误），此时已无法定位是哪个批次的问题。

**根因**：子代理在分析 prompt 时，只输出了 AI 生成的内容（`text_zh`、`type_id`、words），没有保留输入数据中的既有字段（`text_en`、`sort_order`）。即子代理把 batch 输入当作参考而非模板，重写了语句结构。

**修复**（SKILL.md Step 3 — Per-Batch Validation + 字段来源表）：
- **字段来源表**中明确标注：`text_en` 和 `sort_order` 必须从 batch 输入的预拆分片段中复制，不可省略
- prompt 级别的 `title`/`text_en_full`/`text_zh_full`/`category`/`source_file` 必须从 batch 输入逐字复制
- 新增 **逐批校验脚本**：每写完一个 batch-out 文件就立即运行校验，检查所有必填字段是否存在，word 对象格式是否正确。错误当场发现、当场修复，不再拖到合并阶段

---

### 问题 4：错误发现太晚，修复成本高

**现象**：问题 2 和问题 3 均在 Step 3 末尾的 `--merge` + `--validate` 阶段才暴露。此时 4 个批次已完成，需要逐个排查是哪个批次出错、手动修复、重新合并、重新校验。最严重的一次：导入成功但 words=0，整个数据库清空重来。

**根因**：缺少中间质量闸门。4 个批次并行处理后直接合并，没有一个批次级别的检查点。

**修复**（双重闸门）：
1. **逐批闸门（Step 3）**：每个 batch-out 写入后立即跑校验脚本，验证 prompts/stmts/words 三层结构完整。通过才继续下一个批次或合并
2. **合并后闸门（Step 3→4）**：merge 输出中检查 word count — 如果预期有词但合并报 0，立即停止排查，不要盲目导入

---

## 新增防护措施总览

| 步骤 | 闸门 | 阻止的问题 |
|------|------|-----------|
| Step 1b | 列映射确认表，等待用户 yes | 选错英文列 |
| Step 3（每批） | 逐批校验脚本（字段完整性+格式正确性） | 字段名漂移、结构残缺 |
| Step 3（合并后） | word count 合理性检查 | 静默数据丢失 |
| Step 3→4 | `--validate` 终验 | 合并后的结构错误 |

## 涉及的文件变更

- `skills/prompt-analyzer/SKILL.md` — 新增 Step 1 确认门、Step 3 格式契约、逐批校验要求、Notes 约束
- 相关 commit: `81d41ff docs(prompt-analyzer): add guardrails to prevent common import errors`
