/**
 * Transcription list component with expand/collapse and audio playback
 */

import { useState } from 'react'
import { deleteTranscription, getAudioUrl } from '../api'
import { Transcription } from '../types'

interface TranscriptionListProps {
  transcriptions: Transcription[]
  onDelete: (id: number) => void
}

export default function TranscriptionList({ transcriptions, onDelete }: TranscriptionListProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [playingId, setPlayingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this transcription?')) {
      return
    }

    setDeletingId(id)
    try {
      await deleteTranscription(id)
      onDelete(id)
    } catch (error) {
      console.error('Error deleting transcription:', error)
      alert('Failed to delete transcription')
    } finally {
      setDeletingId(null)
    }
  }

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  const truncateText = (text: string, maxLength: number = 100): string => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  if (transcriptions.length === 0) {
    return (
      <div className="card p-12 text-center">
        <svg
          className="w-24 h-24 mx-auto mb-4 text-slate-300 dark:text-slate-600"
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
        <h3 className="text-xl font-semibold text-slate-600 dark:text-slate-400 mb-2">
          No transcriptions yet
        </h3>
        <p className="text-slate-500 dark:text-slate-500">
          Record your first voice message to get started
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
        Transcriptions ({transcriptions.length})
      </h2>

      <div className="space-y-3">
        {transcriptions.map((transcription) => {
          const isExpanded = expandedId === transcription.id
          const isPlaying = playingId === transcription.id
          const isDeleting = deletingId === transcription.id

          return (
            <div
              key={transcription.id}
              className="card p-6 hover:shadow-2xl transition-all duration-200"
            >
              {/* Header */}
              <div
                className="flex items-start justify-between cursor-pointer"
                onClick={() => toggleExpand(transcription.id)}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-3 mb-2">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200">
                      #{transcription.id}
                    </span>
                    <span className="text-sm text-slate-500 dark:text-slate-400">
                      {formatDate(transcription.created_at)}
                    </span>
                  </div>
                  <p className="text-slate-700 dark:text-slate-300">
                    {isExpanded ? transcription.text : truncateText(transcription.text)}
                  </p>
                </div>

                {/* Expand Icon */}
                <svg
                  className={`w-5 h-5 text-slate-400 transition-transform duration-200 flex-shrink-0 ml-4 ${
                    isExpanded ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </div>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-700">
                  <div className="flex items-center justify-between">
                    {/* Audio Player */}
                    <div className="flex items-center space-x-4 flex-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          const audio = document.getElementById(
                            `audio-${transcription.id}`
                          ) as HTMLAudioElement
                          if (audio) {
                            if (isPlaying) {
                              audio.pause()
                              setPlayingId(null)
                            } else {
                              audio.play()
                              setPlayingId(transcription.id)
                            }
                          }
                        }}
                        className="w-12 h-12 rounded-full bg-primary-600 hover:bg-primary-700 text-white flex items-center justify-center transition-colors duration-200 shadow-lg shadow-primary-500/30"
                      >
                        {isPlaying ? (
                          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                            <path
                              fillRule="evenodd"
                              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z"
                              clipRule="evenodd"
                            />
                          </svg>
                        ) : (
                          <svg className="w-6 h-6 ml-1" fill="currentColor" viewBox="0 0 20 20">
                            <path
                              fillRule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                              clipRule="evenodd"
                            />
                          </svg>
                        )}
                      </button>

                      <audio
                        id={`audio-${transcription.id}`}
                        src={getAudioUrl(transcription.id)}
                        onEnded={() => setPlayingId(null)}
                        onPause={() => setPlayingId(null)}
                        onPlay={() => setPlayingId(transcription.id)}
                        className="flex-1"
                        controls
                      />
                    </div>

                    {/* Delete Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDelete(transcription.id)
                      }}
                      disabled={isDeleting}
                      className="ml-4 p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors duration-200 disabled:opacity-50"
                    >
                      {isDeleting ? (
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-red-600" />
                      ) : (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      )}
                    </button>
                  </div>

                  {/* File Info */}
                  <div className="mt-4 text-sm text-slate-500 dark:text-slate-400">
                    <span className="font-medium">File:</span> {transcription.audio_filename}
                    {transcription.duration_seconds && (
                      <>
                        {' • '}
                        <span className="font-medium">Duration:</span>{' '}
                        {transcription.duration_seconds.toFixed(1)}s
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
