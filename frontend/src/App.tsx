/**
 * Main App component for EchoNote
 */

import { useEffect, useState } from 'react'
import { getTranscriptions, transcribeAudio } from './api'
import AudioRecorder from './components/AudioRecorder'
import TranscriptionList from './components/TranscriptionList'
import { Transcription } from './types'

function App() {
  const [transcriptions, setTranscriptions] = useState<Transcription[]>([])
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load transcriptions on mount
  useEffect(() => {
    loadTranscriptions()
  }, [])

  const loadTranscriptions = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await getTranscriptions()
      setTranscriptions(data.transcriptions)
    } catch (err) {
      console.error('Error loading transcriptions:', err)
      setError('Failed to load transcriptions')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRecordingComplete = async (audioBlob: Blob) => {
    setIsTranscribing(true)
    setError(null)

    try {
      // Use .wav extension for WAV format
      const extension = audioBlob.type.includes('wav') ? 'wav' : 'webm'
      const filename = `recording-${Date.now()}.${extension}`
      const transcription = await transcribeAudio(audioBlob, filename)

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

  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <header className="text-center mb-16">
          <div className="flex items-center justify-center space-x-4 mb-6 animate-float">
            <div className="w-16 h-16 bg-gradient-to-br from-vite-500 via-electric-500 to-vite-600 rounded-3xl flex items-center justify-center shadow-2xl shadow-vite-500/50 transform rotate-3">
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
          />
        </div>

        {/* Transcription List */}
        {isLoading ? (
          <div className="glass-card-solid p-16 text-center">
            <div className="relative w-16 h-16 mx-auto mb-6">
              <div className="absolute inset-0 rounded-full border-4 border-vite-500/20"></div>
              <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-vite-400 animate-spin"></div>
            </div>
            <p className="text-white font-medium">Loading transcriptions...</p>
          </div>
        ) : (
          <TranscriptionList transcriptions={transcriptions} onDelete={handleDelete} />
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
                className="text-white hover:text-vite-300 transition-colors underline decoration-vite-400/50 hover:decoration-vite-300"
              >
                FastAPI
              </a>
              {' & '}
              <a
                href="https://vitejs.dev/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-white hover:text-electric-300 transition-colors underline decoration-electric-400/50 hover:decoration-electric-300"
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
