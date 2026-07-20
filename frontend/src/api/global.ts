import apiClient from './client'

export interface GlobalStatementItem {
  text_en: string
  text_zh: string
  type_id: number | null
  type_name: string
  type_color: string
  statement_ids: number[]
  prompt_ids: number[]
  count: number
}

export interface WordTypeInfo {
  type_id: number | null
  type_name: string
  type_color: string
  count: number
}

export interface GlobalWordItem {
  word_en: string
  word_zh: string
  total_count: number
  types: WordTypeInfo[]
  prompt_ids: number[]
}

export interface GlobalPaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export const globalApi = {
  getStatements(params: {
    type_id?: number
    search?: string
    page?: number
    page_size?: number
  } = {}) {
    return apiClient.get('/statements/global', { params }) as Promise<{
      code: number
      data: GlobalPaginatedResponse<GlobalStatementItem>
    }>
  },

  getWords(params: {
    search?: string
    page?: number
    page_size?: number
  } = {}) {
    return apiClient.get('/words/global', { params }) as Promise<{
      code: number
      data: GlobalPaginatedResponse<GlobalWordItem>
    }>
  },
}
