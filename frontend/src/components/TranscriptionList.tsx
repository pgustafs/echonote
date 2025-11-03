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
      <div className="glass-card-solid p-16 text-center">
        <div className="w-32 h-32 mx-auto mb-6 bg-gradient-to-br from-vite-500/20 to-electric-500/20 rounded-full flex items-center justify-center">
          <svg
            className="w-16 h-16 text-vite-300"
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
        <h3 className="text-2xl font-bold text-white mb-3">
          No transcriptions yet
        </h3>
        <p className="text-slate-300 text-lg">
          Record your first voice message to get started
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-white drop-shadow-lg">
          Your Transcriptions
        </h2>
        <span className="glass-card px-4 py-2 rounded-full text-white font-semibold">
          {transcriptions.length} {transcriptions.length === 1 ? 'Recording' : 'Recordings'}
        </span>
      </div>

      <div className="space-y-4">
        {transcriptions.map((transcription) => {
          const isExpanded = expandedId === transcription.id
          const isPlaying = playingId === transcription.id
          const isDeleting = deletingId === transcription.id

          return (
            <div
              key={transcription.id}
              className={`glass-card-solid p-6 transition-all duration-300 hover:shadow-2xl hover:scale-[1.01] ${
                isExpanded ? 'ring-2 ring-vite-500/50' : ''
              }`}
            >
              {/* Header */}
              <div
                className="flex items-start justify-between cursor-pointer group"
                onClick={() => toggleExpand(transcription.id)}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center flex-wrap gap-3 mb-3">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-gradient-to-r from-vite-500 to-electric-500 text-white shadow-lg shadow-vite-500/30">
                      #{transcription.id}
                    </span>
                    <span className="text-sm font-medium text-slate-300">
                      {formatDate(transcription.created_at)}
                    </span>
                  </div>
                  <p className="text-white text-lg leading-relaxed">
                    {isExpanded ? transcription.text : truncateText(transcription.text)}
                  </p>
                </div>

                {/* Expand Icon */}
                <div className="ml-4 flex-shrink-0">
                  <div className="w-8 h-8 rounded-full bg-vite-500/20 flex items-center justify-center group-hover:bg-vite-500/30 transition-colors">
                    <svg
                      className={`w-5 h-5 text-vite-300 transition-transform duration-300 ${
                        isExpanded ? 'rotate-180' : ''
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2.5}
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="mt-8 pt-6 border-t border-vite-500/20">
                  <div className="space-y-6">
                    {/* Audio Player */}
                    <div className="flex items-center space-x-4">
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
                        className="w-14 h-14 rounded-2xl bg-gradient-to-br from-vite-600 to-electric-600 hover:from-vite-700 hover:to-electric-700 text-white flex items-center justify-center transition-all duration-300 shadow-lg shadow-vite-500/30 hover:scale-105"
                      >
                        {isPlaying ? (
                          <svg className="w-7 h-7" fill="currentColor" viewBox="0 0 20 20">
                            <path
                              fillRule="evenodd"
                              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z"
                              clipRule="evenodd"
                            />
                          </svg>
                        ) : (
                          <svg className="w-7 h-7 ml-0.5" fill="currentColor" viewBox="0 0 20 20">
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
                        className="flex-1 h-12"
                        controls
                      />
                    </div>

                    {/* File Info & Actions */}
                    <div className="flex items-center justify-between glass-card p-4 rounded-2xl">
                      <div className="flex-1">
                        <div className="text-sm">
                          <span className="font-semibold text-white">
                            {transcription.audio_filename}
                          </span>
                          {transcription.duration_seconds && (
                            <span className="ml-3 text-slate-300">
                              {transcription.duration_seconds.toFixed(1)}s
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Delete Button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(transcription.id)
                        }}
                        disabled={isDeleting}
                        className="ml-4 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 rounded-xl transition-all duration-200 disabled:opacity-50 font-medium hover:scale-105"
                      >
                        {isDeleting ? (
                          <div className="flex items-center space-x-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-2 border-red-600 border-t-transparent" />
                            <span>Deleting...</span>
                          </div>
                        ) : (
                          <div className="flex items-center space-x-2">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                              />
                            </svg>
                            <span>Delete</span>
                          </div>
                        )}
                      </button>
                    </div>
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
