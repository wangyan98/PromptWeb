<script setup lang="ts">
import { computed, inject, onMounted } from 'vue'
import type { StatementResponse, PromptWordResponse } from '@/api/prompts'
import { useStatementTypeStore } from '@/stores/statementTypes'

const props = defineProps<{
  statement: StatementResponse
  index: number
}>()

const emit = defineEmits<{
  'statement-click': [id: number]
  'word-click': [id: number]
}>()

const highlightedStatementId = inject<{ value: number | null }>('highlightedStatementId')!
const highlightedWordId = inject<{ value: number | null }>('highlightedWordId')!

const typeStore = useStatementTypeStore()

onMounted(() => {
  typeStore.load()
})

const isHighlighted = computed(() => highlightedStatementId?.value === props.statement.id)

const typeInfo = computed(() => typeStore.getType(props.statement.type_id))
const typeName = computed(() => typeInfo.value?.name || '未分类')
const typeColor = computed(() => typeInfo.value?.color || '#4fc3f7')

function onWordClick(wordId: number, event: Event) {
  event.stopPropagation()
  emit('word-click', wordId)
}

function getWordHighlightClass(wordId: number) {
  return highlightedWordId?.value === wordId ? 'word-highlighted' : ''
}
</script>

<template>
  <div
    class="statement-item"
    :class="{ 'statement-highlighted': isHighlighted }"
    @click="emit('statement-click', statement.id)"
  >
    <div class="stmt-header">
      <span class="stmt-index">#{{ index + 1 }}</span>
      <span class="stmt-type-badge" :style="{ backgroundColor: typeColor || '#4fc3f7' }">
        {{ typeName || '未分类' }}
      </span>
    </div>
    <p class="stmt-en">
      <span
        v-for="word in statement.words"
        :key="word.id"
        :class="['clickable-word', getWordHighlightClass(word.id)]"
        @click="onWordClick(word.id, $event)"
      >{{ word.word_en }} </span>
      <span v-if="statement.words.length === 0">{{ statement.text_en }}</span>
    </p>
    <p class="stmt-zh">{{ statement.text_zh }}</p>
  </div>
</template>

<style scoped>
.statement-item {
  padding: var(--space-md);
  margin-bottom: var(--space-sm);
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.statement-item:hover {
  border-color: var(--color-accent);
}

.statement-highlighted {
  border-color: var(--color-highlight);
  background: rgba(255, 224, 102, 0.08);
}

.stmt-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-xs);
}

.stmt-index {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.stmt-type-badge {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 12px;
  color: #1a1a2e;
  font-weight: 600;
}

.stmt-en {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  line-height: 1.7;
  color: var(--color-text-primary);
  margin-bottom: var(--space-xs);
}

.clickable-word {
  cursor: pointer;
  border-radius: 2px;
  transition: all var(--transition-fast);
}

.clickable-word:hover {
  background: rgba(255, 224, 102, 0.3);
}

.word-highlighted {
  background: var(--color-highlight);
  color: var(--color-highlight-text);
  padding: 1px 3px;
  border-radius: 3px;
  font-weight: 600;
}

.stmt-zh {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
}
</style>
