import client from './client'
import { Template, TemplateRenderRequest, TemplateRenderResponse } from '../types'

export const templatesApi = {
  list: async (params?: {
    category?: string
    jurisdiction?: string
  }): Promise<{ items: Template[]; total: number }> => {
    const response = await client.get('/templates', { params })
    return response.data
  },
  
  get: async (id: number): Promise<Template> => {
    const response = await client.get<Template>(`/templates/${id}`)
    return response.data
  },
  
  render: async (id: number, data: TemplateRenderRequest): Promise<TemplateRenderResponse> => {
    const response = await client.post<TemplateRenderResponse>(`/templates/${id}/render`, data)
    return response.data
  },
  
  getDownloadUrl: (templateId: number, fileId: string): string => {
    return `/api/templates/${templateId}/download/${fileId}`
  },
}

