/**
 * Main App component for EchoNote
 * Professional enterprise design with mobile-first responsive layout
 */

import { useEffect, useState, useCallback } from 'react'
import { getModels, getTranscriptions, transcribeAudio, getTranscription, isNetworkError } from './api'
import AudioRecorder from './components/AudioRecorder'
import TranscriptionList from './components/TranscriptionList'
import Login from './components/Login'
import SyncIndicator from './components/SyncIndicator'
import BottomNav from './components/BottomNav'
import AIChat from './components/AIChat'
import { useAuth } from './contexts/AuthContext'
import { useOfflineRecording } from './hooks/useOfflineRecording'
import { useTranscriptionPolling } from './hooks/useTranscriptionPolling'
import { Priority, Transcription } from './types'
import { MessageCircle } from 'lucide-react'

function App() {
  const { user, logout, isLoading: authLoading } = useAuth()
  const { isOnline, syncStatus, pendingCount, saveOfflineRecording, triggerSync } = useOfflineRecording()

  // Track previous pending count to detect sync completion
  const [prevPendingCount, setPrevPendingCount] = useState(pendingCount)
  const [transcriptions, setTranscriptions] = useState<Transcription[]>([])
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [priorityFilter, setPriorityFilter] = useState<Priority | null>(null)
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [defaultModel, setDefaultModel] = useState<string>('')

  // Mobile detection
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [totalTranscriptions, setTotalTranscriptions] = useState(0)

  // AI Chat state (desktop only - mobile uses BottomNav)
  const [showDesktopChat, setShowDesktopChat] = useState(false)
  const pageSize = 10 // Should match DEFAULT_PAGE_SIZE in backend

  // Handle window resize for mobile detection
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])


  // Load models on mount (only when user is authenticated)
  useEffect(() => {
    if (user) {
      loadModels()
    }
  }, [user])

  // Load transcriptions on mount and when filter, search, or page changes (only when user is authenticated)
  useEffect(() => {
    if (user) {
      loadTranscriptions()
    }
  }, [priorityFilter, searchQuery, currentPage, user])

  // Reload transcriptions when sync completes (pending count goes from >0 to 0)
  useEffect(() => {
    if (user && prevPendingCount > 0 && pendingCount === 0) {
      console.log('[App] Sync completed - reloading transcriptions')
      loadTranscriptions()
    }
    setPrevPendingCount(pendingCount)
  }, [pendingCount, prevPendingCount, user])

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
      const data = await getTranscriptions(skip, pageSize, priorityFilter, searchQuery || null)
      console.log('[App] loadTranscriptions received data:', data.transcriptions.map(t => ({
        id: t.id,
        status: t.status,
        progress: t.progress,
        text: t.text?.substring(0, 50)
      })))
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
      // Always attempt online transcription first, regardless of navigator.onLine
      // This is more reliable than navigator.onLine which only checks local network
      const extension = audioBlob.type.includes('wav') ? 'wav' : 'webm'
      const filename = `recording-${Date.now()}.${extension}`
      console.log('[App] Attempting online transcription...')

      const result = await transcribeAudio(
        audioBlob,
        filename,
        url,
        model,
        enableDiarization,
        numSpeakers
      )

      console.log('[App] Transcription created:', {
        id: result.id,
        status: result.status,
        progress: result.progress
      })

      // Reload transcriptions to show new item (will be on page 1)
      setCurrentPage(1)
      console.log('[App] Calling loadTranscriptions after transcribeAudio...')
      await loadTranscriptions()

    } catch (err) {
      console.error('Error transcribing audio:', err)

      // Check if this is a network error (server unreachable)
      if (isNetworkError(err)) {
        console.log('[App] Network error detected - saving recording offline')
        // Save recording for later sync
        try {
          await saveOfflineRecording(
            audioBlob,
            url,
            model,
            enableDiarization,
            numSpeakers
          )
          console.log('[App] Recording saved offline for later sync')
          // Don't show error popup - sync indicator already shows offline status
          // setError('Server unreachable - recording saved offline and will sync when connection is restored')
        } catch (saveErr) {
          console.error('[App] Failed to save recording offline:', saveErr)
          // Check if the error is due to corrupted/empty blob
          if (saveErr instanceof Error && saveErr.message.includes('empty or corrupted')) {
            setError('Recording failed - audio data is empty or corrupted. Please try again.')
          } else {
            setError('Failed to save recording offline')
          }
        }
      } else {
        // API error (4xx, 5xx) - show error to user
        setError(err instanceof Error ? err.message : 'Transcription failed')
      }
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

  // Handle transcription completion - fetch and update the completed transcription
  const handleTranscriptionComplete = useCallback(async (id: number) => {
    try {
      const updated = await getTranscription(id)
      setTranscriptions(prev => prev.map(t => t.id === id ? updated : t))
    } catch (error) {
      console.error('Error refreshing completed transcription:', error)
    }
  }, [])

  // Handle status updates from polling - merge into transcriptions state
  const handleStatusUpdate = useCallback((statuses: Map<number, any>) => {
    console.log('[App] handleStatusUpdate called with statuses:', Array.from(statuses.entries()))
    setTranscriptions(prev => {
      console.log('[App] Previous transcriptions state:', prev)
      const updated = prev.map(t => {
        const statusUpdate = statuses.get(t.id)
        if (statusUpdate) {
          console.log(`[App] Updating transcription ${t.id}:`, {
            oldStatus: t.status,
            newStatus: statusUpdate.status,
            oldProgress: t.progress,
            newProgress: statusUpdate.progress
          })
          return {
            ...t,
            status: statusUpdate.status,
            progress: statusUpdate.progress,
            error_message: statusUpdate.error_message
          }
        }
        return t
      })
      console.log('[App] Updated transcriptions state:', updated)
      return updated
    })
  }, [])

  // Get IDs of pending/processing transcriptions for polling
  const pendingIds = transcriptions
    .filter(t => t.status === 'pending' || t.status === 'processing')
    .map(t => t.id)

  console.log('[App] Pending IDs for polling:', pendingIds)
  console.log('[App] All transcriptions:', transcriptions.map(t => ({ id: t.id, status: t.status, progress: t.progress })))

  // Poll for status updates on pending/processing transcriptions
  useTranscriptionPolling(
    pendingIds,
    pendingIds.length > 0,
    handleTranscriptionComplete,
    handleStatusUpdate
  )

  const handleFilterChange = (priority: Priority | null) => {
    setPriorityFilter(priority)
    setCurrentPage(1) // Reset to first page when filter changes
  }

  const handleSearchChange = useCallback((query: string) => {
    setSearchQuery(query)
    setCurrentPage(1) // Reset to first page when search changes
  }, [])

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
      {/* Header - hidden on mobile */}
      {!isMobile && (
        <header className="gradient-header shadow-xl relative overflow-hidden">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 relative z-10">
            <div className="flex items-center justify-between flex-wrap gap-4">
              {/* Logo */}
              <div className="flex items-center">
                <img
                  src="/econote_logo.png"
                  alt="EchoNote Logo"
                  className="h-12 sm:h-16 lg:h-20 w-auto"
                  style={{ filter: 'drop-shadow(0 2px 8px rgba(0, 0, 0, 0.3))' }}
                />
              </div>
              {/* User info and logout */}
              <div className="flex items-center space-x-2 sm:space-x-3">
                {/* Stats badge */}
                <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-md px-4 py-2 rounded-2xl border border-white/20 shadow-lg">
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
      )}

      {/* Main content */}
      <main className={isMobile ? "px-0 py-0" : "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-12"} style={isMobile ? { paddingBottom: '80px' } : {}}>
        {/* Error Message */}
        {error && (
          <div className={isMobile ? "mb-4 p-4 shadow-lg" : "mb-6 sm:mb-8 rounded-2xl p-4 shadow-lg"} style={{ background: 'rgba(228, 76, 101, 0.1)', border: '1px solid rgba(228, 76, 101, 0.3)' }}>
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
        <section className={isMobile ? "mb-4" : "mb-8 sm:mb-12"}>
          <AudioRecorder
            onRecordingComplete={handleRecordingComplete}
            isTranscribing={isTranscribing}
            availableModels={availableModels}
            defaultModel={defaultModel}
            isMobile={isMobile}
          />
        </section>

        {/* Transcriptions List */}
        <section>
          <TranscriptionList
            transcriptions={transcriptions}
            onDelete={handleDelete}
            onUpdate={handleUpdate}
            isMobile={isMobile}
            searchQuery={searchQuery}
            onSearchChange={handleSearchChange}
            priorityFilter={priorityFilter}
            onFilterChange={handleFilterChange}
            totalCount={totalTranscriptions}
            isLoading={isLoading}
          />

          {/* Pagination Controls */}
          {!isLoading && totalTranscriptions > pageSize && (
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
        </section>
      </main>

      {/* Desktop Footer */}
      {!isMobile && (
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
      )}

      {/* Mobile Bottom Navigation */}
      {isMobile && <BottomNav onLogout={logout} />}

      {/* Desktop Floating AI Chat Button */}
      {!isMobile && (
        <button
          onClick={() => setShowDesktopChat(true)}
          style={{
            position: 'fixed',
            bottom: '2rem',
            right: '2rem',
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
            border: 'none',
            boxShadow: '0 4px 20px rgba(102, 126, 234, 0.4), 0 0 40px rgba(118, 75, 162, 0.2)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.3s ease',
            zIndex: 40,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'scale(1.1)'
            e.currentTarget.style.boxShadow = '0 6px 30px rgba(102, 126, 234, 0.6), 0 0 60px rgba(118, 75, 162, 0.3)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'scale(1)'
            e.currentTarget.style.boxShadow = '0 4px 20px rgba(102, 126, 234, 0.4), 0 0 40px rgba(118, 75, 162, 0.2)'
          }}
          aria-label="Open AI Chat"
          title="Chat with AI"
        >
          <MessageCircle
            size={28}
            style={{
              color: 'white',
              strokeWidth: 2
            }}
          />
        </button>
      )}

      {/* Desktop AI Chat Modal */}
      {!isMobile && showDesktopChat && (
        <AIChat
          onClose={() => setShowDesktopChat(false)}
          isMobile={false}
        />
      )}

      {/* Sync Indicator for PWA offline/online status */}
      <SyncIndicator
        isOnline={isOnline}
        syncStatus={syncStatus}
        pendingCount={pendingCount}
        onSyncClick={triggerSync}
        isMobile={isMobile}
      />
    </div>
  )
}

export default App
