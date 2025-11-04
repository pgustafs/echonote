/**
 * API client functions for EchoNote backend
 */

import { Priority, Transcription, TranscriptionList } from './types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export interface ModelsResponse {
  models: string[]
  default: string
}

/**
 * Get available transcription models
 */
export async function getModels(): Promise<ModelsResponse> {
  const response = await fetch(`${API_BASE_URL}/models`)

  if (!response.ok) {
    throw new Error('Failed to fetch models')
  }

  return response.json()
}

/**
 * Upload and transcribe an audio file
 */
export async function transcribeAudio(audioBlob: Blob, filename: string, url?: string, model?: string): Promise<Transcription> {
  const formData = new FormData()
  formData.append('file', audioBlob, filename)

  if (url) {
    formData.append('url', url)
  }

  if (model) {
    formData.append('model', model)
  }

  const response = await fetch(`${API_BASE_URL}/transcribe`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Transcription failed')
  }

  return response.json()
}

/**
 * Get list of transcriptions with pagination and optional priority filter
 */
export async function getTranscriptions(skip: number = 0, limit: number = 50, priority?: Priority | null): Promise<TranscriptionList> {
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
  })

  if (priority) {
    params.append('priority', priority)
  }

  const response = await fetch(`${API_BASE_URL}/transcriptions?${params}`)

  if (!response.ok) {
    throw new Error('Failed to fetch transcriptions')
  }

  return response.json()
}

/**
 * Get a specific transcription by ID
 */
export async function getTranscription(id: number): Promise<Transcription> {
  const response = await fetch(`${API_BASE_URL}/transcriptions/${id}`)

  if (!response.ok) {
    throw new Error('Transcription not found')
  }

  return response.json()
}

/**
 * Get audio URL for a transcription
 */
export function getAudioUrl(id: number): string {
  return `${API_BASE_URL}/transcriptions/${id}/audio`
}

/**
 * Update transcription priority
 */
export async function updateTranscriptionPriority(id: number, priority: Priority): Promise<Transcription> {
  const params = new URLSearchParams({
    priority: priority,
  })

  const response = await fetch(`${API_BASE_URL}/transcriptions/${id}?${params}`, {
    method: 'PATCH',
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to update priority')
  }

  return response.json()
}

/**
 * Delete a transcription
 */
export async function deleteTranscription(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/transcriptions/${id}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error('Failed to delete transcription')
  }
}
