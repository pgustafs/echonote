/**
 * API client functions for EchoNote backend
 */

import { Priority, Transcription, TranscriptionList } from './types'

// Get API URL from runtime config (injected via ConfigMap) or fallback to env var or localhost
// This function is called on every API request to ensure config is loaded
const getApiBaseUrl = (): string => {
  let apiUrl: string | undefined;

  // Try runtime config first (for Kubernetes deployments)
  // @ts-ignore - window.APP_CONFIG is injected at runtime
  if (typeof window !== 'undefined' && window.APP_CONFIG && window.APP_CONFIG.API_URL) {
    // @ts-ignore
    apiUrl = window.APP_CONFIG.API_URL;
    console.log('[API] Using runtime config API_URL:', apiUrl);
  }

  // Fallback to environment variable
  if (!apiUrl) {
    apiUrl = import.meta.env.VITE_API_URL;
    if (apiUrl) {
      console.log('[API] Using VITE_API_URL:', apiUrl);
    }
  }

  // Final fallback: construct from current location
  if (!apiUrl) {
    // For PWA, use current origin + /api
    const origin = window.location.origin;
    apiUrl = `${origin}/api`;
    console.log('[API] Using origin-based URL:', apiUrl);
  }

  // Validate URL
  try {
    new URL(apiUrl);
    console.log('[API] Final API URL:', apiUrl);
    return apiUrl;
  } catch (error) {
    console.error('[API] Invalid API URL:', apiUrl, error);
    // Last resort fallback
    const fallback = 'http://localhost:8000/api';
    console.warn('[API] Using fallback URL:', fallback);
    return fallback;
  }
}

const TOKEN_KEY = 'echonote_token'

/**
 * Custom error class for network failures
 * Used to distinguish server unreachable errors from API errors
 */
export class NetworkError extends Error {
  constructor(message: string = 'Network request failed - server may be unreachable') {
    super(message)
    this.name = 'NetworkError'
  }
}

/**
 * Custom error class for invalid Blob data from IndexedDB
 * Used to identify recordings that have been corrupted
 */
export class InvalidBlobError extends Error {
  constructor(message: string = 'Audio data is invalid or corrupted') {
    super(message)
    this.name = 'InvalidBlobError'
  }
}

/**
 * Check if an error is a network error (server unreachable)
 *
 * Network errors occur when:
 * - Server is unreachable
 * - DNS resolution fails
 * - Connection is refused
 * - CORS issues prevent request
 *
 * This is different from API errors (4xx, 5xx status codes)
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof NetworkError) {
    return true
  }

  // Fetch throws TypeError for network failures
  if (error instanceof TypeError) {
    const message = error.message.toLowerCase()
    // Common network error messages across browsers
    return (
      message.includes('failed to fetch') ||
      message.includes('network error') ||
      message.includes('networkerror') ||
      message.includes('load failed') ||
      message.includes('network request failed')
    )
  }

  return false
}

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

  try {
    // This can fail if the Blob data is corrupted (e.g., on mobile after PWA resumes)
    formData.append('file', audioBlob, filename)
  } catch (error) {
    console.error('[API] Error appending Blob to FormData:', error)
    // Throw a specific error to indicate corrupted local data
    throw new InvalidBlobError('Failed to read audio data; it may be corrupted.')
  }

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

  try {
    const response = await fetch(`${getApiBaseUrl()}/transcribe`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    })

    if (!response.ok) {
      // Check if the response is JSON before trying to parse it
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error ${response.status}`);
      } else {
        // Handle non-JSON errors (e.g., 500 from server crash)
        throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
      }
    }

    return response.json()
  } catch (error) {
    // If fetch itself failed (network error), wrap it
    if (error instanceof TypeError) {
      throw new NetworkError('Unable to reach server - recording will be saved offline')
    }
    // Re-throw API, InvalidBlobError, or the new HTTP error
    throw error
  }
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

// ============================================================================
// Background Task Status APIs
// ============================================================================

export interface TranscriptionStatus {
  id: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number | null
  task_id: string | null
  error_message: string | null
}

export interface BulkStatusResponse {
  statuses: Array<{
    id: number
    status: string
    progress: number | null
    error_message: string | null
  }>
}

/**
 * Get status for a single transcription
 */
export async function getTranscriptionStatus(id: number): Promise<TranscriptionStatus> {
  const response = await fetch(`${getApiBaseUrl()}/transcriptions/${id}/status`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to get transcription status: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Get status for multiple transcriptions at once
 */
export async function getBulkTranscriptionStatus(ids: number[]): Promise<BulkStatusResponse> {
  if (ids.length === 0) {
    return { statuses: [] }
  }

  const idsParam = ids.join(',')
  const response = await fetch(`${getApiBaseUrl()}/transcriptions/status/bulk?ids=${idsParam}`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to get bulk status: ${response.statusText}`)
  }

  return response.json()
}
