/**
 * API client functions for EchoNote backend
 */

import { Transcription, TranscriptionList } from './types'

const API_BASE_URL = '/api'

/**
 * Upload and transcribe an audio file
 */
export async function transcribeAudio(audioBlob: Blob, filename: string): Promise<Transcription> {
  const formData = new FormData()
  formData.append('file', audioBlob, filename)

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
 * Get list of transcriptions with pagination
 */
export async function getTranscriptions(skip: number = 0, limit: number = 50): Promise<TranscriptionList> {
  const response = await fetch(`${API_BASE_URL}/transcriptions?skip=${skip}&limit=${limit}`)

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
