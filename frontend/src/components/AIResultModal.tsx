/**
 * AI Result Modal Component
 *
 * Displays the result of an AI action with copy, regenerate, and improve options
 * Supports session management for multi-turn conversations
 */

import { useState, useEffect } from 'react'
import type { AIActionResponse, AIAction } from '../types'
import { cleanupAISession, improveAIAction } from '../api'

interface AIResultModalProps {
  isOpen: boolean
  onClose: () => void
  action: AIAction | null
  result: AIActionResponse | null
  isLoading: boolean
  error: string | null
  onRegenerate?: () => void
  isMobile?: boolean
}

export default function AIResultModal({
  isOpen,
  onClose,
  action,
  result,
  isLoading,
  error,
  onRegenerate,
  isMobile = false,
}: AIResultModalProps) {
  const [copied, setCopied] = useState(false)
  const [showImprove, setShowImprove] = useState(false)
  const [improveInstructions, setImproveInstructions] = useState('')
  const [isImproving, setIsImproving] = useState(false)
  const [improveError, setImproveError] = useState<string | null>(null)
  const [currentResult, setCurrentResult] = useState<AIActionResponse | null>(result)

  // Update current result when prop changes
  useEffect(() => {
    setCurrentResult(result)
  }, [result])

  // Cleanup session when modal closes
  useEffect(() => {
    if (!isOpen) {
      // Reset improve state
      setShowImprove(false)
      setImproveInstructions('')
      setImproveError(null)

      // Cleanup session if exists
      if (currentResult?.session_id) {
        cleanupAISession(currentResult.session_id).catch(err => {
          console.warn('Failed to cleanup session:', err)
        })
      }
    }
  }, [isOpen, currentResult?.session_id])

  if (!isOpen) return null

  const handleCopy = async () => {
    if (!currentResult?.message) return

    try {
      await navigator.clipboard.writeText(currentResult.message)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
      alert('Failed to copy to clipboard')
    }
  }

  const handleImprove = async () => {
    if (!improveInstructions.trim()) {
      setImproveError('Please provide instructions for improvement')
      return
    }

    if (!currentResult?.session_id) {
      setImproveError('Session expired. Please regenerate the result.')
      return
    }

    if (!currentResult?.action_id) {
      setImproveError('Unable to improve: missing action ID')
      return
    }

    setIsImproving(true)
    setImproveError(null)

    try {
      const improvedResult = await improveAIAction(currentResult.action_id, {
        session_id: currentResult.session_id,
        instructions: improveInstructions.trim()
      })

      // Update current result with improved version
      setCurrentResult(improvedResult)
      setImproveInstructions('')
      setShowImprove(false)
    } catch (err) {
      console.error('Failed to improve:', err)
      setImproveError(err instanceof Error ? err.message : 'Failed to improve result')
    } finally {
      setIsImproving(false)
    }
  }

  const modalContent = (
    <div className={`flex flex-col ${isMobile ? 'h-full' : 'max-h-[80vh]'}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 flex-shrink-0 drawer-header">
        <div className="flex items-center gap-2">
          {action && <span className="text-2xl">{action.icon}</span>}
          <h2 className="text-lg font-semibold text-[#E6E8EB]">
            {action?.label || 'AI Result'}
          </h2>
        </div>
        <button
          onClick={onClose}
          className="icon-button"
          aria-label="Close"
        >
          <svg
            className="w-5 h-5 text-[#9BA4B5]"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4" style={{ minHeight: 0 }}>
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-12 space-y-4">
            <div className="spinner w-12 h-12" />
            <p className="text-[#9BA4B5]">Generating your content...</p>
          </div>
        )}

        {error && (
          <div className="alert-error">
            <div className="flex items-start gap-3">
              <svg
                className="w-5 h-5 flex-shrink-0 mt-0.5 text-red-500"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <div>
                <h3 className="alert-error-title">Error</h3>
                <p className="alert-error-text">{error}</p>
              </div>
            </div>
          </div>
        )}

        {!isLoading && !error && currentResult && (
          <div className="space-y-4">
            {/* Quota Info */}
            <div className="flex items-center justify-between text-sm">
              <span className="text-[#9BA4B5]">
                Actions remaining today: <span className="font-medium text-[#E6E8EB]">{currentResult.quota_remaining}</span>
              </span>
              <span className="text-xs text-gray-500">
                Resets: {new Date(currentResult.quota_reset_date).toLocaleDateString()}
              </span>
            </div>

            {/* Result Text */}
            <div className="result-card relative">
              {/* Loading Overlay */}
              {isImproving && (
                <div className="absolute inset-0 bg-black/50 backdrop-blur-sm rounded-lg flex flex-col items-center justify-center z-10">
                  <div className="spinner w-12 h-12 mb-3" />
                  <p className="text-white font-medium text-sm">Improving your result...</p>
                  <p className="text-white/70 text-xs mt-1">This may take a few moments</p>
                </div>
              )}
              <pre className={`whitespace-pre-wrap font-sans text-sm leading-relaxed text-[#E6E8EB] ${isImproving ? 'opacity-50' : ''}`}>
                {currentResult.message}
              </pre>
            </div>

            {/* Improve Section */}
            {showImprove && currentResult.session_id && (
              <div className="space-y-2">
                <label htmlFor="improve-instructions" className="block text-sm font-medium text-[#9BA4B5]">
                  How would you like to improve this result?
                </label>
                <textarea
                  id="improve-instructions"
                  value={improveInstructions}
                  onChange={(e) => setImproveInstructions(e.target.value)}
                  placeholder="E.g., 'make it shorter and more professional', 'add more examples', 'use bullet points'"
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-[#E6E8EB] placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  rows={3}
                  disabled={isImproving}
                />
                {improveError && (
                  <p className="text-sm text-red-400">{improveError}</p>
                )}
                <div className="flex gap-2">
                  <button
                    onClick={handleImprove}
                    disabled={isImproving || !improveInstructions.trim()}
                    className="btn-primary flex-1 relative"
                  >
                    {isImproving ? (
                      <>
                        <div className="spinner w-5 h-5" />
                        <span className="font-medium">Improving...</span>
                      </>
                    ) : (
                      <span>Apply Improvement</span>
                    )}
                  </button>
                  <button
                    onClick={() => {
                      setShowImprove(false)
                      setImproveInstructions('')
                      setImproveError(null)
                    }}
                    disabled={isImproving}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer Actions */}
      {!isLoading && !error && currentResult && (
        <div className="p-4 space-y-2 flex-shrink-0 border-t border-white/10">
          <button
            onClick={handleCopy}
            className={copied ? 'btn-success w-full' : 'btn-primary w-full'}
            disabled={isImproving}
          >
            {copied ? (
              <>
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>Copied!</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
                <span>Copy to Clipboard</span>
              </>
            )}
          </button>

          {/* Improve Button - only show if session exists */}
          {currentResult.session_id && !showImprove && (
            <button
              onClick={() => setShowImprove(true)}
              className="btn-secondary w-full"
              disabled={isImproving}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
              <span>Improve Result</span>
            </button>
          )}

          {onRegenerate && (
            <button
              onClick={onRegenerate}
              className="btn-secondary w-full"
              disabled={isImproving}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              <span>Regenerate</span>
            </button>
          )}
        </div>
      )}
    </div>
  )

  if (isMobile) {
    // Mobile: Full Screen Modal
    return (
      <div className="fixed inset-0 z-50 drawer-glass">
        {modalContent}
      </div>
    )
  }

  // Desktop: Centered Modal
  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/70 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="rounded-2xl shadow-2xl w-full max-w-2xl drawer-glass">
          {modalContent}
        </div>
      </div>
    </>
  )
}
