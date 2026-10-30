<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

const props = defineProps<{
  modelValue: number
  total: number
  pageSize: number
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

const inputValue = ref(String(props.modelValue))

watch(() => props.modelValue, (val) => {
  inputValue.value = String(val)
})

function goPrev() {
  if (props.modelValue > 1) {
    emit('update:modelValue', props.modelValue - 1)
  }
}

function goNext() {
  if (props.modelValue < totalPages.value) {
    emit('update:modelValue', props.modelValue + 1)
  }
}

function jumpToPage() {
  const val = parseInt(inputValue.value, 10)
  if (isNaN(val) || val < 1) {
    inputValue.value = String(props.modelValue)
    return
  }
  const clamped = Math.min(val, totalPages.value)
  inputValue.value = String(clamped)
  if (clamped !== props.modelValue) {
    emit('update:modelValue', clamped)
  }
}

function onInput(e: Event) {
  const target = e.target as HTMLInputElement
  // Only allow digits
  target.value = target.value.replace(/[^0-9]/g, '')
  inputValue.value = target.value
}
</script>

<template>
  <div class="page-nav" v-if="total > pageSize">
    <button class="btn btn-sm" :disabled="modelValue <= 1" @click="goPrev"><ChevronLeft :size="14" /> 上一页</button>

    <div class="page-jump">
      <input
        class="page-input"
        :value="inputValue"
        @input="onInput"
        @keyup.enter="jumpToPage"
        @blur="jumpToPage"
      />
      <span class="page-separator">/</span>
      <span class="page-total">{{ totalPages }}</span>
    </div>

    <button class="btn btn-sm" :disabled="modelValue >= totalPages" @click="goNext">下一页 <ChevronRight :size="14" /></button>
  </div>
</template>

<style scoped>
.page-nav {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-md);
}

.page-jump {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.page-input {
  width: 64px;
  height: 28px;
  text-align: center;
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-family: var(--font-mono);
  outline: none;
  transition: border-color var(--transition-fast);
}

.page-input:focus {
  border-color: var(--color-accent);
}

/* Remove spinner for number input */
.page-input::-webkit-outer-spin-button,
.page-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.page-input[type='number'] {
  -moz-appearance: textfield;
}

.page-separator {
  color: var(--color-text-muted);
}

.page-total {
  min-width: 24px;
  text-align: center;
  font-family: var(--font-mono);
}
</style>
