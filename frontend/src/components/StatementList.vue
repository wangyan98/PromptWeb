<script setup lang="ts">
import type { StatementResponse } from '@/api/prompts'
import StatementItem from './StatementItem.vue'

defineProps<{
  statements: StatementResponse[]
}>()

const emit = defineEmits<{
  'statement-click': [id: number]
  'word-click': [id: number]
}>()
</script>

<template>
  <div class="statement-list">
    <div class="section-label">拆分语句</div>
    <StatementItem
      v-for="(stmt, idx) in statements"
      :key="stmt.id"
      :statement="stmt"
      :index="idx"
      @statement-click="emit('statement-click', $event)"
      @word-click="emit('word-click', $event)"
    />
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
</style>
