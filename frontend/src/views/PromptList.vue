<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { promptsApi, type PromptListItem, type PaginatedResponse } from '@/api/prompts'
import SearchBar from '@/components/SearchBar.vue'
import PromptTable from '@/components/PromptTable.vue'

const router = useRouter()

const items = ref<PromptListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const search = ref('')
const category = ref('')
const categories = ref<string[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await promptsApi.list({ page: page.value, page_size: pageSize, search: search.value, category: category.value })
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
  load()
})

watch([search, category], () => {
  page.value = 1
  load()
})

watch(page, () => load())

function goDetail(id: number) {
  router.push(`/prompts/${id}`)
}

function goNew() {
  router.push('/prompts/new')
}

function goImport() {
  router.push('/import')
}
</script>

<template>
  <div class="prompt-list-page">
    <div class="page-header">
      <h1>Prompt 列表</h1>
      <div class="header-actions">
        <button class="btn btn-primary" @click="goNew">+ 新增 Prompt</button>
        <button class="btn btn-secondary" @click="goImport">📥 导入 Excel</button>
      </div>
    </div>

    <SearchBar v-model:search="search" v-model:category="category" :categories="categories" />

    <PromptTable
      :items="items"
      :loading="loading"
      @row-click="goDetail"
    />

    <div class="pagination" v-if="total > pageSize">
      <button
        class="btn btn-sm"
        :disabled="page <= 1"
        @click="page--"
      >上一页</button>
      <span class="page-info">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button
        class="btn btn-sm"
        :disabled="page >= Math.ceil(total / pageSize)"
        @click="page++"
      >下一页</button>
    </div>
  </div>
</template>

<style scoped>
.prompt-list-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.page-header h1 {
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}

.header-actions {
  display: flex;
  gap: var(--space-sm);
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

/* Global button styles */
.btn {
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--border-radius);
  border: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  transition: all var(--transition-fast);
}

.btn:hover {
  background: var(--color-bg-hover);
}

.btn-primary {
  background: var(--color-accent);
  color: #1a1a2e;
  border-color: var(--color-accent);
  font-weight: 600;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.btn-sm {
  padding: var(--space-xs) var(--space-sm);
  font-size: 0.8rem;
}

.btn-danger {
  border-color: var(--color-danger);
  color: var(--color-danger);
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
