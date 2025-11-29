/**
 * Transcription list component with expand/collapse and audio playback
 */

import { useState } from 'react'
import { deleteTranscription, downloadTranscription, getAudioUrl, updateTranscriptionPriority, executeAIAction } from '../api'
import { Priority, Transcription } from '../types'
import AIActionsDrawer from './AIActionsDrawer'
import AIResultModal from './AIResultModal'
import type { AIAction, AIActionResponse } from '../types'

interface TranscriptionListProps {
  transcriptions: Transcription[]
  onDelete: (id: number) => void
  onUpdate: (id: number, updated: Transcription) => void
  isMobile?: boolean
  searchQuery?: string
  onSearchChange?: (query: string) => void
  priorityFilter?: Priority | null
  onFilterChange?: (priority: Priority | null) => void
  totalCount?: number
  isLoading?: boolean
}

// No inline styles needed - all handled by Tailwind theme classes

export default function TranscriptionList({
  transcriptions,
  onDelete,
  onUpdate,
  isMobile = false,
  searchQuery = '',
  onSearchChange,
  priorityFilter = null,
  onFilterChange,
  totalCount = 0,
  isLoading = false
}: TranscriptionListProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [playingId, setPlayingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [updatingId, setUpdatingId] = useState<number | null>(null)
  const [downloadingId, setDownloadingId] = useState<number | null>(null)

  const [aiDrawerOpen, setAiDrawerOpen] = useState(false)
  const [aiResultModalOpen, setAiResultModalOpen] = useState(false)
  const [selectedTranscriptionId, setSelectedTranscriptionId] = useState<number | null>(null)
  const [selectedAction, setSelectedAction] = useState<AIAction | null>(null)
  const [aiResult, setAiResult] = useState<AIActionResponse | null>(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiError, setAiError] = useState<string | null>(null)

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

  const handlePriorityChange = async (id: number, newPriority: Priority) => {
    setUpdatingId(id)
    try {
      const updated = await updateTranscriptionPriority(id, newPriority)
      onUpdate(id, updated)
    } catch (error) {
      console.error('Error updating priority:', error)
      alert('Failed to update priority')
    } finally {
      setUpdatingId(null)
    }
  }

  const handleDownload = async (id: number) => {
    setDownloadingId(id)
    try {
      await downloadTranscription(id)
    } catch (error) {
      console.error('Error downloading transcription:', error)
      alert('Failed to download transcription')
    } finally {
      setDownloadingId(null)
    }
  }

  const handleOpenAIActions = (transcriptionId: number) => {
    setSelectedTranscriptionId(transcriptionId)
    setAiDrawerOpen(true)
  }

  const handleSelectAIAction = async (action: AIAction) => {
    if (!selectedTranscriptionId) return

    setSelectedAction(action)
    setAiDrawerOpen(false)
    setAiResultModalOpen(true)
    setAiLoading(true)
    setAiError(null)
    setAiResult(null)

    try {
      const result = await executeAIAction(action.endpoint, {
        transcription_id: selectedTranscriptionId,
      })
      setAiResult(result)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to execute AI action'
      setAiError(errorMessage)
      console.error('AI action error:', error)
    } finally {
      setAiLoading(false)
    }
  }

  const handleRegenerateAI = () => {
    if (selectedAction) {
      handleSelectAIAction(selectedAction)
    }
  }

  const handleCloseAIResult = () => {
    setAiResultModalOpen(false)
    setSelectedAction(null)
    setAiResult(null)
    setAiError(null)
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

  const getStatusDisplay = (transcription: Transcription) => {
    // Status is already updated by polling in App.tsx
    const status = transcription.status || 'completed'
    const progress = transcription.progress || null
    const errorMessage = transcription.error_message || null

    console.log(`[TranscriptionList] getStatusDisplay for ID ${transcription.id}:`, {
      status,
      progress,
      errorMessage,
      rawStatus: transcription.status,
      rawProgress: transcription.progress
    })

    return { status, progress, errorMessage }
  }

  return (
    <div className={isMobile ? "space-y-0" : "space-y-8 sm:space-y-12"}>
      {/* Header with count and search - 2025 theme */}
      <div className={isMobile ? "px-4 py-3 space-y-3" : "card p-6"}>
        {/* Header with count */}
        <div className={isMobile ? "flex items-center justify-between" : "flex items-center justify-between mb-6"}>
          <h2 className={isMobile ? "text-lg font-bold text-text-primary" : "text-2xl sm:text-3xl font-bold flex items-center space-x-3 text-text-primary"}>
            {!isMobile && (
              <svg className="w-6 h-6 sm:w-7 sm:h-7 text-accent-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            )}
            <span>Transcriptions</span>
          </h2>
          <span className={isMobile ? "text-sm font-medium text-text-secondary" : "text-base font-semibold text-text-secondary"}>
            {totalCount} {totalCount === 1 ? 'result' : 'results'}
          </span>
        </div>

        {/* Search bar - 2025 theme */}
        {onSearchChange && (
          <div className={isMobile ? "relative" : "mb-4"}>
            <div className="relative">
              <div className={isMobile ? "absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" : "absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none"}>
                <svg className={isMobile ? "w-4 h-4 text-text-secondary" : "w-5 h-5 text-text-secondary"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                placeholder="Search transcriptions..."
                className={isMobile ? "input-field w-full pl-10 pr-10 text-sm" : "input-field w-full pl-12 pr-12"}
              />
              {searchQuery && (
                <button
                  onClick={() => onSearchChange('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-lg transition-colors text-text-secondary hover:text-text-primary"
                >
                  <svg className={isMobile ? "w-4 h-4" : "w-5 h-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        )}

        {/* Filter buttons - 2025 theme */}
        {onFilterChange && (
          <div className={isMobile ? "flex gap-2 overflow-x-auto pb-1 scrollbar-hide" : "flex items-center gap-3"}>
            {!isMobile && <span className="text-sm font-medium text-text-secondary">Filter:</span>}
            <div className="flex gap-2">
              <button
                onClick={() => onFilterChange(null)}
                className={isMobile
                  ? (priorityFilter === null ? "filter-btn-mobile-active" : "filter-btn-mobile")
                  : (priorityFilter === null ? "filter-btn-active" : "filter-btn")
                }
              >
                All
              </button>
              <button
                onClick={() => onFilterChange('high')}
                className={isMobile
                  ? (priorityFilter === 'high' ? "filter-btn-mobile-active" : "filter-btn-mobile")
                  : (priorityFilter === 'high' ? "filter-btn-active" : "filter-btn")
                }
              >
                High
              </button>
              <button
                onClick={() => onFilterChange('medium')}
                className={isMobile
                  ? (priorityFilter === 'medium' ? "filter-btn-mobile-active" : "filter-btn-mobile")
                  : (priorityFilter === 'medium' ? "filter-btn-active" : "filter-btn")
                }
              >
                Medium
              </button>
              <button
                onClick={() => onFilterChange('low')}
                className={isMobile
                  ? (priorityFilter === 'low' ? "filter-btn-mobile-active" : "filter-btn-mobile")
                  : (priorityFilter === 'low' ? "filter-btn-active" : "filter-btn")
                }
              >
                Low
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Loading state */}
      {isLoading ? (
        <div className={isMobile ? "card p-8 text-center" : "card p-12 sm:p-16 text-center"}>
          <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-4 sm:mb-6 spinner"></div>
          <p className="font-medium text-base sm:text-lg text-text-primary">Loading transcriptions...</p>
        </div>
      ) : transcriptions.length === 0 ? (
        <div className={isMobile ? "card p-8 text-center" : "card p-12 sm:p-16 text-center"}>
          <div className="w-24 h-24 sm:w-32 sm:h-32 mx-auto mb-6 rounded-full flex items-center justify-center empty-state-icon-bg">
            <svg
              className="w-12 h-12 sm:w-16 sm:h-16 text-accent-blue"
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
          <h3 className="text-xl sm:text-2xl font-bold text-text-primary mb-2 sm:mb-3">
            No Transcriptions Found
          </h3>
          <p className="text-text-secondary text-base sm:text-lg">
            {searchQuery || priorityFilter ? 'Try adjusting your search or filters' : 'Record your first voice message to get started'}
          </p>
        </div>
      ) : (
        <div className={isMobile ? "space-y-2.5" : "space-y-6 sm:space-y-8"}>
          {transcriptions.map((transcription) => {
          const isExpanded = expandedId === transcription.id
          const isPlaying = playingId === transcription.id
          const isDeleting = deletingId === transcription.id
          const { status, progress, errorMessage } = getStatusDisplay(transcription)

          return (
            <div
              key={transcription.id}
              className={isMobile
                ? `card-transcription-mobile ${isExpanded ? 'ring-2 ring-accent-blue/50' : ''}`
                : `card-transcription transition-all duration-200 ${isExpanded ? 'ring-2 ring-accent-blue/50' : ''}`
              }
            >
              {/* Header */}
              <div
                className="flex items-start justify-between cursor-pointer group touch-manipulation min-h-[44px]"
                onClick={() => toggleExpand(transcription.id)}
              >
                <div className="flex-1 min-w-0">
                  {/* Metadata row - single horizontal line for mobile */}
                  <div className={isMobile
                    ? "flex items-center gap-2 mb-2 flex-wrap"
                    : "flex items-center flex-wrap gap-2 sm:gap-3 mb-3"
                  }>
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
                    <div className="mb-3 flex items-center space-x-2 text-yellow-400">
                      <svg className="w-5 h-5 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-sm font-medium">⏳ Queued for processing...</span>
                    </div>
                  )}

                  {status === 'processing' && (
                    <div className="mb-3 space-y-2">
                      <div className="flex items-center space-x-2 text-blue-400">
                        <div className="spinner w-4 h-4" />
                        <span className="text-sm font-medium">
                          🔄 Processing... {progress !== null ? `${progress}%` : ''}
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
                    <div className="mb-3 space-y-2">
                      <div className="flex items-center space-x-2 text-red-400">
                        <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-sm font-medium">❌ Transcription failed</span>
                      </div>
                      {errorMessage && (
                        <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3">
                          <p className="text-xs text-red-300">{errorMessage}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Show transcription text only if completed or failed with text */}
                  {(status === 'completed' || (status === 'failed' && transcription.text)) && transcription.text && (
                    <p className={isMobile
                      ? `text-text-primary text-sm leading-relaxed ${!isExpanded ? 'preview-text' : ''}`
                      : "text-text-primary text-base sm:text-lg leading-relaxed"
                    }>
                      {isExpanded || isMobile ? transcription.text : truncateText(transcription.text)}
                    </p>
                  )}

                  {/* Show placeholder for pending/processing without text */}
                  {(status === 'pending' || status === 'processing') && !transcription.text && (
                    <p className="text-text-secondary text-base sm:text-lg italic">
                      Transcription will appear here once processing is complete...
                    </p>
                  )}
                </div>

                {/* Expand Icon - Floating on mobile, boxed on desktop */}
                <div className="ml-3 sm:ml-4 flex-shrink-0 touch-target flex items-center justify-center">
                  {isMobile ? (
                    <svg
                      className={`w-5 h-5 text-icon expand-button transition-transform duration-200 ${
                        isExpanded ? 'rotate-180' : ''
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  ) : (
                    <div className="expand-button w-10 h-10 rounded-lg flex items-center justify-center">
                      <svg
                        className={`w-5 h-5 text-accent-blue transition-transform duration-200 ${
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
                  )}
                </div>
              </div>

              {/* Expanded Content */}
              {isExpanded && (
                <div className={isMobile ? "divider-mobile" : "mt-6 pt-6 divider-top"}>
                  <div className={isMobile ? "space-y-4" : "space-y-5"}>
                    {/* Audio Player */}
                    <div className={isMobile ? "audio-player-mobile" : "section-container p-3 sm:p-4"}>
                      <div className="flex items-center space-x-2 sm:space-x-3">
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
                          className="flex-shrink-0 w-11 h-11 sm:w-14 sm:h-14 rounded-lg bg-accent-blue hover:bg-accent-blue/90 active:bg-accent-blue/80 text-white flex items-center justify-center transition-all duration-200 touch-target"
                        >
                          {isPlaying ? (
                            <svg className="w-5 h-5 sm:w-7 sm:h-7" fill="currentColor" viewBox="0 0 20 20">
                              <path
                                fillRule="evenodd"
                                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z"
                                clipRule="evenodd"
                              />
                            </svg>
                          ) : (
                            <svg className="w-5 h-5 sm:w-7 sm:h-7 ml-0.5" fill="currentColor" viewBox="0 0 20 20">
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
                          className="flex-1 min-w-0 h-10 sm:h-12"
                          controls
                        />
                      </div>
                    </div>

                    {/* URL Display */}
                    {transcription.url && (
                      <div className={isMobile ? "section-container-mobile" : "section-container"}>
                        <div className="flex items-start space-x-3">
                          <svg className="w-5 h-5 flex-shrink-0 text-accent-blue mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                          </svg>
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-medium text-text-tertiary mb-1">Associated URL</div>
                            <a
                              href={transcription.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-accent-blue hover:text-accent-mint transition-colors underline decoration-accent-blue/30 hover:decoration-accent-mint break-all text-sm"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {transcription.url}
                            </a>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* File Info */}
                    <div className={isMobile ? "section-container-mobile" : "section-container"}>
                      <div className="flex items-center space-x-3">
                        <svg className="w-5 h-5 text-accent-blue flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                        <div className="flex-1 min-w-0">
                          <div className="text-xs font-medium text-text-tertiary mb-1">Audio File</div>
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
                      </div>
                    </div>

                    {/* Priority Selector */}
                    <div className={isMobile ? "section-container-mobile" : "section-container"}>
                      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                        <label className="text-sm font-medium text-text-primary flex items-center space-x-2">
                          <svg className="w-4 h-4 text-accent-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                          </svg>
                          <span>Priority</span>
                        </label>
                        <div className="flex items-center gap-2">
                          <select
                            value={transcription.priority}
                            onChange={(e) => handlePriorityChange(transcription.id, e.target.value as Priority)}
                            disabled={updatingId === transcription.id}
                            className="select-field py-2 text-sm min-h-[44px]"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <option value="low">Low</option>
                            <option value="medium">Medium</option>
                            <option value="high">High</option>
                          </select>
                          {updatingId === transcription.id && (
                            <div className="spinner w-5 h-5" />
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex justify-start gap-3 pt-2 flex-wrap">
                      {/* AI Actions Button */}
                      {status === 'completed' && transcription.text && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleOpenAIActions(transcription.id)
                          }}
                          className="btn-ai min-h-[44px] flex items-center space-x-2"
                          title="Apply AI actions to this transcription"
                        >
                          <span className="text-lg">✨</span>
                          <span>AI Actions</span>
                        </button>
                      )}

                      {/* Download Button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDownload(transcription.id)
                        }}
                        disabled={downloadingId === transcription.id}
                        className="btn-secondary min-h-[44px] flex items-center space-x-2"
                        title="Download as ZIP with WAV audio and config.json"
                      >
                        {downloadingId === transcription.id ? (
                          <>
                            <div className="spinner w-4 h-4" />
                            <span>Downloading...</span>
                          </>
                        ) : (
                          <>
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                              />
                            </svg>
                            <span>Download</span>
                          </>
                        )}
                      </button>

                      {/* Delete Button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(transcription.id)
                        }}
                        disabled={isDeleting}
                        className="btn-danger min-h-[44px] flex items-center space-x-2"
                      >
                        {isDeleting ? (
                          <>
                            <div className="spinner w-4 h-4" />
                            <span>Deleting...</span>
                          </>
                        ) : (
                          <>
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                              />
                            </svg>
                            <span>Delete</span>
                          </>
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
      )}

      {/* AI Actions Drawer */}
      <AIActionsDrawer
        isOpen={aiDrawerOpen}
        onClose={() => setAiDrawerOpen(false)}
        onSelectAction={handleSelectAIAction}
        isMobile={isMobile}
      />

      {/* AI Result Modal */}
      <AIResultModal
        isOpen={aiResultModalOpen}
        onClose={handleCloseAIResult}
        action={selectedAction}
        result={aiResult}
        isLoading={aiLoading}
        error={aiError}
        onRegenerate={handleRegenerateAI}
        isMobile={isMobile}
      />
    </div>
  )
}
