/**
 * API client functions for EchoNote backend
 */

import { Priority, Category, Transcription, TranscriptionList } from './types'

// Get API URL from runtime config (injected via ConfigMap) or fallback to env var or localhost
// This function is called on every API request to ensure config is loaded
export const getApiBaseUrl = (): string => {
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
const REFRESH_TOKEN_KEY = 'echonote_refresh_token'

let isRefreshing = false
let refreshSubscribers: Array<(token: string) => void> = []

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

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
 * Refresh the access token using the refresh token
 */
async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
  if (!refreshToken) {
    return null
  }

  try {
    const response = await fetch(`${getApiBaseUrl()}/auth/refresh`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${refreshToken}`,
      },
    })

    if (!response.ok) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      return null
    }

    const data = await response.json()
    const newAccessToken = data.access_token

    localStorage.setItem(TOKEN_KEY, newAccessToken)
    return newAccessToken
  } catch (error) {
    console.error('Error refreshing token:', error)
    return null
  }
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

/**
 * Fetch wrapper that automatically handles token refresh on 401 errors
 */
async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const makeRequest = async (token?: string) => {
    const headers = {
      ...options.headers,
    }

    if (token) {
      Object.assign(headers, { Authorization: `Bearer ${token}` })
    } else {
      Object.assign(headers, getAuthHeaders())
    }

    return fetch(url, { ...options, headers })
  }

  const response = await makeRequest()

  if (response.status === 401) {
    if (isRefreshing) {
      return new Promise((resolve) => {
        subscribeTokenRefresh((token: string) => {
          resolve(makeRequest(token))
        })
      })
    }

    isRefreshing = true

    const newToken = await refreshAccessToken()

    isRefreshing = false

    if (newToken) {
      onTokenRefreshed(newToken)
      return makeRequest(newToken)
    } else {
      window.location.href = '/'
      throw new Error('Session expired. Please login again.')
    }
  }

  return response
}

export interface ModelsResponse {
  models: string[]
  default: string
}

/**
 * Get available transcription models
 */
export async function getModels(): Promise<ModelsResponse> {
  const response = await fetchWithAuth(`${getApiBaseUrl()}/models`)

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
    const response = await fetchWithAuth(`${getApiBaseUrl()}/transcribe`, {
      method: 'POST',
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
 * Get list of transcriptions with pagination and optional priority/category filters
 */
export async function getTranscriptions(
  skip: number = 0,
  limit: number = 50,
  priority?: Priority | null,
  search?: string | null,
  category?: Category | null
): Promise<TranscriptionList> {
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
  })

  if (priority) {
    params.append('priority', priority)
  }

  if (category) {
    params.append('category', category)
  }

  if (search && search.trim()) {
    params.append('search', search.trim())
  }

  const response = await fetchWithAuth(`${getApiBaseUrl()}/transcriptions?${params}`)

  if (!response.ok) {
    throw new Error('Failed to fetch transcriptions')
  }

  return response.json()
}

/**
 * Get a specific transcription by ID
 */
export async function getTranscription(id: number): Promise<Transcription> {
  const response = await fetchWithAuth(`${getApiBaseUrl()}/transcriptions/${id}`)

  if (!response.ok) {
    throw new Error('Transcription not found')
  }

  return response.json()
}

/**
 * Get audio URL for a transcription with optional format conversion
 * @param id - Transcription ID
 * @param format - Optional audio format (webm, wav, mp3, ogg). If not specified, returns original format.
 * Note: For authenticated audio access, append token as query param in the audio element
 */
export function getAudioUrl(id: number, format?: string): string {
  const token = localStorage.getItem(TOKEN_KEY)
  const baseUrl = `${getApiBaseUrl()}/transcriptions/${id}/audio`

  const params = new URLSearchParams()
  if (token) {
    params.append('token', token)
  }
  if (format) {
    params.append('format', format)
  }

  const queryString = params.toString()
  return queryString ? `${baseUrl}?${queryString}` : baseUrl
}

/**
 * Update transcription priority (legacy - use updateTranscription instead)
 */
export async function updateTranscriptionPriority(id: number, priority: Priority): Promise<Transcription> {
  return updateTranscription(id, { priority })
}

/**
 * Update transcription category
 */
export async function updateTranscriptionCategory(id: number, category: Category): Promise<Transcription> {
  return updateTranscription(id, { category })
}

/**
 * Update transcription (priority, category, or both)
 */
export async function updateTranscription(
  id: number,
  updates: { priority?: Priority; category?: Category }
): Promise<Transcription> {
  const response = await fetchWithAuth(`${getApiBaseUrl()}/transcriptions/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to update transcription')
  }

  return response.json()
}

/**
 * Delete a transcription
 */
export async function deleteTranscription(id: number): Promise<void> {
  const response = await fetchWithAuth(`${getApiBaseUrl()}/transcriptions/${id}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error('Failed to delete transcription')
  }
}

/**
 * Download a transcription as ZIP containing WAV audio and config.json
 */
export async function downloadTranscription(id: number, format?: string): Promise<void> {
  const params = new URLSearchParams()
  if (format) {
    params.append('format', format)
  }
  const queryString = params.toString()
  const url = queryString
    ? `${getApiBaseUrl()}/transcriptions/${id}/download?${queryString}`
    : `${getApiBaseUrl()}/transcriptions/${id}/download`

  const response = await fetchWithAuth(url)

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
  const downloadUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()

  // Cleanup
  document.body.removeChild(link)
  window.URL.revokeObjectURL(downloadUrl)
}

/**
 * Re-transcribe an existing transcription with new options
 */
export async function reTranscribeAudio(
  id: number,
  model?: string,
  url?: string,
  enableDiarization?: boolean,
  numSpeakers?: number
): Promise<Transcription> {
  const formData = new FormData()

  if (model) {
    formData.append('model', model)
  }

  if (url !== undefined) {
    formData.append('url', url)
  }

  if (enableDiarization !== undefined) {
    formData.append('enable_diarization', enableDiarization.toString())
  }

  if (numSpeakers !== undefined) {
    formData.append('num_speakers', numSpeakers.toString())
  }

  const response = await fetchWithAuth(`${getApiBaseUrl()}/transcriptions/${id}/re-transcribe`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP error ${response.status}`);
    } else {
      throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
    }
  }

  return response.json()
}

/**
 * Delete the audio file from a transcription while keeping the text
 */
export async function deleteAudioFile(id: number): Promise<Transcription> {
  const response = await fetchWithAuth(`${getApiBaseUrl()}/transcriptions/${id}/audio`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP error ${response.status}`);
    } else {
      throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
    }
  }

  return response.json()
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
  const response = await fetchWithAuth(`${getApiBaseUrl()}/transcriptions/${id}/status`)

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
  const response = await fetchWithAuth(`${getApiBaseUrl()}/transcriptions/status/bulk?ids=${idsParam}`)

  if (!response.ok) {
    throw new Error(`Failed to get bulk status: ${response.statusText}`)
  }

  return response.json()
}

// ============================================================================
// AI Actions APIs
// ============================================================================

import type { AIActionRequest, AIActionResponse, ImproveActionRequest, ChatRequest } from './types'

/**
 * Execute an AI action on a transcription
 */
export async function executeAIAction(
  endpoint: string,
  request: AIActionRequest
): Promise<AIActionResponse> {
  const response = await fetchWithAuth(`${getApiBaseUrl()}/v1/actions${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || `Failed to execute AI action: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Improve a previous AI action result with additional instructions
 */
export async function improveAIAction(
  actionId: string,
  request: ImproveActionRequest
): Promise<AIActionResponse> {
  const response = await fetchWithAuth(`${getApiBaseUrl()}/v1/actions/improve/${actionId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || `Failed to improve AI action: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Chat with the AI model
 */
export async function chatWithAI(
  request: ChatRequest
): Promise<AIActionResponse> {
  const response = await fetchWithAuth(`${getApiBaseUrl()}/v1/actions/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || `Failed to chat with AI: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Cleanup a LlamaStack session when no longer needed
 */
export async function cleanupAISession(sessionId: string): Promise<void> {
  const response = await fetchWithAuth(`${getApiBaseUrl()}/v1/actions/sessions/${sessionId}`, {
    method: 'DELETE',
  })

  // 204 No Content is success, no need to parse response
  if (!response.ok && response.status !== 204) {
    console.warn(`Failed to cleanup session ${sessionId}: ${response.statusText}`)
    // Don't throw error - cleanup is best-effort
  }
}

/**
 * Get current user information
 */
export async function getCurrentUser(): Promise<any> {
  const response = await fetchWithAuth(`${getApiBaseUrl()}/auth/me`)

  if (!response.ok) {
    throw new Error('Failed to fetch user')
  }

  return response.json()
}
