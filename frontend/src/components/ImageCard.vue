<script setup lang="ts">
import { ref } from 'vue'
import type { PromptImageResponse } from '@/api/prompts'

defineProps<{
  image: PromptImageResponse
  readonly?: boolean
}>()

defineEmits<{
  delete: []
}>()

const enlarged = ref(false)
</script>

<template>
  <div class="image-card" @click="enlarged = !enlarged">
    <img :src="image.url" alt="prompt image" class="gallery-img" />
    <button v-if="!readonly" class="delete-btn" @click.stop="$emit('delete')" title="删除">×</button>
    <div class="enlarge-overlay" v-if="enlarged" @click="enlarged = false">
      <img :src="image.url" class="enlarged-img" />
    </div>
  </div>
</template>

<style scoped>
.image-card {
  position: relative;
  border-radius: var(--border-radius);
  overflow: hidden;
  cursor: pointer;
  aspect-ratio: 1;
}

.gallery-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--transition-fast);
}

.image-card:hover .gallery-img {
  transform: scale(1.05);
}

.delete-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.image-card:hover .delete-btn {
  opacity: 1;
}

.enlarge-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  cursor: zoom-out;
}

.enlarged-img {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
  border-radius: var(--border-radius-lg);
}
</style>
