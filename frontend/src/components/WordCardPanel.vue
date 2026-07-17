<script setup lang="ts">
import { computed, inject } from 'vue'
import type { PromptDetail } from '@/api/prompts'
import WordCard from './WordCard.vue'

const props = defineProps<{
  prompt: PromptDetail
}>()

const highlightedWordId = inject<{ value: number | null }>('highlightedWordId')!

// Get all unique words from all statements
const allWords = computed(() => {
  return props.prompt.statements.flatMap((s) => s.words)
})

const activeWord = computed(() => {
  const id = highlightedWordId?.value
  if (!id) return null
  return allWords.value.find((w) => w.id === id) || null
})
</script>

<template>
  <div class="word-card-panel">
    <div class="section-label">高亮单词卡片区</div>
    <div class="word-cards" v-if="activeWord">
      <WordCard :word="activeWord" />
      <!-- Show all words from the same prompt -->
      <WordCard
        v-for="w in allWords"
        :key="w.id"
        :word="w"
        :class="{ dimmed: activeWord && w.id !== activeWord.id }"
      />
    </div>
    <div class="word-cards" v-else-if="allWords.length > 0">
      <WordCard
        v-for="w in allWords"
        :key="w.id"
        :word="w"
      />
    </div>
    <div class="empty-words" v-else>
      暂无提取的单词。请使用 AI 拆分功能提取难词。
    </div>
  </div>
</template>

<style scoped>
.section-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin-bottom: var(--space-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.word-cards {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.dimmed {
  opacity: 0.4;
}

.empty-words {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  padding: var(--space-md);
  text-align: center;
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
}
</style>
