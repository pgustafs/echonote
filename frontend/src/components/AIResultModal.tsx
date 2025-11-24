/**
 * AI Result Modal Component
 *
 * Displays the result of an AI action with copy and regenerate options
 */

import { useState } from 'react'
import type { AIActionResponse, AIAction } from '../types'

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

  if (!isOpen) return null

  const handleCopy = async () => {
    if (!result?.message) return

    try {
      await navigator.clipboard.writeText(result.message)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
      alert('Failed to copy to clipboard')
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

        {!isLoading && !error && result && (
          <div className="space-y-4">
            {/* Quota Info */}
            <div className="flex items-center justify-between text-sm">
              <span className="text-[#9BA4B5]">
                Actions remaining today: <span className="font-medium text-[#E6E8EB]">{result.quota_remaining}</span>
              </span>
              <span className="text-xs text-gray-500">
                Resets: {new Date(result.quota_reset_date).toLocaleDateString()}
              </span>
            </div>

            {/* Result Text */}
            <div className="result-card">
              <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-[#E6E8EB]">
                {result.message}
              </pre>
            </div>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      {!isLoading && !error && result && (
        <div className="p-4 space-y-2 flex-shrink-0 border-t border-white/10">
          <button
            onClick={handleCopy}
            className={copied ? 'btn-success w-full' : 'btn-primary w-full'}
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

          {onRegenerate && (
            <button
              onClick={onRegenerate}
              className="btn-secondary w-full"
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
