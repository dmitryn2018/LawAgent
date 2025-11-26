import client from './client'
import { RuntimeInfo } from '../types'

export const metaApi = {
  getRuntime: async (): Promise<RuntimeInfo> => {
    const response = await client.get<RuntimeInfo>('/meta/runtime')
    return response.data
  },
}
