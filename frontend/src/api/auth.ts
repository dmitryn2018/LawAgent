import client from './client'
import { User, LoginRequest, TokenResponse } from '../types'

const AUTH_URL = '/auth'

export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await client.post<TokenResponse>(`${AUTH_URL}/login`, data)
    return response.data
  },
  
  logout: async (): Promise<void> => {
    await client.post(`${AUTH_URL}/logout`)
  },
  
  getCurrentUser: async (): Promise<User> => {
    const response = await client.get<User>(`${AUTH_URL}/me`)
    return response.data
  },
}

