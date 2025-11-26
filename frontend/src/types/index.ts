// User types
export interface User {
  id: number
  email: string
  full_name: string | null
  role: 'lawyer' | 'admin'
  is_active: boolean
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

// Document types
export interface Document {
  id: number
  title: string
  document_type: string
  jurisdiction: string | null
  practice_area: string | null
  file_name: string | null
  file_type: string | null
  indexing_status: string
  created_at: string
  updated_at: string
  content?: string
  doc_metadata?: Record<string, unknown>
  chunk_count?: number
}

export interface DocumentListResponse {
  items: Document[]
  total: number
  page: number
  page_size: number
}

// Chat types
export interface ChatSession {
  id: number
  user_id: number
  title: string | null
  jurisdiction: string | null
  mode: string
  created_at: string
  updated_at: string
}

export interface SourceReference {
  document_id: number
  chunk_id: number
  title: string
  snippet: string
  relevance: number
}

export interface ChatMessage {
  id: number
  session_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  sources: SourceReference[] | null
  created_at: string
}

export interface ChatCompletionRequest {
  message: string
  jurisdiction?: string
  mode?: string
}

export interface ChatCompletionResponse {
  message: ChatMessage
  sources: SourceReference[]
}

// Template types
export interface FormField {
  name: string
  type: 'text' | 'textarea' | 'select' | 'checkbox' | 'date'
  label: string
  required: boolean
  default?: unknown
  options?: string[]
  placeholder?: string
}

export interface Template {
  id: number
  name: string
  description: string | null
  category: string | null
  jurisdiction: string | null
  form_schema: { fields: FormField[] }
  optional_sections: string[] | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TemplateRenderRequest {
  form_data: Record<string, unknown>
  include_sections?: string[]
  use_ai_generation: boolean
}

export interface TemplateRenderResponse {
  rendered_text: string
  file_id: string | null
  download_url: string | null
}

// Due Diligence types
export interface DDCheck {
  id: number
  user_id: number
  company_name: string
  check_type: 'ma_dd' | 'compliance'
  jurisdiction: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  raw_data: Record<string, unknown> | null
  ai_summary: string | null
  risk_indicators: {
    overall: 'low' | 'medium' | 'high'
    legal: 'low' | 'medium' | 'high'
    financial: 'low' | 'medium' | 'high'
    regulatory: 'low' | 'medium' | 'high'
  } | null
  risk_items: Array<{
    category: string
    severity: string
    title: string
    description: string
    impact_on_deal?: 'deal_breaker' | 'negotiable' | 'cosmetic'
  }> | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export interface DDCheckListResponse {
  items: DDCheck[]
  total: number
  page: number
  page_size: number
}

// Clause types
export interface Clause {
  id: number
  title: string
  body: string
  category: string
  tags: string[] | null
  jurisdiction: string | null
  practice_area: string | null
  language: string
  notes: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ClauseListResponse {
  items: Clause[]
  total: number
  page: number
  page_size: number
}

// Analysis types
export interface TextSpan {
  start_char: number
  end_char: number
}

export interface DocumentRisk {
  id: string
  title: string
  description: string
  severity: 'low' | 'medium' | 'high'
  spans: TextSpan[]
  recommendation: string | null
  impact_on_deal?: 'deal_breaker' | 'negotiable' | 'cosmetic'
}

export interface DealImpact {
  price: string
  structure: string
  control: string
}

export interface DocumentAnalysisResponse {
  summary: string
  risks: DocumentRisk[]
  recommendations: string[]
  key_terms: string[] | null
  parties: string[] | null
  overall_risk_level: 'low' | 'medium' | 'high'
  deal_impact: DealImpact | null
}

export interface SuggestedClause {
  id: number
  title: string
  body: string
  category: string
  relevance: number
}

// Runtime/Meta types
export interface RuntimeInfo {
  llm_provider: string
  embedding_provider: string
}

// Saved Analysis types
export interface ReviewerInfo {
  id: number
  full_name: string | null
  email: string
}

export interface SavedAnalysis {
  id: number
  document_text_hash: string
  analysis_data: DocumentAnalysisResponse
  review_status: 'unreviewed' | 'reviewed'
  reviewed_by: ReviewerInfo | null
  reviewed_at: string | null
  created_at: string
  updated_at: string
}

// Client Letter types
export interface ClientLetterRequest {
  summary: string
  risks: DocumentRisk[]
  deal_impact?: DealImpact | null
  language?: 'ru' | 'en'
}

export interface ClientLetterResponse {
  letter_text: string
}

// Search types
export interface SearchResult {
  document_id: number
  chunk_id: number
  document_title: string
  document_type: string
  jurisdiction: string | null
  text: string
  relevance: number
}

