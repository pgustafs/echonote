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
