import apiClient from './client'

export interface StatementTypeItem {
  id: number
  name: string
  color: string
  sort_order: number
}

export const statementTypesApi = {
  list() {
    return apiClient.get('/statement-types') as Promise<{ code: number; data: StatementTypeItem[] }>
  },

  create(data: { name: string; color?: string; sort_order?: number }) {
    return apiClient.post('/statement-types', data)
  },

  update(id: number, data: { name?: string; color?: string; sort_order?: number }) {
    return apiClient.put(`/statement-types/${id}`, data)
  },

  delete(id: number) {
    return apiClient.delete(`/statement-types/${id}`)
  },
}
