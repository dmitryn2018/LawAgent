import client from './client'
import { DDCheck, DDCheckListResponse } from '../types'

export const ddApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    check_type?: string
    status?: string
  }): Promise<DDCheckListResponse> => {
    const response = await client.get<DDCheckListResponse>('/dd-checks', { params })
    return response.data
  },
  
  get: async (id: number): Promise<DDCheck> => {
    const response = await client.get<DDCheck>(`/dd-checks/${id}`)
    return response.data
  },
  
  create: async (data: {
    company_name: string
    check_type: string
    jurisdiction: string
  }): Promise<DDCheck> => {
    const response = await client.post<DDCheck>('/dd-checks', data)
    return response.data
  },
  
  delete: async (id: number): Promise<void> => {
    await client.delete(`/dd-checks/${id}`)
  },
}

