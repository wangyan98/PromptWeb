# 语句本 & 单词本 — 设计文档

> 日期：2026-07-20
> 状态：已确认

## 1. 概述

在现有 PromptWeb 基础上新增两个独立页面：

- **语句本** (`/statements`)：数据库中所有拆分语句按类型分类展示，以表格形式呈现，`text_en` 去重。
- **单词本** (`/words`)：所有高亮单词卡片汇总展示，卡片网格布局，`word_en` 去重聚合，背景色随语句类型变化。

---

## 2. 数据模型（现有，不变更）

```
Statement           PromptWord           StatementType
├─ id               ├─ id                ├─ id
├─ prompt_id        ├─ prompt_id         ├─ name
├─ text_en          ├─ statement_id      ├─ color
├─ text_zh          ├─ word_en           └─ sort_order
├─ sort_order       ├─ word_zh
└─ type_id          ├─ position_start
                    └─ position_end
```

### 去重规则

| 页面 | 去重字段 | 聚合逻辑 |
|------|---------|---------|
| 语句本 | `text_en` | GROUP BY `text_en`，`type_id` 取出现次数最多的类型，收集所有 `prompt_ids` |
| 单词本 | `word_en` | GROUP BY `word_en`，聚合 `word_zh`（取最常见的释义），收集所有关联类型及次数，收集 `prompt_ids` |

---

## 3. 路由 & 导航

### 新增路由

```
/statements   → StatementBookPage.vue
/words        → WordBookPage.vue
```

### 侧边栏更新

在现有 展示/管理 基础上增加两个入口：

```
📋 展示    → /prompts
📖 语句本  → /statements   (新增)
📝 单词本  → /words         (新增)
⚙️ 管理    → /manage
```

---

## 4. 页面设计

### 4.1 语句本 (`/statements`)

**布局**：表格 + 顶部工具栏 + 后端分页

```
┌──────────────────────────────────────────────────────────┐
│  🔍 搜索语句 (中/英文)...   [全部类型 ▾]      共 523 条    │
├──────┬──────────┬────────────────────┬──────────┬────────┤
│  #   │ 类型     │ 英文语句            │ 中文翻译  │ 来源   │
├──────┼──────────┼────────────────────┼──────────┼────────┤
│  1   │ 场景主体  │ A majestic dragon  │ 威严的龙  │ #3 →   │
│  2   │ 光照氛围  │ Golden hour light  │ 金色时光  │ #12 →  │
│ ...  │          │                    │          │        │
├──────┴──────────┴────────────────────┴──────────┴────────┤
│                ← 上一页   1 / 44   下一页 →              │
└──────────────────────────────────────────────────────────┘
```

**功能要点**：
- 搜索框：模糊匹配 `text_en` / `text_zh`
- 类型下拉：筛选特定类型，选项格式 "类型名 (数量)"，默认 "全部类型"
- 来源列：显示关联的 Prompt ID 列表，点击跳转到 `/prompts` 并定位
- 后端分页，每页 20 条
- 类型徽章使用该类型定义的颜色

### 4.2 单词本 (`/words`)

**布局**：卡片网格 + 搜索 + 后端分页 + 显示模式切换

```
┌──────────────────────────────────────────────────────────┐
│  🔍 搜索单词...                    共 186 词  [设置 ⚙]   │
│                          显示模式: (渐变) | 纯色 | 色点    │
├──────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ ● ● ●    │ │ ● ●      │ │ ●        │ │ ● ●      │   │
│  │cinematic │ │ethereal  │ │dragon    │ │ornate    │   │
│  │ 电影般的  │ │ 空灵的    │ │ 龙       │ │ 华丽的    │   │
│  │ 28次     │ │ 15次     │ │ 18次     │ │ 22次     │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│  ...                                                     │
├──────────────────────────────────────────────────────────┤
│                ← 上一页   1 / 13   下一页 →              │
└──────────────────────────────────────────────────────────┘
```

**功能要点**：
- 搜索框：模糊匹配 `word_en` / `word_zh`
- 卡片 = 亮黄色/类型色背景 + 英文(上) + 中文释义(中) + 出现次数(下)
- 顶部彩色圆点行标示该单词关联的所有语句类型
- 后端分页，每页 12 张卡片
- 点击卡片可展开详情（关联的 Prompt 列表）

### 4.3 单词卡三种显示模式

模式通过 `localStorage` 持久化，默认 **方案 2（渐变）**。

#### 模式 1：主类型纯色（`solid`）

- 卡片背景色 = 出现次数最多的语句类型的颜色
- 底部半透明小标签展示所有类型名及对应次数
- 单类型时仅显示一个标签

#### 模式 2：渐变背景（`gradient`，默认）

- 2 种类型 = 双色渐变（`linear-gradient(135deg, color1 55%, color2 100%)`）
- 3+ 种类型 = 多色渐变（按占比分配色标位置）
- 单类型 = 纯色（同模式 1）
- 渐变色标按出现次数占比计算

#### 模式 3：主色 + 色点指示器（`dots`）

- 卡片背景色 = 出现次数最多的类型的颜色（纯色）
- 卡片顶部一行彩色小圆点，每个点代表一个关联类型
- hover 圆点显示 tooltip：类型名 + 出现次数
- 单类型 = 1 个圆点，多类型 = 多个圆点

**模式切换器**：位于搜索栏右侧，使用 tabs/segmented-control 样式的按钮组。

### 4.4 设置存储

```typescript
// stores/settings.ts - 新增
interface UserSettings {
  wordCardDisplayMode: 'gradient' | 'solid' | 'dots'
}
// 默认值: { wordCardDisplayMode: 'gradient' }
// 存储在 localStorage key: 'promptweb-settings'
```

---

## 5. API 设计

### 5.1 语句全局查询

```
GET /api/statements/global?type_id=&search=&page=1&page_size=20
```

**响应**：
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "text_en": "A majestic dragon perched on a crystal throne",
        "text_zh": "一条威严的龙栖于水晶王座",
        "type_id": 4,
        "type_name": "场景主体",
        "type_color": "#e57373",
        "statement_ids": [5, 23, 41],
        "prompt_ids": [3, 12, 19],
        "count": 3
      }
    ],
    "total": 523,
    "page": 1,
    "page_size": 20
  }
}
```

**去重逻辑**：
- `GROUP BY text_en`
- `type_id` 取该语句在数据库中出现次数最多的 `type_id`
- `statement_ids` / `prompt_ids` 收集所有出现位置
- `search` 参数同时对 `text_en` 和 `text_zh` 做 `ILIKE` 模糊匹配

### 5.2 单词全局查询

```
GET /api/words/global?search=&page=1&page_size=12
```

**响应**：
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "word_en": "cinematic",
        "word_zh": "电影般的",
        "total_count": 28,
        "types": [
          { "type_id": 6, "type_name": "画质风格", "type_color": "#90a4ae", "count": 20 },
          { "type_id": 2, "type_name": "光照氛围", "type_color": "#ffb74d", "count": 5 },
          { "type_id": 1, "type_name": "固定开头", "type_color": "#4fc3f7", "count": 3 }
        ],
        "prompt_ids": [1, 3, 5, 7, 12, ...]
      }
    ],
    "total": 186,
    "page": 1,
    "page_size": 12
  }
}
```

**去重逻辑**：
- `GROUP BY word_en`
- `word_zh` 取出现次数最多的释义
- `types` 数组按 count 降序排列，第一个为 "主类型"
- `prompt_ids` 收集所有关联 Prompt

---

## 6. 文件变更清单

### 新增文件

| 文件 | 说明 |
|------|------|
| `frontend/src/views/StatementBookPage.vue` | 语句本页面（表格+工具栏+分页） |
| `frontend/src/views/WordBookPage.vue` | 单词本页面（卡片网格+搜索+分页+模式切换） |
| `frontend/src/components/WordCardGrid.vue` | 单词卡片网格组件（支持 solid/gradient/dots 三种模式） |
| `frontend/src/stores/settings.ts` | 用户设置 store（wordCardDisplayMode） |
| `frontend/src/api/global.ts` | 全局查询 API 封装 |
| `backend/app/api/statements_global.py` | 语句全局查询路由 |
| `backend/app/api/words_global.py` | 单词全局查询路由 |

### 修改文件

| 文件 | 修改内容 |
|------|---------|
| `frontend/src/components/SideNav.vue` | navItems 增加 "语句本" 和 "单词本" 两项 |
| `frontend/src/router/index.ts` | 增加 `/statements`、`/words` 两条路由 |
| `backend/app/main.py` | 注册 `statements_global`、`words_global` 路由 |

---

## 7. 不在范围

- Prompt 详情页改动（现有功能不变）
- 单词本的收藏/标记功能
- 语句本的批量导出
- 管理后台对语句本/单词本的编辑功能（只读浏览）
