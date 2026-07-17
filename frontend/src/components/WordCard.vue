<script setup lang="ts">
import type { PromptWordResponse } from '@/api/prompts'

defineProps<{
  word: PromptWordResponse
}>()
</script>

<template>
  <div class="word-card">
    <span class="word-en">{{ word.word_en }}</span>
    <span class="word-zh">{{ word.word_zh }}</span>
  </div>
</template>

<style scoped>
.word-card {
  background: var(--color-highlight);
  color: var(--color-highlight-text);
  border-radius: var(--border-radius);
  padding: var(--space-sm) var(--space-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-width: 80px;
}

.word-en {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.word-zh {
  font-size: 0.75rem;
  opacity: 0.8;
}
</style>
