<script setup lang="ts">
import { ref, onMounted, watch, provide } from 'vue'
import { useRoute } from 'vue-router'
import { ClipboardList, ImageIcon } from 'lucide-vue-next'
import { promptsApi, type PromptListItem, type PromptDetail, type PaginatedResponse } from '@/api/prompts'
import SearchBar from '@/components/SearchBar.vue'
import PageNav from '@/components/PageNav.vue'
import PromptLeftPanel from '@/components/PromptLeftPanel.vue'
import PromptRightPanel from '@/components/PromptRightPanel.vue'

// List state
const route = useRoute()

const items = ref<PromptListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const search = ref('')
const category = ref('')
const categories = ref<string[]>([])
const loading = ref(false)

// Detail state
const selectedId = ref<number | null>(null)
const detail = ref<PromptDetail | null>(null)
const detailLoading = ref(false)

// Highlight state
const highlightedStatementId = ref<number | null>(null)
const highlightedWordId = ref<number | null>(null)

provide('highlightedStatementId', highlightedStatementId)
provide('highlightedWordId', highlightedWordId)

async function loadList() {
  loading.value = true
  try {
    const res = await promptsApi.list({
      page: page.value,
      page_size: pageSize,
      search: search.value,
      category: category.value,
    })
    const data = res.data as PaginatedResponse<PromptListItem>
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  const res = await promptsApi.getCategories()
  categories.value = res.data as string[]
}

onMounted(() => {
  loadCategories()
  loadList()

  // Auto-select prompt from query param (used by statement book jump)
  const selectId = Number(route.query.select)
  if (selectId && !isNaN(selectId)) {
    selectPrompt(selectId)
  }
})

watch([search, category], () => {
  page.value = 1
  loadList()
})

watch(page, () => loadList())

async function selectPrompt(id: number) {
  if (selectedId.value === id) return
  selectedId.value = id
  highlightedStatementId.value = null
  highlightedWordId.value = null
  detailLoading.value = true
  try {
    const res = await promptsApi.get(id)
    detail.value = res.data as PromptDetail
  } finally {
    detailLoading.value = false
  }
}

function onStatementClick(statementId: number) {
  if (highlightedStatementId.value === statementId) {
    highlightedStatementId.value = null
    highlightedWordId.value = null
  } else {
    highlightedStatementId.value = statementId
    highlightedWordId.value = null
  }
}

function onWordClick(wordId: number) {
  highlightedWordId.value = highlightedWordId.value === wordId ? null : wordId
}

function clearHighlights() {
  highlightedStatementId.value = null
  highlightedWordId.value = null
}

function truncate(text: string, max: number): string {
  if (!text) return ''
  return text.length > max ? text.slice(0, max) + '...' : text
}
</script>

<template>
  <div class="display-page">
    <div class="display-header">
      <h1>Prompt 展示</h1>
      <SearchBar v-model:search="search" v-model:category="category" :categories="categories" />
    </div>

    <div class="display-body">
      <!-- Left: Prompt List -->
      <div class="list-panel">
        <div class="list-inner" v-if="!loading">
          <div
            v-for="item in items"
            :key="item.id"
            class="list-row"
            :class="{ 'list-row--active': selectedId === item.id }"
            @click="selectPrompt(item.id)"
          >
            <div class="list-row-thumb">
              <img v-if="item.thumbnail_url" :src="item.thumbnail_url" class="thumb-img" alt="" />
              <div v-else class="thumb-placeholder"><ImageIcon :size="16" :stroke-width="1.6" /></div>
            </div>
            <div class="list-row-content">
              <div class="list-row-en">{{ truncate(item.text_en_full, 100) }}</div>
              <div class="list-row-zh" v-if="item.text_zh_full">{{ truncate(item.text_zh_full, 60) }}</div>
            </div>
          </div>
          <div class="empty" v-if="items.length === 0">暂无数据</div>
        </div>
        <div class="loading" v-else>加载中...</div>

        <!-- Pagination -->
        <PageNav class="list-pagination" v-model="page" :total="total" :page-size="pageSize" />
      </div>

      <!-- Right: Detail Panel -->
      <div class="detail-panel" @click.self="clearHighlights">
        <template v-if="detailLoading">
          <div class="detail-placeholder">加载中...</div>
        </template>
        <template v-else-if="detail">
          <div class="detail-content">
            <PromptLeftPanel
              :prompt="detail"
              @statement-click="onStatementClick"
              @word-click="onWordClick"
            />
            <PromptRightPanel
              :prompt="detail"
              :prompt-id="detail.id"
              :readonly="true"
            />
          </div>
        </template>
        <template v-else>
          <div class="detail-placeholder">
            <div class="placeholder-icon"><ClipboardList :size="40" :stroke-width="1.4" /></div>
            <p>选择一个 Prompt 查看详情</p>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.display-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.display-header {
  flex-shrink: 0;
  margin-bottom: var(--space-md);
}

.display-header h1 {
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
  margin-bottom: var(--space-sm);
}

.display-body {
  flex: 1;
  display: flex;
  gap: 0;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-lg);
}

/* Left List Panel */
.list-panel {
  width: 380px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
}

.list-inner {
  flex: 1;
  overflow-y: auto;
}

.list-row {
  display: flex;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  transition: background var(--transition-fast);
  align-items: flex-start;
}

.list-row:last-child {
  border-bottom: none;
}

.list-row:hover {
  background: var(--color-bg-hover);
}

.list-row--active {
  background: rgba(59, 130, 246, 0.1);
  border-left: 2px solid var(--color-accent);
}

.list-row-thumb {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  margin-top: 2px;
}

.thumb-img {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: var(--border-radius);
}

.thumb-placeholder {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-tertiary);
  border-radius: var(--border-radius);
  font-size: 1rem;
}

.list-row-content {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.list-row-en {
  font-size: 0.75rem;
  font-family: var(--font-mono);
  color: var(--color-text-primary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}

.list-row-zh {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
  margin-top: 2px;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.empty, .loading {
  padding: var(--space-xl);
  text-align: center;
  color: var(--color-text-muted);
}

.list-pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
}

/* Right Detail Panel */
.detail-panel {
  flex: 1;
  overflow-y: auto;
  background: var(--color-bg-primary);
}

.detail-content {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: var(--space-lg);
  padding: var(--space-lg);
  min-height: 100%;
}

.detail-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-text-muted);
  gap: var(--space-md);
}

.placeholder-icon {
  font-size: 3rem;
  opacity: 0.3;
}

.detail-placeholder p {
  font-size: var(--font-size-base);
}
</style>
