<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { promptsApi, type PromptDetail } from '@/api/prompts'
import { statementTypesApi, type StatementTypeItem } from '@/api/statement-types'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const promptId = computed(() => Number(route.params.id))

const form = ref({
  title: '',
  text_en_full: '',
  text_zh_full: '',
  category: '',
})

const statementTypes = ref<StatementTypeItem[]>([])
const saving = ref(false)

onMounted(async () => {
  const typesRes = await statementTypesApi.list()
  statementTypes.value = typesRes.data as StatementTypeItem[]

  if (isEdit.value) {
    const res = await promptsApi.get(promptId.value)
    const p = res.data as PromptDetail
    form.value = {
      title: p.title,
      text_en_full: p.text_en_full,
      text_zh_full: p.text_zh_full,
      category: p.category,
    }
  }
})

async function save() {
  saving.value = true
  try {
    if (isEdit.value) {
      await promptsApi.update(promptId.value, form.value)
    } else {
      await promptsApi.create(form.value)
    }
    router.push('/prompts')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="prompt-form">
    <h1>{{ isEdit ? '编辑 Prompt' : '新增 Prompt' }}</h1>
    <form @submit.prevent="save" class="form">
      <div class="form-group">
        <label>标题</label>
        <input v-model="form.title" type="text" placeholder="可选标题" />
      </div>
      <div class="form-group">
        <label>英文 Prompt *</label>
        <textarea v-model="form.text_en_full" rows="6" required placeholder="粘贴英文 Prompt..."></textarea>
      </div>
      <div class="form-group">
        <label>中文翻译</label>
        <textarea v-model="form.text_zh_full" rows="4" placeholder="中文翻译..."></textarea>
      </div>
      <div class="form-group">
        <label>分类</label>
        <input v-model="form.category" type="text" placeholder="如：远古遗迹、森林自然..." />
      </div>
      <div class="form-actions">
        <button type="button" class="btn" @click="router.back()">取消</button>
        <button type="submit" class="btn btn-primary" :disabled="saving">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.prompt-form {
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-lg);
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.form-group label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: 600;
}

.form-group input,
.form-group textarea {
  width: 100%;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}
</style>
