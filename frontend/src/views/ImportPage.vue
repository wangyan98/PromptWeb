<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'

const router = useRouter()
const file = ref<File | null>(null)
const preview = ref<Record<string, string[][]> | null>(null)
const loading = ref(false)
const importing = ref(false)

async function analyze() {
  if (!file.value) return
  loading.value = true
  try {
    const form = new FormData()
    form.append('file', file.value)
    const res = await apiClient.post('/import/excel', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    preview.value = res.data.sheets
  } finally {
    loading.value = false
  }
}

function selectSheet(sheetName: string) {
  // Parse the sheet and try to auto-map columns
  const rows = preview.value?.[sheetName] || []
  console.log('Selected sheet:', sheetName, rows.length, 'rows')
}

async function confirmImport(sheetName: string) {
  const rows = preview.value?.[sheetName] || []
  if (rows.length < 2) return

  const headers = rows[0]
  const dataRows = rows.slice(1)

  // Simple heuristic: find columns by keyword
  const findCol = (keywords: string[]) => {
    return headers.findIndex((h) => keywords.some((kw) => h.toLowerCase().includes(kw.toLowerCase())))
  }

  const enIdx = findCol(['英文', 'prompt', 'english', 'en'])
  const zhIdx = findCol(['中文', 'chinese', 'zh', '场景主题', '场景'])
  const catIdx = findCol(['类别', 'category', '分类'])

  const items = dataRows.map((row) => ({
    title: row[zhIdx] || '',
    text_en_full: row[enIdx] || '',
    text_zh_full: row[zhIdx] || '',
    category: catIdx >= 0 ? row[catIdx] : '',
    source_file: file.value?.name || '',
  }))

  importing.value = true
  try {
    await apiClient.post('/import/confirm', items)
    alert(`成功导入 ${items.length} 条 Prompt`)
    router.push('/prompts')
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <div class="import-page">
    <h1>导入 Excel 数据</h1>
    <div class="upload-zone">
      <input
        type="file"
        accept=".xlsx,.xls"
        @change="(e) => { file = (e.target as HTMLInputElement).files?.[0] || null; preview = null }"
      />
      <button class="btn btn-primary" :disabled="!file || loading" @click="analyze">
        {{ loading ? '解析中...' : '解析文件' }}
      </button>
    </div>

    <div v-if="preview" class="preview-section">
      <h2>预览结果</h2>
      <div v-for="(rows, sheetName) in preview" :key="sheetName" class="sheet-preview">
        <div class="sheet-header">
          <h3>工作表: {{ sheetName }} ({{ rows.length }} 行)</h3>
          <button
            class="btn btn-primary"
            :disabled="importing"
            @click="confirmImport(sheetName)"
          >
            {{ importing ? '导入中...' : '确认导入此表' }}
          </button>
        </div>
        <div class="sheet-scroll">
          <table>
            <thead>
              <tr>
                <th v-for="(cell, ci) in rows[0]" :key="ci">{{ cell }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, ri) in rows.slice(1, 6)" :key="ri">
                <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
              </tr>
            </tbody>
          </table>
          <p v-if="rows.length > 6" class="more-rows">... 还有 {{ rows.length - 6 }} 行</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.import-page {
  max-width: 900px;
  margin: 0 auto;
}

h1 {
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-lg);
}

.upload-zone {
  display: flex;
  gap: var(--space-md);
  align-items: center;
  margin-bottom: var(--space-xl);
}

.preview-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.sheet-preview {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
}

.sheet-header h3 {
  font-size: var(--font-size-base);
}

.sheet-scroll {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

th, td {
  padding: var(--space-xs) var(--space-sm);
  border: 1px solid var(--color-border);
  text-align: left;
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

th {
  background: var(--color-bg-tertiary);
  font-weight: 600;
}

.more-rows {
  padding: var(--space-sm);
  color: var(--color-text-muted);
  text-align: center;
}
</style>
