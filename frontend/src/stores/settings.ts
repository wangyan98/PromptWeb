// frontend/src/stores/settings.ts
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type WordCardDisplayMode = 'gradient' | 'solid' | 'dots'

const STORAGE_KEY = 'promptweb-settings'

interface SettingsData {
  wordCardDisplayMode: WordCardDisplayMode
}

function loadSettings(): SettingsData {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      return {
        wordCardDisplayMode: parsed.wordCardDisplayMode || 'gradient',
      }
    }
  } catch {
    // ignore parse errors, use defaults
  }
  return { wordCardDisplayMode: 'gradient' }
}

function saveSettings(data: SettingsData): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
}

export const useSettingsStore = defineStore('settings', () => {
  const initial = loadSettings()
  const wordCardDisplayMode = ref<WordCardDisplayMode>(initial.wordCardDisplayMode)

  watch(wordCardDisplayMode, (newMode) => {
    saveSettings({ wordCardDisplayMode: newMode })
  })

  function setDisplayMode(mode: WordCardDisplayMode) {
    wordCardDisplayMode.value = mode
  }

  return { wordCardDisplayMode, setDisplayMode }
})
