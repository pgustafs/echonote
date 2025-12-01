/**
 * Main App component for EchoNote
 * 2025 Modern design with dark/light theme support
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
import { useTheme } from './contexts/ThemeContext'
import { useOfflineRecording } from './hooks/useOfflineRecording'
import { useTranscriptionPolling } from './hooks/useTranscriptionPolling'
import { Priority, Transcription } from './types'
import { MessageCircle, Sun, Moon } from 'lucide-react'

function App() {
  const { user, logout, isLoading: authLoading } = useAuth()
  const { theme, toggleTheme } = useTheme()
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

  // Infinite scroll state (mobile only)
  const [isLoadingMore, setIsLoadingMore] = useState(false)

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
  // On mobile, skip if currentPage > 1 (handled by infinite scroll)
  useEffect(() => {
    if (user && !(isMobile && currentPage > 1)) {
      loadTranscriptions()
    }
  }, [priorityFilter, searchQuery, currentPage, user, isMobile])

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

  const loadTranscriptions = async (append = false) => {
    try {
      if (!append) {
        setIsLoading(true)
      } else {
        setIsLoadingMore(true)
      }
      setError(null)
      const skip = (currentPage - 1) * pageSize
      const data = await getTranscriptions(skip, pageSize, priorityFilter, searchQuery || null)
      console.log('[App] loadTranscriptions received data:', data.transcriptions.map(t => ({
        id: t.id,
        status: t.status,
        progress: t.progress,
        text: t.text?.substring(0, 50)
      })))

      if (append) {
        // Append to existing transcriptions (for infinite scroll)
        setTranscriptions(prev => [...prev, ...data.transcriptions])
      } else {
        // Replace transcriptions (for normal pagination/filters)
        setTranscriptions(data.transcriptions)
      }
      setTotalTranscriptions(data.total)
    } catch (err) {
      console.error('Error loading transcriptions:', err)
      setError('Failed to load transcriptions')
    } finally {
      if (!append) {
        setIsLoading(false)
      } else {
        setIsLoadingMore(false)
      }
    }
  }

  // Load more items for infinite scroll (mobile only)
  const loadMoreTranscriptions = useCallback(() => {
    if (isMobile && !isLoadingMore && transcriptions.length < totalTranscriptions) {
      console.log('[App] Loading more transcriptions for infinite scroll')
      setCurrentPage(prev => prev + 1)
    }
  }, [isMobile, isLoadingMore, transcriptions.length, totalTranscriptions])

  // Infinite scroll: detect when user scrolls near bottom (mobile only)
  useEffect(() => {
    if (!isMobile) return

    const handleScroll = () => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop
      const scrollHeight = document.documentElement.scrollHeight
      const clientHeight = document.documentElement.clientHeight

      // Trigger load when user is within 300px of bottom
      if (scrollHeight - scrollTop - clientHeight < 300) {
        loadMoreTranscriptions()
      }
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [isMobile, loadMoreTranscriptions])

  // Load more items when page changes (for infinite scroll on mobile)
  useEffect(() => {
    if (user && isMobile && currentPage > 1) {
      loadTranscriptions(true) // append = true
    }
  }, [currentPage, user, isMobile])

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
      {/* Header - 2025 Minimal Design (hidden on mobile) */}
      {!isMobile && (
        <header className="bg-bg">
          <div className="max-w-7xl mx-auto px-12 lg:px-20 py-6 lg:py-8">
            <div className="flex items-center justify-between">
              {/* Brand Name */}
              <div className="flex items-center">
                <h1 className="text-xl lg:text-2xl font-bold text-text-primary tracking-tight">
                  EchoNote
                </h1>
              </div>

              {/* Right side controls */}
              <div className="flex items-center gap-6 lg:gap-8">
                {/* Stats - floating text */}
                <div className="flex items-center gap-2 opacity-80 hover:opacity-100 transition-opacity">
                  <svg className="w-5 h-5 text-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span className="text-text-primary font-medium text-sm">
                    {totalTranscriptions} Recording{totalTranscriptions !== 1 ? 's' : ''}
                  </span>
                </div>

                {/* User info - floating text */}
                <div className="flex items-center gap-2 opacity-80 hover:opacity-100 transition-opacity">
                  <svg className="w-5 h-5 text-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  <span className="text-text-primary text-sm font-medium">{user.username}</span>
                </div>

                {/* Theme toggle - floating icon */}
                <button
                  onClick={toggleTheme}
                  className="header-icon-btn opacity-80 hover:opacity-100"
                  aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                  title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                >
                  {theme === 'dark' ? (
                    <Sun className="w-5 h-5 text-icon" strokeWidth={2} />
                  ) : (
                    <Moon className="w-5 h-5 text-icon" strokeWidth={2} />
                  )}
                </button>

                {/* Logout button - text link */}
                <button
                  onClick={logout}
                  className="text-sm font-medium text-error opacity-80 hover:opacity-100 hover:underline transition-all px-2"
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
      <main className={isMobile ? "px-0 py-0 pb-20" : "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-12"}>
        {/* Error Message */}
        {error && (
          <div className={`alert-error ${isMobile ? 'mb-4' : 'mb-6 sm:mb-8 rounded-card'}`}>
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 flex-shrink-0 mt-0.5 text-error" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <div className="flex-1 min-w-0">
                <p className="alert-error-title">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="icon-button"
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
            availableModels={availableModels}
            defaultModel={defaultModel}
          />

          {/* Pagination Controls - Desktop Only */}
          {!isMobile && !isLoading && totalTranscriptions > pageSize && (
                <div className={isMobile ? "mt-6 p-4 bg-bg-secondary" : "mt-6 sm:mt-8 card p-4 sm:p-6"}>
                  <div className="flex flex-col gap-4">
                    {/* Page info */}
                    <div className="text-sm font-medium text-center sm:text-left text-text-secondary">
                      Showing {Math.min((currentPage - 1) * pageSize + 1, totalTranscriptions)} - {Math.min(currentPage * pageSize, totalTranscriptions)} of {totalTranscriptions}
                    </div>

                    {/* Pagination buttons */}
                    <div className="flex items-center justify-center gap-1 sm:gap-2 flex-wrap">
                      {/* Previous button */}
                      <button
                        onClick={() => handlePageChange(currentPage - 1)}
                        disabled={currentPage === 1}
                        className="btn-secondary min-w-[44px] px-3 sm:px-4"
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
                            className={`min-w-[44px] px-3 sm:px-4 py-2 font-semibold rounded-button transition-all duration-200 flex-shrink-0 ${
                              currentPage === page
                                ? 'btn-accent-blue'
                                : 'btn-secondary'
                            }`}
                          >
                            {page}
                          </button>
                        ))
                      })()}

                      {/* Next button */}
                      <button
                        onClick={() => handlePageChange(currentPage + 1)}
                        disabled={currentPage >= Math.ceil(totalTranscriptions / pageSize)}
                        className="btn-secondary min-w-[44px] px-3 sm:px-4"
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

          {/* Mobile: Loading more indicator for infinite scroll */}
          {isMobile && isLoadingMore && (
            <div className="mt-6 mb-4 flex justify-center items-center gap-3 py-4">
              <div className="w-6 h-6 spinner"></div>
              <span className="text-sm text-text-secondary font-medium">Loading more...</span>
            </div>
          )}
        </section>
      </main>

      {/* Desktop Footer */}
      {!isMobile && (
        <footer className="mt-12 sm:mt-20 border-t border-stroke-subtle bg-bg-secondary">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-text-secondary">
              <p>
                © 2025 EchoNote. AI-powered voice transcription.
              </p>
              <div className="flex items-center gap-4">
                <span>Powered by</span>
                <a
                  href="https://fastapi.tiangolo.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent-blue hover:text-accent-mint transition-colors underline"
                >
                  FastAPI
                </a>
                <span>&</span>
                <a
                  href="https://vitejs.dev/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent-blue hover:text-accent-mint transition-colors underline"
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
          className="fixed bottom-8 right-8 w-14 h-14 rounded-full bg-ai hover:scale-110 transition-transform duration-300 flex items-center justify-center z-40"
          aria-label="Open AI Chat"
          title="Chat with AI"
        >
          <MessageCircle
            size={28}
            className="text-ai-text"
            strokeWidth={2}
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
