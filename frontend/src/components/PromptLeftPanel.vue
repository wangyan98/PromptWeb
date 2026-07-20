<script setup lang="ts">
import { computed, inject } from 'vue'
import type { PromptDetail } from '@/api/prompts'
import StatementList from './StatementList.vue'

const props = defineProps<{
  prompt: PromptDetail
}>()

const emit = defineEmits<{
  'statement-click': [id: number]
  'word-click': [id: number]
}>()

const highlightedWordId = inject<{ value: number | null }>('highlightedWordId')!

const highlightedWord = computed(() => {
  const id = highlightedWordId?.value
  if (!id) return null
  return props.prompt.words.find(w => w.id === id) || null
})
</script>

<template>
  <div class="left-panel">
    <div class="full-text-section">
      <div class="section-label">英文 Prompt</div>
      <p class="full-text-en">
        <template v-if="highlightedWord">
          <span>{{ prompt.text_en_full.slice(0, highlightedWord.position_start ?? 0) }}</span>
          <span class="word-highlight-inline">{{ highlightedWord.word_en }}</span>
          <span>{{ prompt.text_en_full.slice((highlightedWord.position_end ?? 0)) }}</span>
        </template>
        <template v-else>{{ prompt.text_en_full }}</template>
      </p>
    </div>
    <div class="full-text-section" v-if="prompt.text_zh_full">
      <div class="section-label">中文 Prompt</div>
      <p class="full-text-zh">{{ prompt.text_zh_full }}</p>
    </div>
    <div class="divider"></div>
    <StatementList
      :statements="prompt.statements"
      @statement-click="emit('statement-click', $event)"
      @word-click="emit('word-click', $event)"
    />
  </div>
</template>

<style scoped>
.left-panel {
  overflow-y: auto;
}

.full-text-section {
  margin-bottom: var(--space-md);
}

.section-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin-bottom: var(--space-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.full-text-en {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  line-height: 1.8;
  color: var(--color-text-primary);
  background: var(--color-bg-card);
  padding: var(--space-md);
  border-radius: var(--border-radius);
}

.full-text-zh {
  font-size: var(--font-size-base);
  line-height: 1.8;
  color: var(--color-text-secondary);
  background: var(--color-bg-card);
  padding: var(--space-md);
  border-radius: var(--border-radius);
}

.divider {
  height: 1px;
  background: var(--color-border);
  margin: var(--space-lg) 0;
}

.word-highlight-inline {
  background: var(--color-highlight);
  color: var(--color-highlight-text);
  padding: 1px 3px;
  border-radius: 3px;
  font-weight: 600;
}
</style>
