# 语句本 & 单词本 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two new read-only browse pages — Statement Book (table of deduplicated statements grouped by type) and Word Book (card grid of deduplicated words with type-colored backgrounds).

**Architecture:** Two new backend API endpoints for cross-Prompt global queries with `GROUP BY` deduplication. Two new frontend views with a shared settings store for word card display mode persistence. Follows existing patterns: FastAPI router + service for backend, Vue 3 SFC + Pinia store for frontend.

**Tech Stack:** Python FastAPI + SQLAlchemy async + PostgreSQL (backend); Vue 3 Composition API + TypeScript + Pinia + Vite (frontend)

## Global Constraints

- Theme: dark (`--color-bg-primary: #000000`), accent blue (`--color-accent: #3b82f6`)
- All APIs return `{ code: 0, data: ..., message: "ok" }` envelope
- Frontend API client auto-unwraps envelope via response interceptor — code accesses `res.data` directly
- Follow existing naming conventions: PascalCase for Vue components, snake_case for Python functions, camelCase for TypeScript
- Backend pagination: `page`/`page_size` query params returning `{ items, total, page, page_size }`
- No new database migrations needed — queries use existing tables only

---

### Task 1: Backend — Statement Global Query API

**Files:**
- Create: `backend/app/api/statements_global.py`

**Interfaces:**
- Produces: `GET /api/statements/global?type_id=&search=&page=1&page_size=20` → `ApiResponse(data={items: GlobalStatementItem[], total, page, page_size})`

- [ ] **Step 1: Create the API router file**

```python
# backend/app/api/statements_global.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api", tags=["statements-global"])


@router.get("/statements/global")
async def list_statements_global(
    type_id: int | None = Query(None),
    search: str = Query(""),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    # Build WHERE clauses
    where_parts = ["1=1"]
    params = {}

    if type_id is not None:
        where_parts.append("s.type_id = :type_id")
        params["type_id"] = type_id

    if search:
        where_parts.append("(s.text_en ILIKE :search OR s.text_zh ILIKE :search2)")
        params["search"] = f"%{search}%"
        params["search2"] = f"%{search}%"

    where_clause = " AND ".join(where_parts)

    # Count query: number of distinct text_en groups
    count_sql = f"""
        SELECT COUNT(*) FROM (
            SELECT 1 FROM statements s
            WHERE {where_clause}
            GROUP BY s.text_en
        ) sub
    """
    total_result = await db.execute(text(count_sql), params)
    total = total_result.scalar() or 0

    # Main query: GROUP BY text_en, take the most common type_id
    main_sql = f"""
        SELECT
            s.text_en,
            (ARRAY_AGG(s.text_zh ORDER BY COUNT(*) DESC))[1] AS text_zh,
            (ARRAY_AGG(s.type_id ORDER BY COUNT(*) DESC))[1] AS type_id,
            (ARRAY_AGG(st.name ORDER BY COUNT(*) DESC))[1] AS type_name,
            (ARRAY_AGG(st.color ORDER BY COUNT(*) DESC))[1] AS type_color,
            ARRAY_AGG(DISTINCT s.id ORDER BY s.id) AS statement_ids,
            ARRAY_AGG(DISTINCT s.prompt_id ORDER BY s.prompt_id) AS prompt_ids,
            COUNT(*)::int AS count
        FROM statements s
        LEFT JOIN statement_types st ON s.type_id = st.id
        WHERE {where_clause}
        GROUP BY s.text_en
        ORDER BY s.text_en
        LIMIT :limit OFFSET :offset
    """
    params["limit"] = page_size
    params["offset"] = (page - 1) * page_size

    result = await db.execute(text(main_sql), params)
    rows = result.mappings().all()

    items = [
        {
            "text_en": row["text_en"],
            "text_zh": row["text_zh"] or "",
            "type_id": row["type_id"],
            "type_name": row["type_name"] or "",
            "type_color": row["type_color"] or "#3b82f6",
            "statement_ids": list(row["statement_ids"] or []),
            "prompt_ids": list(row["prompt_ids"] or []),
            "count": row["count"],
        }
        for row in rows
    ]

    return ApiResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })
```

- [ ] **Step 2: Register route in main.py**

```python
# backend/app/main.py — add two lines:
# 1) import:  from app.api import prompts, statements, words, images, statement_types, import_, statements_global
# 2) router:  app.include_router(statements_global.router)
```

Edit the file with these exact additions:

Old:
```
from app.api import prompts, statements, words, images, statement_types, import_
```
New:
```
from app.api import prompts, statements, words, images, statement_types, import_, statements_global
```

Old (before `@app.on_event("startup")`):
```
app.include_router(import_.router)
```
New:
```
app.include_router(import_.router)
app.include_router(statements_global.router)
```

- [ ] **Step 3: Verify endpoint works**

Run: `curl -s "http://localhost:8000/api/statements/global?page=1&page_size=2" | python -m json.tool`
Expected: JSON with `code: 0`, `data.items` array, `data.total` number.

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/statements_global.py backend/app/main.py
git commit -m "feat: add GET /api/statements/global with text_en dedup and type aggregation"
```

---

### Task 2: Backend — Word Global Query API

**Files:**
- Create: `backend/app/api/words_global.py`

**Interfaces:**
- Produces: `GET /api/words/global?search=&page=1&page_size=12` → `ApiResponse(data={items: GlobalWordItem[], total, page, page_size})`

- [ ] **Step 1: Create the API router file**

```python
# backend/app/api/words_global.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api", tags=["words-global"])


@router.get("/words/global")
async def list_words_global(
    search: str = Query(""),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    # Build WHERE for search
    params = {}
    where_clause = "1=1"
    if search:
        where_clause = "(pw.word_en ILIKE :search OR pw.word_zh ILIKE :search2)"
        params["search"] = f"%{search}%"
        params["search2"] = f"%{search}%"

    # Count: distinct words
    count_sql = f"""
        SELECT COUNT(*) FROM (
            SELECT 1 FROM prompt_words pw
            WHERE {where_clause}
            GROUP BY pw.word_en
        ) sub
    """
    total_result = await db.execute(text(count_sql), params)
    total = total_result.scalar() or 0

    # Main query: group by word_en, pick most common word_zh, collect prompt_ids
    main_sql = f"""
        SELECT
            pw.word_en,
            (ARRAY_AGG(pw.word_zh ORDER BY COUNT(*) DESC))[1] AS word_zh,
            COUNT(*)::int AS total_count,
            ARRAY_AGG(DISTINCT pw.prompt_id ORDER BY pw.prompt_id) AS prompt_ids
        FROM prompt_words pw
        WHERE {where_clause}
        GROUP BY pw.word_en
        ORDER BY total_count DESC, pw.word_en
        LIMIT :limit OFFSET :offset
    """
    params["limit"] = page_size
    params["offset"] = (page - 1) * page_size

    result = await db.execute(text(main_sql), params)
    rows = result.mappings().all()

    if not rows:
        return ApiResponse(data={
            "items": [], "total": total, "page": page, "page_size": page_size
        })

    # Second query: get type breakdown for the words in this page
    word_list = [row["word_en"] for row in rows]
    # PostgreSQL requires a cast for ARRAY[...]::text[] with bind params
    placeholders = ", ".join(f":w{i}" for i in range(len(word_list)))
    types_params = {f"w{i}": w for i, w in enumerate(word_list)}
    types_params.update({k: v for k, v in params.items() if k not in ("limit", "offset")})

    types_sql = f"""
        SELECT
            pw.word_en,
            st.id AS type_id,
            st.name AS type_name,
            st.color AS type_color,
            COUNT(*)::int AS count
        FROM prompt_words pw
        JOIN statements s ON pw.statement_id = s.id
        LEFT JOIN statement_types st ON s.type_id = st.id
        WHERE pw.word_en IN ({placeholders})
        GROUP BY pw.word_en, st.id, st.name, st.color
        ORDER BY pw.word_en, count DESC
    """

    types_result = await db.execute(text(types_sql), types_params)
    types_rows = types_result.mappings().all()

    # Build types lookup: word_en → list of types
    types_map: dict[str, list[dict]] = {}
    for tr in types_rows:
        w = tr["word_en"]
        if w not in types_map:
            types_map[w] = []
        types_map[w].append({
            "type_id": tr["type_id"],
            "type_name": tr["type_name"] or "",
            "type_color": tr["type_color"] or "#3b82f6",
            "count": tr["count"],
        })

    items = [
        {
            "word_en": row["word_en"],
            "word_zh": row["word_zh"] or "",
            "total_count": row["total_count"],
            "types": types_map.get(row["word_en"], []),
            "prompt_ids": list(row["prompt_ids"] or []),
        }
        for row in rows
    ]

    return ApiResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })
```

- [ ] **Step 2: Register route in main.py**

Edit `backend/app/main.py` — two changes:

Old:
```
from app.api import prompts, statements, words, images, statement_types, import_, statements_global
```
New:
```
from app.api import prompts, statements, words, images, statement_types, import_, statements_global, words_global
```

Old (after last include_router):
```
app.include_router(statements_global.router)
```
New:
```
app.include_router(statements_global.router)
app.include_router(words_global.router)
```

- [ ] **Step 3: Verify endpoint works**

Run: `curl -s "http://localhost:8000/api/words/global?page=1&page_size=3" | python -m json.tool`
Expected: JSON with `code: 0`, items have `word_en`, `word_zh`, `total_count`, `types` array (each with `type_id`, `type_name`, `type_color`, `count`), `prompt_ids`.

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/words_global.py backend/app/main.py
git commit -m "feat: add GET /api/words/global with word_en dedup and type aggregation"
```

---

### Task 3: Frontend — Settings Store

**Files:**
- Create: `frontend/src/stores/settings.ts`

**Interfaces:**
- Produces: `useSettingsStore()` Pinia store with `wordCardDisplayMode` ref (persisted to localStorage), `setDisplayMode(mode)` action.

- [ ] **Step 1: Create the settings store**

```typescript
// frontend/src/stores/settings.ts
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type WordCardDisplayMode = 'gradient' | 'solid' | 'dots'

const STORAGE_KEY = 'promptweb-settings'

interface SettingsData {
  wordCardDisplayMode: WordCardDisplayMode
}

function loadSettings(): SettingsData {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      return {
        wordCardDisplayMode: parsed.wordCardDisplayMode || 'gradient',
      }
    }
  } catch {
    // ignore parse errors, use defaults
  }
  return { wordCardDisplayMode: 'gradient' }
}

function saveSettings(data: SettingsData): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
}

export const useSettingsStore = defineStore('settings', () => {
  const initial = loadSettings()
  const wordCardDisplayMode = ref<WordCardDisplayMode>(initial.wordCardDisplayMode)

  watch(wordCardDisplayMode, (newMode) => {
    saveSettings({ wordCardDisplayMode: newMode })
  })

  function setDisplayMode(mode: WordCardDisplayMode) {
    wordCardDisplayMode.value = mode
  }

  return { wordCardDisplayMode, setDisplayMode }
})
```

- [ ] **Step 2: Verify in browser console**

After integrating (it's just a store, no visual change yet), run the frontend and paste in console:
```js
// Should log 'gradient' (default)
console.log(JSON.parse(localStorage.getItem('promptweb-settings')))
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/settings.ts
git commit -m "feat: add settings store with wordCardDisplayMode persistence"
```

---

### Task 4: Frontend — Global API Client

**Files:**
- Create: `frontend/src/api/global.ts`

**Interfaces:**
- Produces: `globalApi.getStatements(params)` and `globalApi.getWords(params)` typed functions.

- [ ] **Step 1: Create the API module**

```typescript
// frontend/src/api/global.ts
import apiClient from './client'

export interface GlobalStatementItem {
  text_en: string
  text_zh: string
  type_id: number | null
  type_name: string
  type_color: string
  statement_ids: number[]
  prompt_ids: number[]
  count: number
}

export interface WordTypeInfo {
  type_id: number | null
  type_name: string
  type_color: string
  count: number
}

export interface GlobalWordItem {
  word_en: string
  word_zh: string
  total_count: number
  types: WordTypeInfo[]
  prompt_ids: number[]
}

export interface GlobalPaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export const globalApi = {
  getStatements(params: {
    type_id?: number
    search?: string
    page?: number
    page_size?: number
  } = {}) {
    return apiClient.get('/statements/global', { params }) as Promise<{
      code: number
      data: GlobalPaginatedResponse<GlobalStatementItem>
    }>
  },

  getWords(params: {
    search?: string
    page?: number
    page_size?: number
  } = {}) {
    return apiClient.get('/words/global', { params }) as Promise<{
      code: number
      data: GlobalPaginatedResponse<GlobalWordItem>
    }>
  },
}
```

- [ ] **Step 2: Smoke test (no visual output)**

This is a pure module file — no visual test possible. It compiles if the frontend dev server doesn't error.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/global.ts
git commit -m "feat: add global API client for statements and words endpoints"
```

---

### Task 5: Frontend — StatementBookPage

**Files:**
- Create: `frontend/src/views/StatementBookPage.vue`

**Interfaces:**
- Consumes: `globalApi.getStatements()` from Task 4
- Produces: Full statement book page at `/statements`

- [ ] **Step 1: Create the page component**

```vue
<!-- frontend/src/views/StatementBookPage.vue -->
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { globalApi, type GlobalStatementItem, type GlobalPaginatedResponse } from '@/api/global'
import { statementTypesApi, type StatementTypeItem } from '@/api/statement-types'

const router = useRouter()

const items = ref<GlobalStatementItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const search = ref('')
const typeId = ref<number | null>(null)
const types = ref<StatementTypeItem[]>([])
const loading = ref(false)

onMounted(async () => {
  const res = await statementTypesApi.list()
  types.value = res.data as StatementTypeItem[]
  await loadData()
})

watch(search, () => { page.value = 1; loadData() })
watch(typeId, () => { page.value = 1; loadData() })
watch(page, () => loadData())

async function loadData() {
  loading.value = true
  try {
    const res = await globalApi.getStatements({
      search: search.value,
      type_id: typeId.value ?? undefined,
      page: page.value,
      page_size: pageSize,
    })
    const data = res.data as GlobalPaginatedResponse<GlobalStatementItem>
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function goToPrompt(promptId: number) {
  router.push('/prompts')
  // Note: selecting a specific prompt after navigation would require
  // DisplayPage to support a query param; for now, navigate to list
}

function getTypeLabel(typeName: string): string {
  return typeName || '未分类'
}

function getTypeColor(typeColor: string): string {
  return typeColor || '#3b82f6'
}

const totalPages = () => Math.max(1, Math.ceil(total.value / pageSize))
</script>

<template>
  <div class="statement-book-page">
    <h1>📖 语句本</h1>

    <!-- Toolbar -->
    <div class="toolbar">
      <input
        v-model="search"
        type="text"
        placeholder="搜索语句 (中/英文)..."
        class="search-input"
        @keyup.enter="loadData"
      />
      <select v-model="typeId" class="type-select">
        <option :value="null">全部类型 ({{ total }})</option>
        <option v-for="t in types" :key="t.id" :value="t.id">
          {{ t.name }}
        </option>
      </select>
      <span class="total-label">共 {{ total }} 条</span>
    </div>

    <!-- Table -->
    <div class="table-wrap" v-if="!loading">
      <table class="statement-table" v-if="items.length > 0">
        <thead>
          <tr>
            <th class="col-num">#</th>
            <th class="col-type">类型</th>
            <th class="col-en">英文语句</th>
            <th class="col-zh">中文翻译</th>
            <th class="col-src">来源</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, idx) in items" :key="item.text_en">
            <td class="col-num">{{ (page - 1) * pageSize + idx + 1 }}</td>
            <td class="col-type">
              <span
                class="type-badge"
                :style="{ backgroundColor: getTypeColor(item.type_color) }"
              >
                {{ getTypeLabel(item.type_name) }}
              </span>
            </td>
            <td class="col-en">{{ item.text_en }}</td>
            <td class="col-zh">{{ item.text_zh }}</td>
            <td class="col-src">
              <span
                v-for="pid in item.prompt_ids.slice(0, 3)"
                :key="pid"
                class="prompt-link"
                @click="goToPrompt(pid)"
              >
                #{{ pid }}
              </span>
              <span v-if="item.prompt_ids.length > 3" class="more-link">
                +{{ item.prompt_ids.length - 3 }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="empty" v-else>暂无语句数据</div>
    </div>
    <div class="loading" v-else>加载中...</div>

    <!-- Pagination -->
    <div class="pagination" v-if="total > pageSize">
      <button class="btn btn-sm" :disabled="page <= 1" @click="page--">上一页</button>
      <span class="page-info">{{ page }} / {{ totalPages() }}</span>
      <button class="btn btn-sm" :disabled="page >= totalPages()" @click="page++">下一页</button>
    </div>
  </div>
</template>

<style scoped>
.statement-book-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: var(--space-lg) 0;
}

h1 {
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
  margin-bottom: var(--space-md);
}

.toolbar {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
  margin-bottom: var(--space-md);
}

.search-input {
  flex: 1;
}

.type-select {
  min-width: 160px;
}

.total-label {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  white-space: nowrap;
}

.table-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
}

.statement-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.statement-table thead {
  background: var(--color-bg-secondary);
}

.statement-table th {
  padding: var(--space-sm) var(--space-md);
  text-align: left;
  color: var(--color-text-secondary);
  font-weight: 600;
  border-bottom: 1px solid var(--color-border);
}

.statement-table td {
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--color-border);
  vertical-align: top;
}

.statement-table tbody tr:last-child td {
  border-bottom: none;
}

.statement-table tbody tr:hover {
  background: var(--color-bg-hover);
}

.col-num { width: 40px; color: var(--color-text-muted); }
.col-type { width: 90px; }
.col-en { font-family: var(--font-mono); line-height: 1.5; }
.col-zh { color: var(--color-text-secondary); line-height: 1.5; }
.col-src { width: 100px; }

.type-badge {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 12px;
  color: #000;
  font-weight: 600;
  white-space: nowrap;
}

.prompt-link {
  color: var(--color-accent);
  cursor: pointer;
  margin-right: var(--space-xs);
  font-size: var(--font-size-sm);
}

.prompt-link:hover {
  text-decoration: underline;
}

.more-link {
  color: var(--color-text-muted);
  font-size: 0.75rem;
}

.empty, .loading {
  padding: var(--space-xl);
  text-align: center;
  color: var(--color-text-muted);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-lg);
}

.page-info {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}
</style>
```

- [ ] **Step 2: Verify in browser**

After adding the route (Task 9), navigate to `http://localhost:5173/statements` — should see table with data.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/StatementBookPage.vue
git commit -m "feat: add StatementBookPage with search, type filter, and pagination"
```

---

### Task 6: Frontend — WordCardGrid Component

**Files:**
- Create: `frontend/src/components/WordCardGrid.vue`

**Interfaces:**
- Consumes: `useSettingsStore()` from Task 3, `GlobalWordItem` type from Task 4
- Produces: Reusable card grid that renders word cards in solid/gradient/dots mode

- [ ] **Step 1: Create the component**

```vue
<!-- frontend/src/components/WordCardGrid.vue -->
<script setup lang="ts">
import type { GlobalWordItem } from '@/api/global'
import { useSettingsStore, type WordCardDisplayMode } from '@/stores/settings'

const props = defineProps<{
  words: GlobalWordItem[]
}>()

const settings = useSettingsStore()

/** Compute a CSS background for a word card based on display mode */
function cardBackground(word: GlobalWordItem): string {
  const types = word.types
  if (!types || types.length === 0) {
    return 'var(--color-highlight)'
  }

  const mode: WordCardDisplayMode = settings.wordCardDisplayMode

  if (mode === 'solid' || types.length === 1) {
    return types[0].type_color
  }

  if (mode === 'gradient') {
    const total = types.reduce((s, t) => s + t.count, 0)
    let acc = 0
    const stops = types.map((t) => {
      acc += t.count
      const pct = Math.round((acc / total) * 100)
      return `${t.type_color} ${pct}%`
    })
    return `linear-gradient(135deg, ${stops.join(', ')})`
  }

  // dots mode: use main type color
  return types[0].type_color
}

/** Determine text color — black or white based on background brightness */
function textColor(word: GlobalWordItem): string {
  const types = word.types
  if (!types || types.length === 0) return '#60a5fa'  // default light blue
  const hex = types[0].type_color.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.55 ? '#000000' : '#ffffff'
}

/** Get display mode label for current mode */
const modeLabel = (): string => {
  const m = settings.wordCardDisplayMode
  if (m === 'gradient') return '渐变'
  if (m === 'solid') return '纯色'
  return '色点'
}
</script>

<template>
  <div class="word-card-grid">
    <div v-if="words.length === 0" class="empty">暂无单词数据</div>
    <div
      v-for="word in words"
      :key="word.word_en"
      class="word-card"
      :style="{
        background: cardBackground(word),
        color: textColor(word),
      }"
    >
      <!-- Dots row (dots mode) -->
      <div
        v-if="settings.wordCardDisplayMode === 'dots' && word.types.length > 0"
        class="type-dots"
      >
        <span
          v-for="t in word.types"
          :key="t.type_id"
          class="type-dot"
          :style="{ backgroundColor: t.type_color }"
          :title="`${t.type_name}: ${t.count}次`"
        ></span>
      </div>

      <span class="word-en">{{ word.word_en }}</span>
      <span class="word-zh">{{ word.word_zh }}</span>
      <span class="word-count">{{ word.total_count }}次</span>

      <!-- Type tags row (solid mode) -->
      <div
        v-if="settings.wordCardDisplayMode === 'solid' && word.types.length > 0"
        class="type-tags"
      >
        <span
          v-for="t in word.types"
          :key="t.type_id"
          class="type-tag"
        >
          {{ t.type_name }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.word-card-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
}

.word-card {
  border-radius: 10px;
  padding: var(--space-md) var(--space-lg);
  min-width: 130px;
  flex: 0 0 calc(25% - var(--space-md));
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

.word-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
}

.word-en {
  font-family: var(--font-mono);
  font-size: var(--font-size-base);
  font-weight: 700;
}

.word-zh {
  font-size: var(--font-size-sm);
  opacity: 0.85;
}

.word-count {
  font-size: 0.75rem;
  opacity: 0.65;
}

.type-dots {
  display: flex;
  gap: 3px;
  margin-bottom: 2px;
}

.type-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.2);
}

.type-tags {
  display: flex;
  gap: 3px;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 2px;
}

.type-tag {
  background: rgba(0, 0, 0, 0.2);
  padding: 1px 6px;
  border-radius: 8px;
  font-size: 0.65rem;
}

.empty {
  width: 100%;
  padding: var(--space-xl);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

@media (max-width: 900px) {
  .word-card {
    flex: 0 0 calc(33.333% - var(--space-md));
  }
}

@media (max-width: 600px) {
  .word-card {
    flex: 0 0 calc(50% - var(--space-md));
  }
}
</style>
```

- [ ] **Step 2: Verify in browser**

Will be visible on WordBookPage (Task 7).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/WordCardGrid.vue
git commit -m "feat: add WordCardGrid component with solid/gradient/dots display modes"
```

---

### Task 7: Frontend — WordBookPage

**Files:**
- Create: `frontend/src/views/WordBookPage.vue`

**Interfaces:**
- Consumes: `globalApi.getWords()` from Task 4, `WordCardGrid` from Task 6, `useSettingsStore` from Task 3
- Produces: Full word book page at `/words`

- [ ] **Step 1: Create the page component**

```vue
<!-- frontend/src/views/WordBookPage.vue -->
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { globalApi, type GlobalWordItem, type GlobalPaginatedResponse } from '@/api/global'
import { useSettingsStore, type WordCardDisplayMode } from '@/stores/settings'
import WordCardGrid from '@/components/WordCardGrid.vue'

const settings = useSettingsStore()

const words = ref<GlobalWordItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 12
const search = ref('')
const loading = ref(false)

onMounted(() => loadData())

watch(search, () => { page.value = 1; loadData() })
watch(page, () => loadData())

async function loadData() {
  loading.value = true
  try {
    const res = await globalApi.getWords({
      search: search.value,
      page: page.value,
      page_size: pageSize,
    })
    const data = res.data as GlobalPaginatedResponse<GlobalWordItem>
    words.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function setMode(mode: WordCardDisplayMode) {
  settings.setDisplayMode(mode)
}

const modes: { key: WordCardDisplayMode; label: string }[] = [
  { key: 'gradient', label: '渐变' },
  { key: 'solid', label: '纯色' },
  { key: 'dots', label: '色点' },
]

const totalPages = () => Math.max(1, Math.ceil(total.value / pageSize))
</script>

<template>
  <div class="word-book-page">
    <h1>📝 单词本</h1>

    <!-- Toolbar -->
    <div class="toolbar">
      <input
        v-model="search"
        type="text"
        placeholder="搜索单词 (中/英文)..."
        class="search-input"
        @keyup.enter="loadData"
      />
      <span class="total-label">共 {{ total }} 词</span>

      <!-- Mode switcher -->
      <div class="mode-switcher">
        <button
          v-for="m in modes"
          :key="m.key"
          class="mode-btn"
          :class="{ 'mode-btn--active': settings.wordCardDisplayMode === m.key }"
          @click="setMode(m.key)"
        >
          {{ m.label }}
        </button>
      </div>
    </div>

    <!-- Card Grid -->
    <div class="cards-area" v-if="!loading">
      <WordCardGrid :words="words" />
    </div>
    <div class="loading" v-else>加载中...</div>

    <!-- Pagination -->
    <div class="pagination" v-if="total > pageSize">
      <button class="btn btn-sm" :disabled="page <= 1" @click="page--">上一页</button>
      <span class="page-info">{{ page }} / {{ totalPages() }}</span>
      <button class="btn btn-sm" :disabled="page >= totalPages()" @click="page++">下一页</button>
    </div>
  </div>
</template>

<style scoped>
.word-book-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: var(--space-lg) 0;
}

h1 {
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
  margin-bottom: var(--space-md);
}

.toolbar {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
  margin-bottom: var(--space-lg);
}

.search-input {
  flex: 1;
}

.total-label {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  white-space: nowrap;
}

.mode-switcher {
  display: flex;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.mode-btn {
  padding: var(--space-xs) var(--space-md);
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.mode-btn:not(:last-child) {
  border-right: 1px solid var(--color-border);
}

.mode-btn:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

.mode-btn--active {
  background: var(--color-accent);
  color: #ffffff;
}

.cards-area {
  min-height: 300px;
}

.loading {
  padding: var(--space-xl);
  text-align: center;
  color: var(--color-text-muted);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-lg);
}

.page-info {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}
</style>
```

- [ ] **Step 2: Verify in browser**

After adding the route (Task 8), navigate to `http://localhost:5173/words` — should see card grid with data and mode switcher.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/WordBookPage.vue
git commit -m "feat: add WordBookPage with search, mode switcher, and pagination"
```

---

### Task 8: Frontend — Router & SideNav Updates

**Files:**
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/components/SideNav.vue`

**Interfaces:**
- Consumes: Tasks 5 and 7 (page components)
- Produces: Navigable routes at `/statements` and `/words`

- [ ] **Step 1: Add routes**

Edit `frontend/src/router/index.ts` — add two route entries inside the `routes` array, after the existing `/prompts` redirect:

```typescript
// Insert after the { path: '/', redirect: '/prompts' } entry and before the '/prompts' entry:
    {
      path: '/statements',
      name: 'statements',
      component: () => import('@/views/StatementBookPage.vue'),
    },
    {
      path: '/words',
      name: 'words',
      component: () => import('@/views/WordBookPage.vue'),
    },
```

The complete routes array should look like:

```typescript
  routes: [
    {
      path: '/',
      redirect: '/prompts',
    },
    {
      path: '/statements',
      name: 'statements',
      component: () => import('@/views/StatementBookPage.vue'),
    },
    {
      path: '/words',
      name: 'words',
      component: () => import('@/views/WordBookPage.vue'),
    },
    {
      path: '/prompts',
      name: 'display',
      component: () => import('@/views/DisplayPage.vue'),
    },
    // ... rest unchanged
  ],
```

- [ ] **Step 2: Add SideNav entries**

Edit `frontend/src/components/SideNav.vue` — update the `navItems` array to include the two new entries:

Old:
```typescript
const navItems = [
  { label: '展示', to: '/prompts', icon: '📋' },
  { label: '管理', to: '/manage', icon: '⚙️' },
]
```

New:
```typescript
const navItems = [
  { label: '展示', to: '/prompts', icon: '📋' },
  { label: '语句本', to: '/statements', icon: '📖' },
  { label: '单词本', to: '/words', icon: '📝' },
  { label: '管理', to: '/manage', icon: '⚙️' },
]
```

- [ ] **Step 3: Verify navigation**

Navigate to `http://localhost:5173` — side nav should show 4 items. Click "语句本" and "单词本" to confirm routes work and pages load with data.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/router/index.ts frontend/src/components/SideNav.vue
git commit -m "feat: add /statements and /words routes to router and sidebar navigation"
```

---

### Task 9: End-to-End Verification

**Files:** None (verification only)

- [ ] **Step 1: Verify statement book page**

Navigate to `http://localhost:5173/statements`:
- Table loads with deduplicated statements
- Type column shows colored badges matching StatementType colors
- Search filters by text_en / text_zh
- Type dropdown filters by type
- Pagination works (prev/next, page count)
- Source links are clickable

- [ ] **Step 2: Verify word book page**

Navigate to `http://localhost:5173/words`:
- Card grid loads with deduplicated words
- Cards have type-colored backgrounds
- Mode switcher cycles between 渐变/纯色/色点
- Switching mode persists across page reload (check localStorage `promptweb-settings`)
- Default mode is "渐变" (gradient)
- Search filters by word_en / word_zh
- Pagination works

- [ ] **Step 3: Verify API endpoints**

```bash
# Statements endpoint
curl -s "http://localhost:8000/api/statements/global?page=1&page_size=3" | python -m json.tool
# Expected: items array with text_en, text_zh, type_name, type_color, prompt_ids

# Statements search
curl -s "http://localhost:8000/api/statements/global?search=dragon&page=1" | python -m json.tool
# Expected: only statements containing "dragon"

# Words endpoint
curl -s "http://localhost:8000/api/words/global?page=1&page_size=2" | python -m json.tool
# Expected: items array with word_en, word_zh, total_count, types[], prompt_ids

# Words search
curl -s "http://localhost:8000/api/words/global?search=cinematic" | python -m json.tool
# Expected: only words containing "cinematic"
```

- [ ] **Step 4: Commit any final fixes, then final commit**

If any issues were found and fixed, commit those fixes.

---

## Implementation Order Summary

```
Task 1 (backend: statements_global)  ──┐
Task 2 (backend: words_global)       ──┤  Backend — can run in parallel
Task 3 (frontend: settings store)     ──┤
Task 4 (frontend: global API client)  ──┤  Frontend infra — can run in parallel
                                        │
Task 5 (StatementBookPage)             │  Depends on Task 4
Task 6 (WordCardGrid)                  │  Depends on Task 3, 4
Task 7 (WordBookPage)                  │  Depends on Tasks 3, 4, 6
Task 8 (Router + SideNav)              │  Depends on Tasks 5, 7
Task 9 (E2E verification)              │  Depends on all above
```

Recommended execution: Tasks 1-4 in parallel, then 5 and 6 in parallel, then 7, then 8, then 9.
