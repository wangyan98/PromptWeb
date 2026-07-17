<script setup lang="ts">
import type { PromptListItem } from '@/api/prompts'

defineProps<{
  item: PromptListItem
}>()

defineEmits<{
  click: []
}>()

function truncate(text: string, max: number): string {
  return text.length > max ? text.slice(0, max) + '...' : text
}
</script>

<template>
  <div class="prompt-row" @click="$emit('click')">
    <div class="col-thumb">
      <img
        v-if="item.thumbnail_url"
        :src="item.thumbnail_url"
        class="thumbnail"
        alt="thumb"
      />
      <div v-else class="thumbnail-placeholder">🖼️</div>
    </div>
    <div class="col-en">{{ truncate(item.text_en_full, 120) }}</div>
    <div class="col-zh">{{ truncate(item.text_zh_full, 80) }}</div>
  </div>
</template>

<style scoped>
.prompt-row {
  display: grid;
  grid-template-columns: 80px 1fr 1fr;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  transition: background var(--transition-fast);
  align-items: center;
  min-height: 60px;
}

.prompt-row:last-child {
  border-bottom: none;
}

.prompt-row:hover {
  background: var(--color-bg-hover);
}

.col-thumb {
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumbnail {
  width: 56px;
  height: 56px;
  object-fit: cover;
  border-radius: 4px;
}

.thumbnail-placeholder {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-secondary);
  border-radius: 4px;
  font-size: 1.2rem;
}

.col-en {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  line-height: 1.5;
  word-break: break-word;
  font-family: var(--font-mono);
}

.col-zh {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.5;
  word-break: break-word;
}
</style>
