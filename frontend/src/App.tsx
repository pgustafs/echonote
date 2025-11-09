/**
 * Main App component for EchoNote
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
      // Use .wav extension for WAV format
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
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <header className="text-center mb-16">
          <div className="flex items-center justify-center space-x-4 mb-6 animate-float">
            <div
              className="w-16 h-16 rounded-3xl flex items-center justify-center shadow-2xl transform rotate-3"
              style={{
                background: 'linear-gradient(90deg, #6B9FED 0%, #9B6FED 100%)',
                boxShadow: '0 20px 40px rgba(107, 159, 237, 0.4)'
              }}
            >
              <svg
                className="w-9 h-9 text-white transform -rotate-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2.5}
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                />
              </svg>
            </div>
            <h1 className="text-6xl font-bold text-white drop-shadow-lg">
              EchoNote
            </h1>
          </div>
          <p className="text-white/90 text-xl font-medium">
            Voice transcription powered by AI
          </p>
          <p className="text-white/70 text-sm mt-2">
            Record, transcribe, and store your voice messages instantly
          </p>
        </header>

        {/* Error Message */}
        {error && (
          <div className="mb-8 glass-card-solid p-4 border-l-4 border-red-400">
            <div className="flex items-center space-x-3 text-red-300">
              <svg className="w-6 h-6 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="font-semibold">{error}</span>
            </div>
          </div>
        )}

        {/* Audio Recorder */}
        <div className="mb-16">
          <AudioRecorder
            onRecordingComplete={handleRecordingComplete}
            isTranscribing={isTranscribing}
            availableModels={availableModels}
            defaultModel={defaultModel}
          />
        </div>

        {/* Priority Filter */}
        <div className="mb-8">
          <div className="glass-card-solid p-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <label className="text-white font-semibold text-lg">Filter by Priority:</label>
              <div className="flex items-center gap-3 flex-wrap">
                <button
                  onClick={() => setPriorityFilter(null)}
                  className={`px-4 py-2 rounded-xl font-medium transition-all duration-200 ${
                    priorityFilter === null
                      ? 'text-white shadow-lg scale-105'
                      : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700 hover:text-white'
                  }`}
                  style={priorityFilter === null ? {
                    background: 'linear-gradient(90deg, #6B9FED 0%, #9B6FED 100%)',
                    boxShadow: '0 4px 20px rgba(107, 159, 237, 0.3)'
                  } : undefined}
                >
                  All
                </button>
                <button
                  onClick={() => setPriorityFilter('high')}
                  className={`px-4 py-2 rounded-xl font-medium transition-all duration-200 ${
                    priorityFilter === 'high'
                      ? 'bg-red-500 text-white shadow-lg shadow-red-500/30 scale-105'
                      : 'bg-red-500/20 text-red-300 hover:bg-red-500/30 hover:text-red-200 border border-red-500/30'
                  }`}
                >
                  High
                </button>
                <button
                  onClick={() => setPriorityFilter('medium')}
                  className={`px-4 py-2 rounded-xl font-medium transition-all duration-200 ${
                    priorityFilter === 'medium'
                      ? 'bg-yellow-500 text-white shadow-lg shadow-yellow-500/30 scale-105'
                      : 'bg-yellow-500/20 text-yellow-300 hover:bg-yellow-500/30 hover:text-yellow-200 border border-yellow-500/30'
                  }`}
                >
                  Medium
                </button>
                <button
                  onClick={() => setPriorityFilter('low')}
                  className={`px-4 py-2 rounded-xl font-medium transition-all duration-200 ${
                    priorityFilter === 'low'
                      ? 'bg-green-500 text-white shadow-lg shadow-green-500/30 scale-105'
                      : 'bg-green-500/20 text-green-300 hover:bg-green-500/30 hover:text-green-200 border border-green-500/30'
                  }`}
                >
                  Low
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Transcription List */}
        {isLoading ? (
          <div className="glass-card-solid p-16 text-center">
            <div className="relative w-16 h-16 mx-auto mb-6">
              <div className="absolute inset-0 rounded-full border-4" style={{ borderColor: 'rgba(107, 159, 237, 0.2)' }}></div>
              <div className="absolute inset-0 rounded-full border-4 border-transparent animate-spin" style={{ borderTopColor: '#6B9FED' }}></div>
            </div>
            <p className="text-white font-medium">Loading transcriptions...</p>
          </div>
        ) : (
          <TranscriptionList transcriptions={transcriptions} onDelete={handleDelete} onUpdate={handleUpdate} />
        )}

        {/* Footer */}
        <footer className="mt-20 text-center">
          <div className="glass-card p-6">
            <p className="text-white/80 text-sm font-medium">
              Powered by{' '}
              <a
                href="https://fastapi.tiangolo.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-white transition-colors underline"
                style={{ textDecorationColor: 'rgba(107, 159, 237, 0.5)' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = '#6B9FED'
                  e.currentTarget.style.textDecorationColor = '#6B9FED'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = 'white'
                  e.currentTarget.style.textDecorationColor = 'rgba(107, 159, 237, 0.5)'
                }}
              >
                FastAPI
              </a>
              {' & '}
              <a
                href="https://vitejs.dev/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-white transition-colors underline"
                style={{ textDecorationColor: 'rgba(107, 159, 237, 0.5)' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = '#6B9FED'
                  e.currentTarget.style.textDecorationColor = '#6B9FED'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = 'white'
                  e.currentTarget.style.textDecorationColor = 'rgba(107, 159, 237, 0.5)'
                }}
              >
                Vite
              </a>
            </p>
          </div>
        </footer>
      </div>
    </div>
  )
}

export default App
