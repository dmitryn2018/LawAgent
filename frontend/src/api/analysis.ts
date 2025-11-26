import client from './client'
import { 
  DocumentAnalysisResponse, 
  SuggestedClause, 
  SavedAnalysis,
  ClientLetterRequest,
  ClientLetterResponse,
  DocumentRisk,
  DealImpact
} from '../types'

export const analysisApi = {
  analyzeDocument: async (data: {
    text: string
    document_type?: string
    jurisdiction?: string
  }): Promise<DocumentAnalysisResponse> => {
    const response = await client.post<DocumentAnalysisResponse>('/analysis/analyze', data)
    return response.data
  },
  
  suggestClauses: async (data: {
    context: string
    category?: string
    jurisdiction?: string
    practice_area?: string
  }): Promise<{ suggestions: SuggestedClause[] }> => {
    const response = await client.post('/analysis/suggest-clauses', data)
    return response.data
  },

  generateClientLetter: async (data: {
    summary: string
    risks: DocumentRisk[]
    deal_impact?: DealImpact | null
    language?: 'ru' | 'en'
  }): Promise<ClientLetterResponse> => {
    const response = await client.post<ClientLetterResponse>('/analysis/client-letter', data)
    return response.data
  },

  saveAnalysis: async (data: {
    document_text_hash: string
    analysis_data: DocumentAnalysisResponse
  }): Promise<SavedAnalysis> => {
    const response = await client.post<SavedAnalysis>('/analysis/save', data)
    return response.data
  },

  getSavedAnalysis: async (analysisId: number): Promise<SavedAnalysis> => {
    const response = await client.get<SavedAnalysis>(`/analysis/saved/${analysisId}`)
    return response.data
  },

  getSavedAnalysisByHash: async (documentHash: string): Promise<SavedAnalysis> => {
    const response = await client.get<SavedAnalysis>(`/analysis/saved/by-hash/${documentHash}`)
    return response.data
  },

  markReviewed: async (analysisId: number): Promise<SavedAnalysis> => {
    const response = await client.post<SavedAnalysis>(`/analysis/saved/${analysisId}/review`)
    return response.data
  },
}

