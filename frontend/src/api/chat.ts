import client from './client'
import { ChatSession, ChatMessage, ChatCompletionRequest, ChatCompletionResponse } from '../types'

export const chatApi = {
  listSessions: async (): Promise<{ items: ChatSession[]; total: number }> => {
    const response = await client.get('/chat/sessions')
    return response.data
  },
  
  getSession: async (id: number): Promise<ChatSession> => {
    const response = await client.get<ChatSession>(`/chat/sessions/${id}`)
    return response.data
  },
  
  createSession: async (data: {
    title?: string
    jurisdiction?: string
    mode?: string
  }): Promise<ChatSession> => {
    const response = await client.post<ChatSession>('/chat/sessions', data)
    return response.data
  },
  
  deleteSession: async (id: number): Promise<void> => {
    await client.delete(`/chat/sessions/${id}`)
  },
  
  getMessages: async (sessionId: number): Promise<ChatMessage[]> => {
    const response = await client.get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`)
    return response.data
  },
  
  sendMessage: async (
    sessionId: number,
    data: ChatCompletionRequest
  ): Promise<ChatCompletionResponse> => {
    const response = await client.post<ChatCompletionResponse>(
      `/chat/sessions/${sessionId}/completions`,
      data
    )
    return response.data
  },
}

