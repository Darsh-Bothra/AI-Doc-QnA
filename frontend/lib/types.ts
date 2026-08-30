export type DocumentStatus = "processing" | "completed" | "failed"

export type Document = {
  id: number
  name: string
  status: DocumentStatus
  error_message: string | null
  created_at: string
  updated_at: string
}

export type DocumentListResponse = {
  total_count: number
  documents: Document[]
}

export type LoginResponse = {
  access_token: string
  token_type: string
}

export type SearchHit = {
  score: number
  text: string | null
  document_id: number | null
  chunk_id: number | string
}

export type SearchResponse = {
  question: string
  results: SearchHit[]
}

export type AskResponse = {
  answer: string
  sources: SearchHit[]
}
