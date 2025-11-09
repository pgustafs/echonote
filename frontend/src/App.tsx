/**
 * Main App component for EchoNote
 * Professional enterprise design with mobile-first responsive layout
 */

import { useEffect, useState } from 'react'
import { getModels, getTranscriptions, transcribeAudio } from './api'
import AudioRecorder from './components/AudioRecorder'
import TranscriptionList from './components/TranscriptionList'
import { Priority, Transcription } from './types'

function App() {
  const [transcriptions, setTranscriptions] = useState<Transcription[]>([])
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [priorityFilter, setPriorityFilter] = useState<Priority | null>(null)
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [defaultModel, setDefaultModel] = useState<string>('')

  // Load models on mount
  useEffect(() => {
    loadModels()
  }, [])

  // Load transcriptions on mount and when filter changes
  useEffect(() => {
    loadTranscriptions()
  }, [priorityFilter])

  const loadModels = async () => {
    try {
      const data = await getModels()
      setAvailableModels(data.models)
      setDefaultModel(data.default)
    } catch (err) {
      console.error('Error loading models:', err)
      setError('Failed to load available models')
    }
  }

  const loadTranscriptions = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await getTranscriptions(0, 50, priorityFilter)
      setTranscriptions(data.transcriptions)
    } catch (err) {
      console.error('Error loading transcriptions:', err)
      setError('Failed to load transcriptions')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRecordingComplete = async (
    audioBlob: Blob,
    url?: string,
    model?: string,
    enableDiarization?: boolean,
    numSpeakers?: number
  ) => {
    setIsTranscribing(true)
    setError(null)

    try {
      const extension = audioBlob.type.includes('wav') ? 'wav' : 'webm'
      const filename = `recording-${Date.now()}.${extension}`
      const transcription = await transcribeAudio(
        audioBlob,
        filename,
        url,
        model,
        enableDiarization,
        numSpeakers
      )

      // Add new transcription to the top of the list
      setTranscriptions([transcription, ...transcriptions])
    } catch (err) {
      console.error('Error transcribing audio:', err)
      setError(err instanceof Error ? err.message : 'Transcription failed')
    } finally {
      setIsTranscribing(false)
    }
  }

  const handleDelete = (id: number) => {
    setTranscriptions(transcriptions.filter((t) => t.id !== id))
  }

  const handleUpdate = (id: number, updated: Transcription) => {
    setTranscriptions(transcriptions.map((t) => t.id === id ? updated : t))
  }

  return (
    <div className="min-h-screen">
      {/* Header with gradient background */}
      <header className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center space-x-3 sm:space-x-4">
              {/* Icon */}
              <div className="w-12 h-12 sm:w-14 sm:h-14 bg-white rounded-lg shadow-md flex items-center justify-center flex-shrink-0">
                <svg
                  className="w-7 h-7 sm:w-8 sm:h-8 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                  />
                </svg>
              </div>
              {/* Title */}
              <div>
                <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-white">
                  EchoNote
                </h1>
                <p className="text-blue-100 text-sm sm:text-base mt-1">
                  AI-Powered Voice Transcription
                </p>
              </div>
            </div>
            {/* Stats badge - hidden on mobile */}
            <div className="hidden sm:flex items-center space-x-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-lg border border-white/20">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="text-white font-semibold">{transcriptions.length} Recordings</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-12">
        {/* Error Message */}
        {error && (
          <div className="mb-6 sm:mb-8 bg-red-50 border-l-4 border-red-500 rounded-lg p-4 shadow-sm">
            <div className="flex items-start space-x-3">
              <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-red-800">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="flex-shrink-0 text-red-500 hover:text-red-700 touch-target"
                aria-label="Dismiss error"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Audio Recorder Section */}
        <section className="mb-8 sm:mb-12">
          <AudioRecorder
            onRecordingComplete={handleRecordingComplete}
            isTranscribing={isTranscribing}
            availableModels={availableModels}
            defaultModel={defaultModel}
          />
        </section>

        {/* Filter Section */}
        <section className="mb-6 sm:mb-8">
          <div className="enterprise-card-dark p-4 sm:p-6">
            <div className="space-y-3 sm:space-y-0 sm:flex sm:items-center sm:justify-between sm:gap-4">
              <label className="text-white font-semibold text-sm sm:text-base lg:text-lg flex items-center space-x-2">
                <svg className="w-4 h-4 sm:w-5 sm:h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                </svg>
                <span>Filter by Priority</span>
              </label>
              <div className="grid grid-cols-2 sm:flex sm:flex-wrap gap-2">
                <button
                  onClick={() => setPriorityFilter(null)}
                  className={`px-4 py-2.5 rounded-lg font-medium transition-all duration-200 min-h-[44px] touch-manipulation text-sm sm:text-base ${
                    priorityFilter === null
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600 hover:text-white'
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => setPriorityFilter('high')}
                  className={`px-4 py-2.5 rounded-lg font-medium transition-all duration-200 min-h-[44px] touch-manipulation text-sm sm:text-base ${
                    priorityFilter === 'high'
                      ? 'bg-red-600 text-white shadow-md'
                      : 'bg-red-600/20 text-red-300 hover:bg-red-600/30 border border-red-600/30'
                  }`}
                >
                  High
                </button>
                <button
                  onClick={() => setPriorityFilter('medium')}
                  className={`px-4 py-2.5 rounded-lg font-medium transition-all duration-200 min-h-[44px] touch-manipulation text-sm sm:text-base ${
                    priorityFilter === 'medium'
                      ? 'bg-yellow-600 text-white shadow-md'
                      : 'bg-yellow-600/20 text-yellow-300 hover:bg-yellow-600/30 border border-yellow-600/30'
                  }`}
                >
                  Medium
                </button>
                <button
                  onClick={() => setPriorityFilter('low')}
                  className={`px-4 py-2.5 rounded-lg font-medium transition-all duration-200 min-h-[44px] touch-manipulation text-sm sm:text-base ${
                    priorityFilter === 'low'
                      ? 'bg-green-600 text-white shadow-md'
                      : 'bg-green-600/20 text-green-300 hover:bg-green-600/30 border border-green-600/30'
                  }`}
                >
                  Low
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Transcriptions List */}
        <section>
          {isLoading ? (
            <div className="enterprise-card-dark p-12 sm:p-16 text-center">
              <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-4 sm:mb-6 spinner"></div>
              <p className="text-white font-medium text-base sm:text-lg">Loading transcriptions...</p>
            </div>
          ) : (
            <TranscriptionList
              transcriptions={transcriptions}
              onDelete={handleDelete}
              onUpdate={handleUpdate}
            />
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="mt-12 sm:mt-20 border-t border-slate-700/50 bg-slate-900/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm">
            <p className="text-slate-400">
              © 2025 EchoNote. AI-powered voice transcription.
            </p>
            <div className="flex items-center space-x-4 text-slate-400">
              <span>Powered by</span>
              <a
                href="https://fastapi.tiangolo.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 transition-colors underline decoration-blue-400/30"
              >
                FastAPI
              </a>
              <span>&</span>
              <a
                href="https://vitejs.dev/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 transition-colors underline decoration-blue-400/30"
              >
                Vite
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
