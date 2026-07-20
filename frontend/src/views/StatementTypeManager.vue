<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { statementTypesApi, type StatementTypeItem } from '@/api/statement-types'

const types = ref<StatementTypeItem[]>([])
const newName = ref('')
const newColor = ref('#3b82f6')

onMounted(async () => {
  await load()
})

async function load() {
  const res = await statementTypesApi.list()
  types.value = res.data as StatementTypeItem[]
}

async function add() {
  if (!newName.value.trim()) return
  await statementTypesApi.create({ name: newName.value.trim(), color: newColor.value, sort_order: types.value.length + 1 })
  newName.value = ''
  newColor.value = '#3b82f6'
  await load()
}

async function remove(id: number) {
  await statementTypesApi.delete(id)
  await load()
}

async function updateColor(type: StatementTypeItem) {
  const color = prompt('新颜色 (HEX):', type.color)
  if (color) {
    await statementTypesApi.update(type.id, { color })
    await load()
  }
}
</script>

<template>
  <div class="type-manager">
    <div class="add-row">
      <input v-model="newName" type="text" placeholder="类型名称" @keyup.enter="add" />
      <input v-model="newColor" type="color" />
      <button class="btn btn-primary" @click="add">添加</button>
    </div>
    <div class="type-list">
      <div v-for="t in types" :key="t.id" class="type-row">
        <span class="color-dot" :style="{ background: t.color }"></span>
        <span class="type-name">{{ t.name }}</span>
        <code class="type-color">{{ t.color }}</code>
        <button class="btn btn-sm" @click="updateColor(t)">改色</button>
        <button class="btn btn-sm btn-danger" @click="remove(t.id)">删除</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.type-manager {
  max-width: 600px;
  margin: 0 auto;
}

.add-row {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.add-row input[type="text"] {
  flex: 1;
}

.add-row input[type="color"] {
  width: 44px;
  height: 38px;
  padding: 2px;
}

.type-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.type-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
}

.color-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  flex-shrink: 0;
}

.type-name {
  flex: 1;
  font-weight: 600;
}

.type-color {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}
</style>
