/**
 * Mobile full-page detail slider for transcriptions
 * Gmail-style slide-in from right on mobile devices
 */

import { useState } from 'react'
import { Priority, Transcription } from '../types'
import { getAudioUrl } from '../api'
import { ArrowLeft } from 'lucide-react'

interface MobileDetailSliderProps {
  transcription: Transcription | null
  isOpen: boolean
  onClose: () => void
  onDelete: (id: number) => void
  onDownload: (id: number) => void
  onPriorityChange: (id: number, priority: Priority) => void
  onOpenAIActions: (id: number) => void
  isDeleting: boolean
  isDownloading: boolean
  isUpdating: boolean
}

export default function MobileDetailSlider({
  transcription,
  isOpen,
  onClose,
  onDelete,
  onDownload,
  onPriorityChange,
  onOpenAIActions,
  isDeleting,
  isDownloading,
  isUpdating,
}: MobileDetailSliderProps) {
  const [playingId, setPlayingId] = useState<number | null>(null)

  if (!transcription) return null

  const isPlaying = playingId === transcription.id
  const status = transcription.status || 'completed'
  const progress = transcription.progress || null
  const errorMessage = transcription.error_message || null

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

  const getPriorityColor = (priority: Priority): string => {
    switch (priority) {
      case 'high':
        return 'badge-high'
      case 'medium':
        return 'badge-medium'
      case 'low':
        return 'badge-low'
      default:
        return 'bg-slate-100 text-slate-800 border border-slate-200'
    }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className={`mobile-slider-backdrop ${isOpen ? 'mobile-slider-backdrop-open' : ''}`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slider */}
      <div className={`mobile-slider ${isOpen ? 'mobile-slider-open' : ''}`}>
        {/* Header */}
        <div className="mobile-slider-header">
          <button
            onClick={onClose}
            className="touch-target p-2 -ml-2 text-text-primary hover:opacity-70 transition-opacity"
            aria-label="Close"
          >
            <ArrowLeft className="w-6 h-6" strokeWidth={2} />
          </button>
          <h2 className="text-lg font-bold text-text-primary">Transcription #{transcription.id}</h2>
          <div className="w-10"></div>
        </div>

        {/* Content */}
        <div className="mobile-slider-content">
          {/* Metadata */}
          <div className="flex items-center gap-2 mb-4 flex-wrap">
            <span className="badge-id">
              #{transcription.id}
            </span>
            <span className={`badge ${getPriorityColor(transcription.priority)} uppercase tracking-wide`}>
              {transcription.priority}
            </span>
            <span className="text-xs font-medium text-text-tertiary">
              {formatDate(transcription.created_at)}
            </span>
          </div>

          {/* Status Indicators */}
          {status === 'pending' && (
            <div className="mb-4 flex items-center space-x-2 text-yellow-400">
              <svg className="w-5 h-5 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm font-medium">Queued for processing...</span>
            </div>
          )}

          {status === 'processing' && (
            <div className="mb-4 space-y-2">
              <div className="flex items-center space-x-2 text-blue-400">
                <div className="spinner w-4 h-4" />
                <span className="text-sm font-medium">
                  Processing... {progress !== null ? `${progress}%` : ''}
                </span>
              </div>
              {progress !== null && (
                <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-blue-500 h-full transition-all duration-300 ease-out"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              )}
            </div>
          )}

          {status === 'failed' && (
            <div className="mb-4 space-y-2">
              <div className="flex items-center space-x-2 text-red-400">
                <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-sm font-medium">Transcription failed</span>
              </div>
              {errorMessage && (
                <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3">
                  <p className="text-xs text-red-300">{errorMessage}</p>
                </div>
              )}
            </div>
          )}

          {/* Transcription Text */}
          {(status === 'completed' || (status === 'failed' && transcription.text)) && transcription.text && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-text-secondary mb-2 uppercase tracking-wide">Transcription</h3>
              <p className="text-text-primary text-base leading-relaxed">
                {transcription.text}
              </p>
            </div>
          )}

          {(status === 'pending' || status === 'processing') && !transcription.text && (
            <p className="text-text-secondary text-base italic mb-6">
              Transcription will appear here once processing is complete...
            </p>
          )}

          {/* Audio Player */}
          <div className="section-container-mobile mb-4">
            <h3 className="text-xs font-semibold text-text-secondary mb-2 uppercase tracking-wide">Audio</h3>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => {
                  const audio = document.getElementById(
                    `audio-mobile-${transcription.id}`
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
                className="flex-shrink-0 w-11 h-11 rounded-lg bg-accent-blue hover:bg-accent-blue/90 active:bg-accent-blue/80 text-white flex items-center justify-center transition-all duration-200 touch-target"
              >
                {isPlaying ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                ) : (
                  <svg className="w-5 h-5 ml-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </button>

              <audio
                id={`audio-mobile-${transcription.id}`}
                src={getAudioUrl(transcription.id)}
                onEnded={() => setPlayingId(null)}
                onPause={() => setPlayingId(null)}
                onPlay={() => setPlayingId(transcription.id)}
                className="flex-1 min-w-0 h-10"
                controls
              />
            </div>
          </div>

          {/* URL Display */}
          {transcription.url && (
            <div className="section-container-mobile mb-4">
              <h3 className="text-xs font-semibold text-text-secondary mb-2 uppercase tracking-wide">Associated URL</h3>
              <a
                href={transcription.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent-blue hover:text-accent-mint transition-colors underline decoration-accent-blue/30 hover:decoration-accent-mint break-all text-sm"
              >
                {transcription.url}
              </a>
            </div>
          )}

          {/* File Info */}
          <div className="section-container-mobile mb-4">
            <h3 className="text-xs font-semibold text-text-secondary mb-2 uppercase tracking-wide">Audio File</h3>
            <div className="flex items-center flex-wrap gap-2">
              <span className="font-medium text-text-primary text-sm truncate">
                {transcription.audio_filename}
              </span>
              {transcription.duration_seconds && (
                <span className="badge-duration">
                  {transcription.duration_seconds.toFixed(1)}s
                </span>
              )}
            </div>
          </div>

          {/* Priority Selector */}
          <div className="section-container-mobile mb-4">
            <h3 className="text-xs font-semibold text-text-secondary mb-2 uppercase tracking-wide">Priority</h3>
            <div className="flex items-center gap-2">
              <select
                value={transcription.priority}
                onChange={(e) => onPriorityChange(transcription.id, e.target.value as Priority)}
                disabled={isUpdating}
                className="select-field py-2 text-sm min-h-[44px]"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
              {isUpdating && (
                <div className="spinner w-5 h-5" />
              )}
            </div>
          </div>
        </div>

        {/* Bottom Action Bar */}
        <div className="mobile-slider-actions">
          {/* AI Actions Button */}
          {status === 'completed' && transcription.text && (
            <button
              onClick={() => onOpenAIActions(transcription.id)}
              className="mobile-slider-action-btn"
              title="Apply AI actions"
            >
              <span className="text-2xl">✨</span>
              <span className="text-xs font-medium">AI Actions</span>
            </button>
          )}

          {/* Download Button */}
          <button
            onClick={() => onDownload(transcription.id)}
            disabled={isDownloading}
            className="mobile-slider-action-btn"
            title="Download"
          >
            {isDownloading ? (
              <>
                <div className="spinner w-5 h-5" />
                <span className="text-xs font-medium">Loading...</span>
              </>
            ) : (
              <>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                <span className="text-xs font-medium">Download</span>
              </>
            )}
          </button>

          {/* Delete Button */}
          <button
            onClick={() => onDelete(transcription.id)}
            disabled={isDeleting}
            className="mobile-slider-action-btn mobile-slider-action-btn-danger"
            title="Delete"
          >
            {isDeleting ? (
              <>
                <div className="spinner w-5 h-5" />
                <span className="text-xs font-medium">Deleting...</span>
              </>
            ) : (
              <>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
                <span className="text-xs font-medium">Delete</span>
              </>
            )}
          </button>
        </div>
      </div>
    </>
  )
}
