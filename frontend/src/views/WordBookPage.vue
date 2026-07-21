<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import PageNav from '@/components/PageNav.vue'
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
    <PageNav class="pagination" v-model="page" :total="total" :page-size="pageSize" />
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


</style>
