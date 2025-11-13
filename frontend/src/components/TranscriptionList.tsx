/**
 * Transcription list component with expand/collapse and audio playback
 */

import { useState } from 'react'
import { deleteTranscription, downloadTranscription, getAudioUrl, updateTranscriptionPriority } from '../api'
import { Priority, Transcription } from '../types'

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

// Stable style objects defined outside component to prevent re-renders
const mobileInputStyle = {
  padding: '0.625rem 2.5rem',
  fontSize: '0.875rem',
  borderRadius: '0.5rem'
}

const desktopInputStyle = {
  padding: '0.75rem 3rem',
  fontSize: '1rem',
  borderRadius: '0.75rem'
}

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

  return (
    <div className={isMobile ? "space-y-0" : "space-y-4 sm:space-y-6"}>
      {/* Header with count and search - unified for both mobile and desktop */}
      <div className={isMobile ? "px-4 py-3 space-y-3" : "enterprise-card-dark p-6"} style={isMobile ? { background: 'rgba(255, 255, 255, 0.02)' } : undefined}>
        {/* Header with count */}
        <div className={isMobile ? "flex items-center justify-between" : "flex items-center justify-between mb-6"}>
          <h2 className={isMobile ? "text-lg font-bold" : "text-2xl sm:text-3xl font-bold flex items-center space-x-3"} style={{ color: '#E6E8EB' }}>
            {!isMobile && (
              <svg className="w-6 h-6 sm:w-7 sm:h-7" style={{ color: '#5C7CFA' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            )}
            <span>Transcriptions</span>
          </h2>
          <span className={isMobile ? "text-sm font-medium" : "text-base font-semibold"} style={{ color: '#9BA4B5' }}>
            {totalCount} {totalCount === 1 ? 'result' : 'results'}
          </span>
        </div>

        {/* Single unified search bar - conditional styling only */}
        {onSearchChange && (
          <div className={isMobile ? "relative" : "mb-4"}>
            <div className="relative">
              <div className={isMobile ? "absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" : "absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none"}>
                <svg className={isMobile ? "w-4 h-4" : "w-5 h-5"} style={{ color: '#9BA4B5' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                placeholder="Search transcriptions..."
                className="input-field-dark w-full"
                style={isMobile ? mobileInputStyle : desktopInputStyle}
              />
              {searchQuery && (
                <button
                  onClick={() => onSearchChange('')}
                  className={isMobile
                    ? "absolute right-3 top-1/2 -translate-y-1/2 p-1"
                    : "absolute right-4 top-1/2 -translate-y-1/2 p-1.5 rounded-lg transition-all"
                  }
                  style={{ color: '#9BA4B5' }}
                  onMouseEnter={!isMobile ? (e) => e.currentTarget.style.color = '#E6E8EB' : undefined}
                  onMouseLeave={!isMobile ? (e) => e.currentTarget.style.color = '#9BA4B5' : undefined}
                >
                  <svg className={isMobile ? "w-4 h-4" : "w-5 h-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        )}

        {/* Filter buttons - unified for both mobile and desktop */}
        {onFilterChange && (
          <div className={isMobile ? "flex gap-2 overflow-x-auto pb-1 scrollbar-hide" : "flex items-center gap-3"}>
            {!isMobile && <span className="text-sm font-medium" style={{ color: '#9BA4B5' }}>Filter:</span>}
            <div className={isMobile ? "flex gap-2" : "flex gap-2"}>
              <button
                onClick={() => onFilterChange(null)}
                className={isMobile
                  ? "flex-shrink-0 px-3 py-1.5 text-xs font-medium rounded-full transition-all"
                  : "px-4 py-2 text-sm font-medium rounded-xl transition-all"
                }
                style={
                  priorityFilter === null
                    ? isMobile
                      ? {
                          background: 'rgba(92, 124, 250, 0.15)',
                          color: '#5C7CFA',
                          border: '1px solid rgba(92, 124, 250, 0.3)',
                        }
                      : {
                          background: 'linear-gradient(135deg, #5C7CFA 0%, #9775FA 100%)',
                          color: 'white',
                          boxShadow: '0 2px 8px rgba(92, 124, 250, 0.25)',
                        }
                    : {
                        background: 'rgba(255, 255, 255, 0.04)',
                        color: '#9BA4B5',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                      }
                }
              >
                All
              </button>
              <button
                onClick={() => onFilterChange('high')}
                className={isMobile
                  ? "flex-shrink-0 px-3 py-1.5 text-xs font-medium rounded-full transition-all"
                  : "px-4 py-2 text-sm font-medium rounded-xl transition-all"
                }
                style={
                  priorityFilter === 'high'
                    ? isMobile
                      ? {
                          background: 'rgba(228, 76, 101, 0.15)',
                          color: '#FF6B6B',
                          border: '1px solid rgba(228, 76, 101, 0.3)',
                        }
                      : {
                          background: '#E44C65',
                          color: 'white',
                          boxShadow: '0 2px 8px rgba(228, 76, 101, 0.25)',
                        }
                    : isMobile
                    ? {
                        background: 'rgba(255, 255, 255, 0.04)',
                        color: '#9BA4B5',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                      }
                    : {
                        background: 'rgba(255, 107, 107, 0.1)',
                        color: '#FF6B6B',
                        border: '1px solid rgba(255, 107, 107, 0.3)',
                      }
                }
              >
                High
              </button>
              <button
                onClick={() => onFilterChange('medium')}
                className={isMobile
                  ? "flex-shrink-0 px-3 py-1.5 text-xs font-medium rounded-full transition-all"
                  : "px-4 py-2 text-sm font-medium rounded-xl transition-all"
                }
                style={
                  priorityFilter === 'medium'
                    ? isMobile
                      ? {
                          background: 'rgba(249, 168, 38, 0.15)',
                          color: '#F9A826',
                          border: '1px solid rgba(249, 168, 38, 0.3)',
                        }
                      : {
                          background: '#F9A826',
                          color: 'white',
                          boxShadow: '0 2px 8px rgba(249, 168, 38, 0.25)',
                        }
                    : isMobile
                    ? {
                        background: 'rgba(255, 255, 255, 0.04)',
                        color: '#9BA4B5',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                      }
                    : {
                        background: 'rgba(249, 168, 38, 0.1)',
                        color: '#F9A826',
                        border: '1px solid rgba(249, 168, 38, 0.3)',
                      }
                }
              >
                Medium
              </button>
              <button
                onClick={() => onFilterChange('low')}
                className={isMobile
                  ? "flex-shrink-0 px-3 py-1.5 text-xs font-medium rounded-full transition-all"
                  : "px-4 py-2 text-sm font-medium rounded-xl transition-all"
                }
                style={
                  priorityFilter === 'low'
                    ? isMobile
                      ? {
                          background: 'rgba(74, 222, 128, 0.15)',
                          color: '#4ADE80',
                          border: '1px solid rgba(74, 222, 128, 0.3)',
                        }
                      : {
                          background: '#4ADE80',
                          color: 'white',
                          boxShadow: '0 2px 8px rgba(74, 222, 128, 0.25)',
                        }
                    : isMobile
                    ? {
                        background: 'rgba(255, 255, 255, 0.04)',
                        color: '#9BA4B5',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                      }
                    : {
                        background: 'rgba(74, 222, 128, 0.1)',
                        color: '#4ADE80',
                        border: '1px solid rgba(74, 222, 128, 0.3)',
                      }
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
        <div className={isMobile ? "enterprise-card-dark p-8 text-center" : "enterprise-card-dark p-12 sm:p-16 text-center"}>
          <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-4 sm:mb-6 spinner"></div>
          <p className="font-medium text-base sm:text-lg" style={{ color: '#E6E8EB' }}>Loading transcriptions...</p>
        </div>
      ) : transcriptions.length === 0 ? (
        <div className={isMobile ? "enterprise-card-dark p-8 text-center" : "enterprise-card-dark p-12 sm:p-16 text-center"}>
          <div className="w-24 h-24 sm:w-32 sm:h-32 mx-auto mb-6 rounded-full bg-blue-500/10 flex items-center justify-center">
            <svg
              className="w-12 h-12 sm:w-16 sm:h-16 text-blue-400"
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
          <h3 className="text-xl sm:text-2xl font-bold text-white mb-2 sm:mb-3">
            No Transcriptions Found
          </h3>
          <p className="text-slate-300 text-base sm:text-lg">
            {searchQuery || priorityFilter ? 'Try adjusting your search or filters' : 'Record your first voice message to get started'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {transcriptions.map((transcription) => {
          const isExpanded = expandedId === transcription.id
          const isPlaying = playingId === transcription.id
          const isDeleting = deletingId === transcription.id

          return (
            <div
              key={transcription.id}
              className={`enterprise-card-dark ${isMobile ? 'p-4' : 'p-5 sm:p-6'} transition-all duration-200 ${
                isExpanded ? 'ring-2 ring-blue-500/50 shadow-xl' : 'hover:shadow-xl'
              }`}
            >
              {/* Header */}
              <div
                className="flex items-start justify-between cursor-pointer group touch-manipulation min-h-[44px]"
                onClick={() => toggleExpand(transcription.id)}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center flex-wrap gap-2 sm:gap-3 mb-3">
                    <span className="inline-flex items-center px-3 py-1 rounded-md text-xs font-semibold bg-blue-600/20 text-blue-300 border border-blue-500/30">
                      #{transcription.id}
                    </span>
                    <span className={`badge ${getPriorityColor(transcription.priority)} uppercase tracking-wide`}>
                      {transcription.priority}
                    </span>
                    <span className="text-xs sm:text-sm font-medium text-slate-400">
                      {formatDate(transcription.created_at)}
                    </span>
                  </div>
                  <p className="text-white text-base sm:text-lg leading-relaxed">
                    {isExpanded ? transcription.text : truncateText(transcription.text)}
                  </p>
                </div>

                {/* Expand Icon */}
                <div className="ml-3 sm:ml-4 flex-shrink-0 touch-target flex items-center justify-center">
                  <div className="w-10 h-10 rounded-lg bg-slate-700/50 hover:bg-slate-600/50 flex items-center justify-center transition-colors">
                    <svg
                      className={`w-5 h-5 text-blue-400 transition-transform duration-200 ${
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
                </div>
              </div>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="mt-6 pt-6 border-t border-slate-700/50">
                  <div className="space-y-5">
                    {/* Audio Player */}
                    <div className="bg-slate-700/30 rounded-lg p-3 sm:p-4 border border-slate-600/50">
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
                          className="flex-shrink-0 w-11 h-11 sm:w-14 sm:h-14 rounded-lg bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white flex items-center justify-center transition-all duration-200 shadow-sm hover:shadow-md touch-target"
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
                      <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600/50">
                        <div className="flex items-start space-x-3">
                          <svg className="w-5 h-5 flex-shrink-0 text-blue-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                          </svg>
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-medium text-slate-400 mb-1">Associated URL</div>
                            <a
                              href={transcription.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-400 hover:text-blue-300 transition-colors underline decoration-blue-400/30 hover:decoration-blue-300 break-all text-sm"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {transcription.url}
                            </a>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* File Info */}
                    <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600/50">
                      <div className="flex items-center space-x-3">
                        <svg className="w-5 h-5 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                        <div className="flex-1 min-w-0">
                          <div className="text-xs font-medium text-slate-400 mb-1">Audio File</div>
                          <div className="flex items-center flex-wrap gap-2">
                            <span className="font-medium text-white text-sm truncate">
                              {transcription.audio_filename}
                            </span>
                            {transcription.duration_seconds && (
                              <span className="text-xs px-2 py-0.5 rounded bg-blue-600/20 text-blue-300 border border-blue-500/30">
                                {transcription.duration_seconds.toFixed(1)}s
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Priority Selector */}
                    <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600/50">
                      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                        <label className="text-sm font-medium text-white flex items-center space-x-2">
                          <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                          </svg>
                          <span>Priority</span>
                        </label>
                        <div className="flex items-center gap-2">
                          <select
                            value={transcription.priority}
                            onChange={(e) => handlePriorityChange(transcription.id, e.target.value as Priority)}
                            disabled={updatingId === transcription.id}
                            className="input-field-dark py-2 text-sm min-h-[44px]"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <option value="low" className="bg-slate-800">Low</option>
                            <option value="medium" className="bg-slate-800">Medium</option>
                            <option value="high" className="bg-slate-800">High</option>
                          </select>
                          {updatingId === transcription.id && (
                            <div className="spinner w-5 h-5" />
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex justify-start gap-3 pt-2">
                      {/* Download Button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDownload(transcription.id)
                        }}
                        disabled={downloadingId === transcription.id}
                        className="px-4 py-2 text-sm font-semibold rounded-xl transition-all duration-200 flex items-center space-x-2 min-h-[44px]"
                        style={{
                          background: 'rgba(59, 130, 246, 0.2)',
                          color: '#60A5FA',
                          border: '1px solid rgba(59, 130, 246, 0.3)',
                        }}
                        onMouseEnter={(e) => {
                          if (downloadingId !== transcription.id) {
                            e.currentTarget.style.background = 'rgba(59, 130, 246, 0.3)'
                            e.currentTarget.style.color = '#93C5FD'
                          }
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = 'rgba(59, 130, 246, 0.2)'
                          e.currentTarget.style.color = '#60A5FA'
                        }}
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
                        className="btn-danger"
                      >
                        {isDeleting ? (
                          <div className="flex items-center space-x-2">
                            <div className="spinner w-4 h-4" />
                            <span>Deleting...</span>
                          </div>
                        ) : (
                          <div className="flex items-center space-x-2">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
      )}
    </div>
  )
}
