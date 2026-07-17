<script setup lang="ts">
defineProps<{
  search: string
  category: string
  categories: string[]
}>()

const emit = defineEmits<{
  'update:search': [value: string]
  'update:category': [value: string]
}>()
</script>

<template>
  <div class="search-bar">
    <input
      type="text"
      class="search-input"
      placeholder="搜索 Prompt..."
      :value="search"
      @input="emit('update:search', ($event.target as HTMLInputElement).value)"
    />
    <select
      class="category-select"
      :value="category"
      @change="emit('update:category', ($event.target as HTMLSelectElement).value)"
    >
      <option value="">全部分类</option>
      <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
    </select>
  </div>
</template>

<style scoped>
.search-bar {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.search-input {
  flex: 1;
  padding: var(--space-sm) var(--space-md);
  font-size: var(--font-size-base);
}

.category-select {
  min-width: 160px;
}
</style>
