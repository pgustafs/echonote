/**
 * API client functions for EchoNote backend
 */

import { Priority, Transcription, TranscriptionList } from './types'

// Get API URL from runtime config (injected via ConfigMap) or fallback to env var or localhost
// This function is called on every API request to ensure config is loaded
const getApiBaseUrl = (): string => {
  // @ts-ignore - window.APP_CONFIG is injected at runtime
  if (typeof window !== 'undefined' && window.APP_CONFIG && window.APP_CONFIG.API_URL) {
    // @ts-ignore
    return window.APP_CONFIG.API_URL
  }
  return import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
}

const TOKEN_KEY = 'echonote_token'

/**
 * Get authorization headers with JWT token if available
 */
function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    return {
      Authorization: `Bearer ${token}`,
    }
  }
  return {}
}

export interface ModelsResponse {
  models: string[]
  default: string
}

/**
 * Get available transcription models
 */
export async function getModels(): Promise<ModelsResponse> {
  const response = await fetch(`${getApiBaseUrl()}/models`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error('Failed to fetch models')
  }

  return response.json()
}

/**
 * Upload and transcribe an audio file
 */
export async function transcribeAudio(
  audioBlob: Blob,
  filename: string,
  url?: string,
  model?: string,
  enableDiarization?: boolean,
  numSpeakers?: number
): Promise<Transcription> {
  const formData = new FormData()
  formData.append('file', audioBlob, filename)

  if (url) {
    formData.append('url', url)
  }

  if (model) {
    formData.append('model', model)
  }

  if (enableDiarization !== undefined) {
    formData.append('enable_diarization', enableDiarization.toString())
  }

  if (numSpeakers !== undefined) {
    formData.append('num_speakers', numSpeakers.toString())
  }

  const response = await fetch(`${getApiBaseUrl()}/transcribe`, {
    method: 'POST',
    headers: getAuthHeaders(),
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
export async function getTranscriptions(skip: number = 0, limit: number = 50, priority?: Priority | null, search?: string | null): Promise<TranscriptionList> {
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
  })

  if (priority) {
    params.append('priority', priority)
  }

  if (search && search.trim()) {
    params.append('search', search.trim())
  }

  const response = await fetch(`${getApiBaseUrl()}/transcriptions?${params}`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error('Failed to fetch transcriptions')
  }

  return response.json()
}

/**
 * Get a specific transcription by ID
 */
export async function getTranscription(id: number): Promise<Transcription> {
  const response = await fetch(`${getApiBaseUrl()}/transcriptions/${id}`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error('Transcription not found')
  }

  return response.json()
}

/**
 * Get audio URL for a transcription
 * Note: For authenticated audio access, append token as query param in the audio element
 */
export function getAudioUrl(id: number): string {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    return `${getApiBaseUrl()}/transcriptions/${id}/audio?token=${encodeURIComponent(token)}`
  }
  return `${getApiBaseUrl()}/transcriptions/${id}/audio`
}

/**
 * Update transcription priority
 */
export async function updateTranscriptionPriority(id: number, priority: Priority): Promise<Transcription> {
  const params = new URLSearchParams({
    priority: priority,
  })

  const response = await fetch(`${getApiBaseUrl()}/transcriptions/${id}?${params}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
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
  const response = await fetch(`${getApiBaseUrl()}/transcriptions/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error('Failed to delete transcription')
  }
}

/**
 * Download a transcription as ZIP containing WAV audio and config.json
 */
export async function downloadTranscription(id: number): Promise<void> {
  const response = await fetch(`${getApiBaseUrl()}/transcriptions/${id}/download`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error('Failed to download transcription')
  }

  // Get the filename from Content-Disposition header, or use a default
  const contentDisposition = response.headers.get('Content-Disposition')
  let filename = `transcription_${id}.zip`
  if (contentDisposition) {
    const matches = /filename="([^"]+)"/.exec(contentDisposition)
    if (matches && matches[1]) {
      filename = matches[1]
    }
  }

  // Create a blob from the response
  const blob = await response.blob()

  // Create a temporary link element and trigger download
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()

  // Cleanup
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}
