<script setup lang="ts">
import type { PromptImageResponse } from '@/api/prompts'
import ImageCard from './ImageCard.vue'

defineProps<{
  images: PromptImageResponse[]
  readonly?: boolean
}>()

const emit = defineEmits<{
  upload: []
  'add-url': []
  delete: [id: number]
}>()
</script>

<template>
  <div class="image-gallery">
    <div class="section-label">生成图片 ({{ images.length }})</div>
    <div class="image-grid">
      <ImageCard
        v-for="img in images"
        :key="img.id"
        :image="img"
        :readonly="readonly"
        @delete="emit('delete', img.id)"
      />
    </div>
    <div class="image-actions" v-if="!readonly">
      <button class="btn btn-sm" @click="emit('upload')">📤 上传图片</button>
      <button class="btn btn-sm" @click="emit('add-url')">🔗 添加链接</button>
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

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.image-actions {
  display: flex;
  gap: var(--space-sm);
}
</style>
