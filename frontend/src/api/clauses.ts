import client from './client'
import { Clause, ClauseListResponse } from '../types'

export const clausesApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    category?: string
    jurisdiction?: string
    practice_area?: string
    language?: string
    search?: string
  }): Promise<ClauseListResponse> => {
    const response = await client.get<ClauseListResponse>('/clauses', { params })
    return response.data
  },
  
  getCategories: async (): Promise<string[]> => {
    const response = await client.get<string[]>('/clauses/categories')
    return response.data
  },
  
  get: async (id: number): Promise<Clause> => {
    const response = await client.get<Clause>(`/clauses/${id}`)
    return response.data
  },
  
  create: async (data: Omit<Clause, 'id' | 'created_at' | 'updated_at' | 'is_active'>): Promise<Clause> => {
    const response = await client.post<Clause>('/clauses', data)
    return response.data
  },
  
  update: async (id: number, data: Partial<Clause>): Promise<Clause> => {
    const response = await client.put<Clause>(`/clauses/${id}`, data)
    return response.data
  },
  
  delete: async (id: number): Promise<void> => {
    await client.delete(`/clauses/${id}`)
  },
}

