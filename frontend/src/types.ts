/**
 * TypeScript types for EchoNote frontend
 */

export type Priority = 'low' | 'medium' | 'high'

export interface Transcription {
  id: number
  text: string
  audio_filename: string
  audio_content_type: string
  created_at: string
  duration_seconds: number | null
  priority: Priority
  url: string | null
  task_id?: string | null
  status?: 'pending' | 'processing' | 'completed' | 'failed'
  progress?: number | null
  error_message?: string | null
}

export interface TranscriptionList {
  transcriptions: Transcription[]
  total: number
  skip: number
  limit: number
}

export interface ApiError {
  detail: string
}

export interface AIActionRequest {
  transcription_id: number
  options?: Record<string, any>
}

export interface AIActionResponse {
  action_id: string
  status: 'work_in_progress' | 'completed' | 'failed'
  message?: string
  quota_remaining: number
  quota_reset_date: string
  result?: Record<string, any> | null
  error?: string | null
  created_at: string
  completed_at?: string | null
  session_id?: string | null  // LlamaStack session ID for conversation continuity
}

export interface ImproveActionRequest {
  session_id: string
  instructions: string
}

export interface ChatRequest {
  message: string
  session_id?: string | null
  transcription_id?: number | null
}

export type AIActionCategory = 'analyze' | 'create' | 'improve' | 'translate' | 'voice' | 'chat'

export interface AIAction {
  id: string
  category: AIActionCategory
  label: string
  description: string
  icon: string
  endpoint: string
}
