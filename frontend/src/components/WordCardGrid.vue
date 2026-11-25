<script setup lang="ts">
import type { GlobalWordItem } from '@/api/global'
import { useSettingsStore, type WordCardDisplayMode } from '@/stores/settings'

const props = defineProps<{
  words: GlobalWordItem[]
}>()

const settings = useSettingsStore()

/** Compute a CSS background for a word card based on display mode */
function cardBackground(word: GlobalWordItem): string {
  const types = word.types
  if (!types || types.length === 0) {
    return 'var(--color-highlight)'
  }

  const mode: WordCardDisplayMode = settings.wordCardDisplayMode

  if (mode === 'solid' || types.length === 1) {
    return types[0].type_color
  }

  if (mode === 'gradient') {
    const total = types.reduce((s, t) => s + t.count, 0)
    let acc = 0
    const stops = types.map((t) => {
      acc += t.count
      const pct = Math.round((acc / total) * 100)
      return `${t.type_color} ${pct}%`
    })
    return `linear-gradient(135deg, ${stops.join(', ')})`
  }

  // dots mode: use main type color
  return types[0].type_color
}

/** Determine text color — black or white based on background brightness */
function textColor(word: GlobalWordItem): string {
  const types = word.types
  if (!types || types.length === 0) return '#60a5fa'  // default light blue
  const hex = types[0].type_color.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.55 ? '#000000' : '#ffffff'
}

/** Get display mode label for current mode */
const modeLabel = (): string => {
  const m = settings.wordCardDisplayMode
  if (m === 'gradient') return '渐变'
  if (m === 'solid') return '纯色'
  return '色点'
}
</script>

<template>
  <div class="word-card-grid">
    <div v-if="words.length === 0" class="empty">暂无单词数据</div>
    <div
      v-for="word in words"
      :key="word.word_en"
      class="word-card"
      :style="{
        background: cardBackground(word),
        color: textColor(word),
      }"
    >
      <!-- Dots row (dots mode) -->
      <div
        v-if="settings.wordCardDisplayMode === 'dots' && word.types.length > 0"
        class="type-dots"
      >
        <span
          v-for="(t, i) in word.types"
          :key="t.type_id ?? i"
          class="type-dot"
          :style="{ backgroundColor: t.type_color }"
          :title="`${t.type_name}: ${t.count}次`"
        ></span>
      </div>

      <span class="word-en">{{ word.word_en }}</span>
      <span class="word-zh">{{ word.word_zh }}</span>
      <span v-if="word.source !== 'danbooru'" class="word-count">{{ word.total_count }}次</span>

      <!-- Type tags row (solid mode) -->
      <div
        v-if="settings.wordCardDisplayMode === 'solid' && word.types.length > 0"
        class="type-tags"
      >
        <span
          v-for="(t, i) in word.types"
          :key="t.type_id ?? i"
          class="type-tag"
        >
          {{ t.type_name }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.word-card-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
}

.word-card {
  border-radius: 10px;
  padding: var(--space-md) var(--space-lg);
  min-width: 130px;
  flex: 0 0 calc(25% - var(--space-md));
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

.word-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
}

.word-en {
  font-family: var(--font-mono);
  font-size: var(--font-size-base);
  font-weight: 700;
}

.word-zh {
  font-size: var(--font-size-sm);
  opacity: 0.85;
}

.word-count {
  font-size: 0.75rem;
  opacity: 0.65;
}

.type-dots {
  display: flex;
  gap: 3px;
  margin-bottom: 2px;
}

.type-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.2);
}

.type-tags {
  display: flex;
  gap: 3px;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 2px;
}

.type-tag {
  background: rgba(0, 0, 0, 0.2);
  padding: 1px 6px;
  border-radius: 8px;
  font-size: 0.65rem;
}

.empty {
  width: 100%;
  padding: var(--space-xl);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

@media (max-width: 900px) {
  .word-card {
    flex: 0 0 calc(33.333% - var(--space-md));
  }
}

@media (max-width: 600px) {
  .word-card {
    flex: 0 0 calc(50% - var(--space-md));
  }
}
</style>
