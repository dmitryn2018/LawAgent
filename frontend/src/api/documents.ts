import client from './client'
import { Document, DocumentListResponse, SearchResult } from '../types'

export const documentsApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    document_type?: string
    jurisdiction?: string
    practice_area?: string
  }): Promise<DocumentListResponse> => {
    const response = await client.get<DocumentListResponse>('/documents', { params })
    return response.data
  },
  
  get: async (id: number): Promise<Document> => {
    const response = await client.get<Document>(`/documents/${id}`)
    return response.data
  },
  
  create: async (data: {
    title: string
    document_type: string
    jurisdiction?: string
    practice_area?: string
    content?: string
    doc_metadata?: Record<string, unknown>
  }): Promise<Document> => {
    const response = await client.post<Document>('/documents', data)
    return response.data
  },
  
  upload: async (file: File, data: {
    title: string
    document_type: string
    jurisdiction?: string
    practice_area?: string
  }): Promise<Document> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', data.title)
    formData.append('document_type', data.document_type)
    if (data.jurisdiction) formData.append('jurisdiction', data.jurisdiction)
    if (data.practice_area) formData.append('practice_area', data.practice_area)
    
    const response = await client.post<Document>('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
  
  update: async (id: number, data: Partial<Document>): Promise<Document> => {
    const response = await client.put<Document>(`/documents/${id}`, data)
    return response.data
  },
  
  delete: async (id: number): Promise<void> => {
    await client.delete(`/documents/${id}`)
  },
  
  reindex: async (id: number): Promise<void> => {
    await client.post(`/documents/${id}/reindex`)
  },
  
  search: async (params: {
    query: string
    jurisdiction?: string
    practice_area?: string
    document_type?: string
    top_k?: number
  }): Promise<{ query: string; results: SearchResult[]; total: number }> => {
    const response = await client.post('/documents/search', params)
    return response.data
  },
}

