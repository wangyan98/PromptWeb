import apiClient from './client'

export interface PromptListItem {
  id: number
  title: string
  text_en_full: string
  text_zh_full: string
  category: string
  thumbnail_url: string | null
  created_at: string
  updated_at: string
}

export interface StatementResponse {
  id: number
  prompt_id: number
  text_en: string
  text_zh: string
  sort_order: number
  type_id: number | null
  words: PromptWordResponse[]
}

export interface PromptWordResponse {
  id: number
  prompt_id: number
  statement_id: number
  word_en: string
  word_zh: string
  position_start: number | null
  position_end: number | null
}

export interface PromptImageResponse {
  id: number
  prompt_id: number
  url: string
  storage_type: string
  sort_order: number
  width: number | null
  height: number | null
}

export interface PromptDetail {
  id: number
  title: string
  text_en_full: string
  text_zh_full: string
  category: string
  source_file: string
  created_at: string
  updated_at: string
  statements: StatementResponse[]
  words: PromptWordResponse[]
  images: PromptImageResponse[]
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export const promptsApi = {
  list(params: { page?: number; page_size?: number; search?: string; category?: string } = {}) {
    return apiClient.get('/prompts', { params }) as Promise<{ code: number; data: PaginatedResponse<PromptListItem> }>
  },

  get(id: number) {
    return apiClient.get(`/prompts/${id}`) as Promise<{ code: number; data: PromptDetail }>
  },

  create(data: { title?: string; text_en_full: string; text_zh_full?: string; category?: string }) {
    return apiClient.post('/prompts', data)
  },

  update(id: number, data: Record<string, unknown>) {
    return apiClient.put(`/prompts/${id}`, data)
  },

  delete(id: number) {
    return apiClient.delete(`/prompts/${id}`)
  },

  getCategories() {
    return apiClient.get('/prompts/categories') as Promise<{ code: number; data: string[] }>
  },

  // Statements
  createStatements(promptId: number, statements: { text_en: string; text_zh: string; sort_order: number; type_id: number | null }[]) {
    return apiClient.post(`/prompts/${promptId}/statements`, statements)
  },

  updateStatement(id: number, data: Record<string, unknown>) {
    return apiClient.put(`/statements/${id}`, data)
  },

  deleteStatement(id: number) {
    return apiClient.delete(`/statements/${id}`)
  },

  // Words
  createWords(statementId: number, words: { word_en: string; word_zh: string; position_start?: number; position_end?: number }[]) {
    return apiClient.post(`/statements/${statementId}/words`, words)
  },

  deleteWord(id: number) {
    return apiClient.delete(`/words/${id}`)
  },

  // Images
  uploadImage(promptId: number, file: File) {
    const form = new FormData()
    form.append('file', file)
    return apiClient.post(`/prompts/${promptId}/images`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  addImageUrl(promptId: number, url: string) {
    const form = new FormData()
    form.append('url', url)
    return apiClient.post(`/prompts/${promptId}/images`, form)
  },

  deleteImage(id: number) {
    return apiClient.delete(`/images/${id}`)
  },
}
