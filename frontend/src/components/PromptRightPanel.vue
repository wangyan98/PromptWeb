<script setup lang="ts">
import { ref } from 'vue'
import type { PromptDetail, PromptImageResponse } from '@/api/prompts'
import { promptsApi } from '@/api/prompts'
import ImageGallery from './ImageGallery.vue'
import WordCardPanel from './WordCardPanel.vue'

const props = defineProps<{
  prompt: PromptDetail
  promptId: number
  readonly?: boolean
}>()

const images = ref<PromptImageResponse[]>(props.prompt.images || [])

const fileInput = ref<HTMLInputElement | null>(null)

async function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    await promptsApi.uploadImage(props.promptId, file)
    const promptRes = await promptsApi.get(props.promptId)
    images.value = (promptRes.data as PromptDetail).images || []
  } catch (e) {
    console.error('Upload failed:', e)
  }
}

async function addUrl() {
  const url = prompt('输入图片 URL:')
  if (!url) return
  await promptsApi.addImageUrl(props.promptId, url)
  const promptRes = await promptsApi.get(props.promptId)
  images.value = (promptRes.data as PromptDetail).images || []
}

async function removeImage(imageId: number) {
  await promptsApi.deleteImage(imageId)
  images.value = images.value.filter((i) => i.id !== imageId)
}
</script>

<template>
  <div class="right-panel">
    <ImageGallery
      :images="images"
      :readonly="readonly"
      @upload="fileInput?.click()"
      @add-url="addUrl"
      @delete="removeImage"
    />
    <input
      v-if="!readonly"
      ref="fileInput"
      type="file"
      accept="image/*"
      style="display: none"
      @change="onFileSelected"
    />
    <WordCardPanel :prompt="prompt" />
  </div>
</template>

<style scoped>
.right-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  overflow-y: auto;
  border-left: 1px solid var(--color-border);
  padding-left: var(--space-lg);
}
</style>
