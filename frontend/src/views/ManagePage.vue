<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { promptsApi, type PromptListItem, type PaginatedResponse } from '@/api/prompts'
import SearchBar from '@/components/SearchBar.vue'
import PageNav from '@/components/PageNav.vue'
import StatementTypeManager from './StatementTypeManager.vue'
import ImportPage from './ImportPage.vue'

const router = useRouter()

type TabKey = 'prompts' | 'types' | 'import'

const activeTab = ref<TabKey>('prompts')

const tabs: { key: TabKey; label: string }[] = [
  { key: 'prompts', label: 'Prompt 管理' },
  { key: 'types', label: '语句类型' },
  { key: 'import', label: '导入数据' },
]

// Prompt management state
const items = ref<PromptListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const search = ref('')
const category = ref('')
const categories = ref<string[]>([])
const loading = ref(false)

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
})

watch([search, category], () => {
  page.value = 1
  loadList()
})

watch(page, () => loadList())

function goNew() {
  router.push('/manage/prompts/new')
}

function goEdit(id: number) {
  router.push(`/manage/prompts/${id}/edit`)
}

async function deletePrompt(id: number) {
  if (!confirm('确认删除这条 Prompt？')) return
  await promptsApi.delete(id)
  await loadList()
}

function truncate(text: string, max: number): string {
  if (!text) return ''
  return text.length > max ? text.slice(0, max) + '...' : text
}
</script>

<template>
  <div class="manage-page">
    <h1>管理</h1>

    <!-- Tabs -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab: Prompt Management -->
    <div class="tab-content" v-show="activeTab === 'prompts'">
      <div class="tab-header">
        <SearchBar v-model:search="search" v-model:category="category" :categories="categories" />
        <button class="btn btn-primary" @click="goNew">+ 新增 Prompt</button>
      </div>

      <div class="manage-table" v-if="!loading">
        <div class="table-header">
          <span class="col-thumb"></span>
          <span class="col-en">英文 Prompt</span>
          <span class="col-zh">中文 Prompt</span>
          <span class="col-actions">操作</span>
        </div>
        <div
          v-for="item in items"
          :key="item.id"
          class="table-row"
        >
          <div class="col-thumb">
            <img v-if="item.thumbnail_url" :src="item.thumbnail_url" class="thumb-img" alt="" />
            <div v-else class="thumb-placeholder">🖼️</div>
          </div>
          <div class="col-en">{{ truncate(item.text_en_full, 100) }}</div>
          <div class="col-zh">{{ truncate(item.text_zh_full, 60) }}</div>
          <div class="col-actions">
            <button class="btn btn-sm" @click="goEdit(item.id)">编辑</button>
            <button class="btn btn-sm btn-danger" @click="deletePrompt(item.id)">删除</button>
          </div>
        </div>
        <div class="empty" v-if="items.length === 0">暂无数据</div>
      </div>
      <div class="loading" v-else>加载中...</div>

      <!-- Pagination -->
      <PageNav class="pagination" v-model="page" :total="total" :page-size="pageSize" />
    </div>

    <!-- Tab: Statement Types -->
    <div class="tab-content" v-show="activeTab === 'types'">
      <StatementTypeManager />
    </div>

    <!-- Tab: Import -->
    <div class="tab-content" v-show="activeTab === 'import'">
      <ImportPage />
    </div>
  </div>
</template>

<style scoped>
.manage-page {
  max-width: 1100px;
  margin: 0 auto;
}

h1 {
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
  margin-bottom: var(--space-md);
}

/* Tabs */
.tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-lg);
}

.tab-btn {
  padding: var(--space-sm) var(--space-lg);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  transition: all var(--transition-fast);
  cursor: pointer;
}

.tab-btn:hover {
  color: var(--color-text-primary);
}

.tab-btn--active {
  color: var(--color-accent);
  border-bottom-color: var(--color-accent);
}

.tab-content {
  min-height: 400px;
}

/* Prompt Management */
.tab-header {
  display: flex;
  gap: var(--space-md);
  align-items: flex-start;
  margin-bottom: var(--space-md);
}

.tab-header :deep(.search-bar) {
  flex: 1;
  margin-bottom: 0;
}

.manage-table {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 56px 1fr 1fr 120px;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: 600;
}

.table-row {
  display: grid;
  grid-template-columns: 56px 1fr 1fr 120px;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--color-border);
  align-items: center;
  min-height: 56px;
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: var(--color-bg-hover);
}

.col-thumb {
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumb-img {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: var(--border-radius);
}

.thumb-placeholder {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-tertiary);
  border-radius: var(--border-radius);
  font-size: 0.9rem;
}

.col-en {
  font-size: var(--font-size-sm);
  font-family: var(--font-mono);
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.col-zh {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.col-actions {
  display: flex;
  gap: var(--space-xs);
}

.empty, .loading {
  padding: var(--space-xl);
  text-align: center;
  color: var(--color-text-muted);
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-lg);
}


</style>
