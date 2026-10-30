<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import PageNav from '@/components/PageNav.vue'
import { BookOpen } from 'lucide-vue-next'
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
  router.push({ path: '/prompts', query: { select: promptId } })
}

function getTypeLabel(typeName: string): string {
  return typeName || '未分类'
}

function getTypeColor(typeColor: string): string {
  return typeColor || '#3b82f6'
}


</script>

<template>
  <div class="statement-book-page">
    <h1 class="page-title"><BookOpen :size="22" :stroke-width="1.8" /> 语句本</h1>

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
    <PageNav class="pagination" v-model="page" :total="total" :page-size="pageSize" />
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
  display: flex;
  align-items: center;
  gap: 8px;
}

h1 :deep(svg) {
  color: var(--color-accent);
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


</style>
