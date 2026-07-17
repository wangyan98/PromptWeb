import { defineStore } from 'pinia'
import { ref } from 'vue'
import { statementTypesApi, type StatementTypeItem } from '@/api/statement-types'

export const useStatementTypeStore = defineStore('statementTypes', () => {
  const types = ref<StatementTypeItem[]>([])
  const loaded = ref(false)

  async function load() {
    if (loaded.value) return
    const res = await statementTypesApi.list()
    types.value = res.data as StatementTypeItem[]
    loaded.value = true
  }

  function getType(id: number | null): StatementTypeItem | undefined {
    return types.value.find((t) => t.id === id)
  }

  return { types, loaded, load, getType }
})
