<script setup lang="ts">
import { ref, onMounted, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { promptsApi, type PromptDetail as PromptDetailType } from '@/api/prompts'
import PromptLeftPanel from '@/components/PromptLeftPanel.vue'
import PromptRightPanel from '@/components/PromptRightPanel.vue'

const route = useRoute()
const router = useRouter()
const prompt = ref<PromptDetailType | null>(null)
const loading = ref(true)
const highlightedStatementId = ref<number | null>(null)
const highlightedWordId = ref<number | null>(null)

provide('highlightedStatementId', highlightedStatementId)
provide('highlightedWordId', highlightedWordId)

onMounted(async () => {
  const id = Number(route.params.id)
  if (!id) return
  try {
    loading.value = true
    const res = await promptsApi.get(id)
    prompt.value = res.data as PromptDetailType
  } finally {
    loading.value = false
  }
})

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

function goEdit() {
  router.push(`/prompts/${route.params.id}/edit`)
}

async function deletePrompt() {
  if (!confirm('确认删除这条 Prompt？')) return
  await promptsApi.delete(Number(route.params.id))
  router.push('/prompts')
}
</script>

<template>
  <div class="prompt-detail" v-if="!loading && prompt">
    <div class="detail-header">
      <button class="btn btn-sm" @click="router.push('/prompts')">← 返回列表</button>
      <h2>{{ prompt.title || '未命名 Prompt' }}</h2>
      <div class="detail-actions">
        <button class="btn btn-sm" @click="goEdit">编辑</button>
        <button class="btn btn-sm btn-danger" @click="deletePrompt">删除</button>
      </div>
    </div>
    <div class="detail-body" @click.self="clearHighlights">
      <PromptLeftPanel
        :prompt="prompt"
        @statement-click="onStatementClick"
        @word-click="onWordClick"
      />
      <PromptRightPanel :prompt="prompt" />
    </div>
  </div>
  <div class="loading" v-else>加载中...</div>
</template>

<style scoped>
.prompt-detail {
  max-width: 1400px;
  margin: 0 auto;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.detail-header h2 {
  flex: 1;
  font-size: var(--font-size-lg);
}

.detail-actions {
  display: flex;
  gap: var(--space-sm);
}

.detail-body {
  display: grid;
  grid-template-columns: 1fr 420px;
  gap: var(--space-lg);
  min-height: calc(100vh - 140px);
}

.loading {
  text-align: center;
  padding: var(--space-xl);
  color: var(--color-text-muted);
}
</style>
