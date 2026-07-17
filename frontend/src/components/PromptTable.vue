<script setup lang="ts">
import type { PromptListItem } from '@/api/prompts'
import PromptRow from './PromptRow.vue'

defineProps<{
  items: PromptListItem[]
  loading: boolean
}>()

const emit = defineEmits<{
  'row-click': [id: number]
}>()
</script>

<template>
  <div class="prompt-table" v-if="!loading">
    <div class="table-header">
      <span class="col-thumb"></span>
      <span class="col-en">英文 Prompt</span>
      <span class="col-zh">中文翻译</span>
    </div>
    <PromptRow
      v-for="item in items"
      :key="item.id"
      :item="item"
      @click="emit('row-click', item.id)"
    />
    <div class="empty" v-if="items.length === 0">
      暂无数据
    </div>
  </div>
  <div class="loading" v-else>
    加载中...
  </div>
</template>

<style scoped>
.prompt-table {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 80px 1fr 1fr;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: 600;
}

.col-thumb {
  text-align: center;
}

.empty, .loading {
  padding: var(--space-xl);
  text-align: center;
  color: var(--color-text-muted);
}
</style>
