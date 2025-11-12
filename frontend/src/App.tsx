/**
 * Main App component for EchoNote
 * Professional enterprise design with mobile-first responsive layout
 */

import { useEffect, useState } from 'react'
import { getModels, getTranscriptions, transcribeAudio } from './api'
import AudioRecorder from './components/AudioRecorder'
import TranscriptionList from './components/TranscriptionList'
import Login from './components/Login'
import { useAuth } from './contexts/AuthContext'
import { Priority, Transcription } from './types'

function App() {
  const { user, logout, isLoading: authLoading } = useAuth()
  const [transcriptions, setTranscriptions] = useState<Transcription[]>([])
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [priorityFilter, setPriorityFilter] = useState<Priority | null>(null)
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [defaultModel, setDefaultModel] = useState<string>('')

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [totalTranscriptions, setTotalTranscriptions] = useState(0)
  const pageSize = 10 // Should match DEFAULT_PAGE_SIZE in backend

  // Load models on mount (only when user is authenticated)
  useEffect(() => {
    if (user) {
      loadModels()
    }
  }, [user])

  // Load transcriptions on mount and when filter or page changes (only when user is authenticated)
  useEffect(() => {
    if (user) {
      loadTranscriptions()
    }
  }, [priorityFilter, currentPage, user])

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
      const skip = (currentPage - 1) * pageSize
      const data = await getTranscriptions(skip, pageSize, priorityFilter)
      setTranscriptions(data.transcriptions)
      setTotalTranscriptions(data.total)
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
      await transcribeAudio(
        audioBlob,
        filename,
        url,
        model,
        enableDiarization,
        numSpeakers
      )

      // Reload transcriptions to show new item (will be on page 1)
      setCurrentPage(1)
      loadTranscriptions()
    } catch (err) {
      console.error('Error transcribing audio:', err)
      setError(err instanceof Error ? err.message : 'Transcription failed')
    } finally {
      setIsTranscribing(false)
    }
  }

  const handleDelete = () => {
    // Reload current page after deletion
    loadTranscriptions()
  }

  const handleUpdate = (id: number, updated: Transcription) => {
    setTranscriptions(transcriptions.map((t) => t.id === id ? updated : t))
  }

  const handleFilterChange = (priority: Priority | null) => {
    setPriorityFilter(priority)
    setCurrentPage(1) // Reset to first page when filter changes
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // Show loading spinner while checking authentication
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-16 h-16 spinner"></div>
      </div>
    )
  }

  // Show login page if not authenticated
  if (!user) {
    return <Login />
  }

  return (
    <div className="min-h-screen">
      {/* Header with glass effect matching footer */}
      <header className="gradient-header shadow-xl relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 relative z-10">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center space-x-3 sm:space-x-4">
              {/* Icon */}
              <div className="w-12 h-12 sm:w-14 sm:h-14 bg-white/10 backdrop-blur-md rounded-2xl shadow-lg flex items-center justify-center flex-shrink-0 border border-white/20">
                <svg
                  className="w-7 h-7 sm:w-8 sm:h-8 text-white"
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
                <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-white" style={{ textShadow: '0 2px 8px rgba(0, 0, 0, 0.3)' }}>
                  EchoNote
                </h1>
                <p className="text-white/90 text-sm sm:text-base mt-1">
                  AI-Powered Voice Transcription
                </p>
              </div>
            </div>
            {/* User info and logout */}
            <div className="flex items-center space-x-2 sm:space-x-3">
              {/* Stats badge - hidden on mobile */}
              <div className="hidden sm:flex items-center space-x-2 bg-white/10 backdrop-blur-md px-4 py-2 rounded-2xl border border-white/20 shadow-lg">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span className="text-white font-semibold">{totalTranscriptions} Recording{totalTranscriptions !== 1 ? 's' : ''}</span>
              </div>

              {/* User info */}
              <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-md px-3 sm:px-4 py-2 rounded-2xl border border-white/20 shadow-lg">
                <svg className="w-4 h-4 sm:w-5 sm:h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span className="text-white text-sm sm:text-base font-medium">{user.username}</span>
              </div>

              {/* Logout button */}
              <button
                onClick={logout}
                className="px-3 sm:px-4 py-2 text-xs sm:text-sm font-semibold rounded-2xl transition-all duration-200 min-h-[44px]"
                style={{
                  background: 'rgba(228, 76, 101, 0.2)',
                  color: '#FF6B6B',
                  border: '1px solid rgba(228, 76, 101, 0.3)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(228, 76, 101, 0.3)'
                  e.currentTarget.style.color = '#FF8787'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(228, 76, 101, 0.2)'
                  e.currentTarget.style.color = '#FF6B6B'
                }}
                title="Sign out"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-12">
        {/* Error Message */}
        {error && (
          <div className="mb-6 sm:mb-8 rounded-2xl p-4 shadow-lg" style={{ background: 'rgba(228, 76, 101, 0.1)', border: '1px solid rgba(228, 76, 101, 0.3)' }}>
            <div className="flex items-start space-x-3">
              <svg className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: '#E44C65' }} fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium" style={{ color: '#E44C65' }}>{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="flex-shrink-0 touch-target transition-colors"
                style={{ color: '#E44C65' }}
                onMouseEnter={(e) => e.currentTarget.style.color = '#d43d56'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#E44C65'}
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
              <label className="font-semibold text-sm sm:text-base lg:text-lg flex items-center space-x-2" style={{ color: '#E6E8EB' }}>
                <svg className="w-4 h-4 sm:w-5 sm:h-5" style={{ color: '#5C7CFA' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                </svg>
                <span>Filter by Priority</span>
              </label>
              <div className="grid grid-cols-2 sm:flex sm:flex-wrap gap-2">
                <button
                  onClick={() => handleFilterChange(null)}
                  className="px-4 py-2.5 font-medium transition-all duration-200 min-h-[44px] touch-manipulation text-sm sm:text-base"
                  style={priorityFilter === null ? {
                    background: 'linear-gradient(135deg, #5C7CFA 0%, #9775FA 100%)',
                    color: 'white',
                    borderRadius: '1.5rem',
                    boxShadow: '0 4px 12px rgba(92, 124, 250, 0.25)'
                  } : {
                    background: 'rgba(255, 255, 255, 0.04)',
                    color: '#9BA4B5',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '1.5rem'
                  }}
                  onMouseEnter={(e) => {
                    if (priorityFilter !== null) {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)'
                      e.currentTarget.style.color = '#E6E8EB'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (priorityFilter !== null) {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)'
                      e.currentTarget.style.color = '#9BA4B5'
                    }
                  }}
                >
                  All
                </button>
                <button
                  onClick={() => handleFilterChange('high')}
                  className="px-4 py-2.5 font-medium transition-all duration-200 min-h-[44px] touch-manipulation text-sm sm:text-base"
                  style={priorityFilter === 'high' ? {
                    background: '#E44C65',
                    color: 'white',
                    borderRadius: '1.5rem',
                    boxShadow: '0 4px 12px rgba(228, 76, 101, 0.25)'
                  } : {
                    background: 'rgba(255, 107, 107, 0.1)',
                    color: '#FF6B6B',
                    border: '1px solid rgba(255, 107, 107, 0.3)',
                    borderRadius: '1.5rem'
                  }}
                  onMouseEnter={(e) => {
                    if (priorityFilter !== 'high') {
                      e.currentTarget.style.background = 'rgba(255, 107, 107, 0.2)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (priorityFilter !== 'high') {
                      e.currentTarget.style.background = 'rgba(255, 107, 107, 0.1)'
                    }
                  }}
                >
                  High
                </button>
                <button
                  onClick={() => handleFilterChange('medium')}
                  className="px-4 py-2.5 font-medium transition-all duration-200 min-h-[44px] touch-manipulation text-sm sm:text-base"
                  style={priorityFilter === 'medium' ? {
                    background: '#F9A826',
                    color: 'white',
                    borderRadius: '1.5rem',
                    boxShadow: '0 4px 12px rgba(249, 168, 38, 0.25)'
                  } : {
                    background: 'rgba(249, 168, 38, 0.1)',
                    color: '#F9A826',
                    border: '1px solid rgba(249, 168, 38, 0.3)',
                    borderRadius: '1.5rem'
                  }}
                  onMouseEnter={(e) => {
                    if (priorityFilter !== 'medium') {
                      e.currentTarget.style.background = 'rgba(249, 168, 38, 0.2)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (priorityFilter !== 'medium') {
                      e.currentTarget.style.background = 'rgba(249, 168, 38, 0.1)'
                    }
                  }}
                >
                  Medium
                </button>
                <button
                  onClick={() => handleFilterChange('low')}
                  className="px-4 py-2.5 font-medium transition-all duration-200 min-h-[44px] touch-manipulation text-sm sm:text-base"
                  style={priorityFilter === 'low' ? {
                    background: '#4ADE80',
                    color: 'white',
                    borderRadius: '1.5rem',
                    boxShadow: '0 4px 12px rgba(74, 222, 128, 0.25)'
                  } : {
                    background: 'rgba(74, 222, 128, 0.1)',
                    color: '#4ADE80',
                    border: '1px solid rgba(74, 222, 128, 0.3)',
                    borderRadius: '1.5rem'
                  }}
                  onMouseEnter={(e) => {
                    if (priorityFilter !== 'low') {
                      e.currentTarget.style.background = 'rgba(74, 222, 128, 0.2)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (priorityFilter !== 'low') {
                      e.currentTarget.style.background = 'rgba(74, 222, 128, 0.1)'
                    }
                  }}
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
              <p className="font-medium text-base sm:text-lg" style={{ color: '#E6E8EB' }}>Loading transcriptions...</p>
            </div>
          ) : (
            <>
              <TranscriptionList
                transcriptions={transcriptions}
                onDelete={handleDelete}
                onUpdate={handleUpdate}
              />

              {/* Pagination Controls */}
              {totalTranscriptions > pageSize && (
                <div className="mt-6 sm:mt-8 enterprise-card-dark p-4 sm:p-6">
                  <div className="flex flex-col gap-4">
                    {/* Page info */}
                    <div className="text-sm font-medium text-center sm:text-left" style={{ color: '#9BA4B5' }}>
                      Showing {Math.min((currentPage - 1) * pageSize + 1, totalTranscriptions)} - {Math.min(currentPage * pageSize, totalTranscriptions)} of {totalTranscriptions}
                    </div>

                    {/* Pagination buttons */}
                    <div className="flex items-center justify-center gap-1 sm:gap-2 flex-wrap">
                      {/* Previous button */}
                      <button
                        onClick={() => handlePageChange(currentPage - 1)}
                        disabled={currentPage === 1}
                        className="btn-secondary min-w-[44px] min-h-[44px] px-3 sm:px-4 py-2 flex-shrink-0"
                        aria-label="Previous page"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                      </button>

                      {/* Page numbers */}
                      {(() => {
                        const totalPages = Math.ceil(totalTranscriptions / pageSize)
                        const pages: number[] = []

                        // Show max 3 page numbers on mobile, 5 on desktop
                        const maxPages = window.innerWidth < 640 ? 3 : 5
                        const sidePages = Math.floor((maxPages - 1) / 2)

                        let startPage = Math.max(1, currentPage - sidePages)
                        let endPage = Math.min(totalPages, currentPage + sidePages)

                        // Adjust if at edges
                        if (currentPage <= sidePages + 1) {
                          endPage = Math.min(maxPages, totalPages)
                        }
                        if (currentPage >= totalPages - sidePages) {
                          startPage = Math.max(1, totalPages - maxPages + 1)
                        }

                        for (let i = startPage; i <= endPage; i++) {
                          pages.push(i)
                        }

                        return pages.map(page => (
                          <button
                            key={page}
                            onClick={() => handlePageChange(page)}
                            className="min-w-[44px] min-h-[44px] px-3 sm:px-4 py-2 font-semibold transition-all duration-200 flex-shrink-0"
                            style={currentPage === page ? {
                              background: 'linear-gradient(135deg, #5C7CFA 0%, #9775FA 100%)',
                              color: 'white',
                              borderRadius: '1.5rem',
                              boxShadow: '0 4px 12px rgba(92, 124, 250, 0.25)'
                            } : {
                              background: 'rgba(255, 255, 255, 0.04)',
                              color: '#9BA4B5',
                              border: '1px solid rgba(255, 255, 255, 0.08)',
                              borderRadius: '1.5rem'
                            }}
                            onMouseEnter={(e) => {
                              if (currentPage !== page) {
                                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)'
                                e.currentTarget.style.color = '#E6E8EB'
                              }
                            }}
                            onMouseLeave={(e) => {
                              if (currentPage !== page) {
                                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)'
                                e.currentTarget.style.color = '#9BA4B5'
                              }
                            }}
                          >
                            {page}
                          </button>
                        ))
                      })()}

                      {/* Next button */}
                      <button
                        onClick={() => handlePageChange(currentPage + 1)}
                        disabled={currentPage >= Math.ceil(totalTranscriptions / pageSize)}
                        className="btn-secondary min-w-[44px] min-h-[44px] px-3 sm:px-4 py-2 flex-shrink-0"
                        aria-label="Next page"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="mt-12 sm:mt-20" style={{ borderTop: '1px solid rgba(255, 255, 255, 0.08)', background: 'rgba(255, 255, 255, 0.02)' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm">
            <p style={{ color: '#9BA4B5' }}>
              © 2025 EchoNote. AI-powered voice transcription.
            </p>
            <div className="flex items-center space-x-4" style={{ color: '#9BA4B5' }}>
              <span>Powered by</span>
              <a
                href="https://fastapi.tiangolo.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="transition-colors underline"
                style={{ color: '#5C7CFA', textDecorationColor: 'rgba(92, 124, 250, 0.3)' }}
                onMouseEnter={(e) => e.currentTarget.style.color = '#4ADEDE'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#5C7CFA'}
              >
                FastAPI
              </a>
              <span>&</span>
              <a
                href="https://vitejs.dev/"
                target="_blank"
                rel="noopener noreferrer"
                className="transition-colors underline"
                style={{ color: '#5C7CFA', textDecorationColor: 'rgba(92, 124, 250, 0.3)' }}
                onMouseEnter={(e) => e.currentTarget.style.color = '#4ADEDE'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#5C7CFA'}
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
