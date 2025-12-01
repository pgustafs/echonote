/**
 * Re-transcribe Modal Component
 * Allows users to re-transcribe existing recordings with new options
 *
 * Desktop: Centered modal overlay
 * Mobile: Full-screen slider from right
 */

import { useState, useEffect } from 'react'
import { X } from 'lucide-react'

interface ReTranscribeModalProps {
  transcriptionId: number | null
  isOpen: boolean
  onClose: () => void
  onSubmit: (options: ReTranscribeOptions) => Promise<void>
  availableModels: string[]
  defaultModel: string
  isMobile?: boolean
  currentUrl?: string
}

export interface ReTranscribeOptions {
  model?: string
  url?: string
  enableDiarization?: boolean
  numSpeakers?: number
}

export default function ReTranscribeModal({
  transcriptionId,
  isOpen,
  onClose,
  onSubmit,
  availableModels,
  defaultModel,
  isMobile = false,
  currentUrl = '',
}: ReTranscribeModalProps) {
  const [selectedModel, setSelectedModel] = useState(defaultModel)
  const [includeUrl, setIncludeUrl] = useState(Boolean(currentUrl))
  const [url, setUrl] = useState(currentUrl || '')
  const [enableDiarization, setEnableDiarization] = useState(false)
  const [numSpeakers, setNumSpeakers] = useState<number | undefined>(undefined)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Reset form when modal opens with new transcription or currentUrl changes
  useEffect(() => {
    if (isOpen) {
      setSelectedModel(defaultModel)
      setIncludeUrl(Boolean(currentUrl))
      setUrl(currentUrl || '')
      setEnableDiarization(false)
      setNumSpeakers(undefined)
      setIsSubmitting(false)
    }
  }, [isOpen, defaultModel, currentUrl])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!transcriptionId) return

    setIsSubmitting(true)
    try {
      await onSubmit({
        model: selectedModel !== defaultModel ? selectedModel : undefined,
        url: includeUrl && url.trim() ? url.trim() : undefined,
        enableDiarization,
        numSpeakers: enableDiarization && numSpeakers ? numSpeakers : undefined,
      })
      onClose()
    } catch (error) {
      console.error('Re-transcription failed:', error)
      alert(error instanceof Error ? error.message : 'Re-transcription failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen || !transcriptionId) return null

  // Mobile full-screen slider
  if (isMobile) {
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
              disabled={isSubmitting}
            >
              <X className="w-6 h-6" strokeWidth={2} />
            </button>
            <h2 className="text-lg font-bold text-text-primary">Re-Transcribe</h2>
            <div className="w-10"></div>
          </div>

          {/* Content */}
          <form onSubmit={handleSubmit} className="mobile-slider-content">
            <p className="text-text-secondary text-sm mb-6">
              Re-process this recording with different options. Your audio file will be re-analyzed with the settings you choose below.
            </p>

            {/* Model Selection */}
            <div className="section-container-mobile mb-4">
              <label htmlFor="model-mobile" className="text-xs font-semibold text-text-secondary mb-2 uppercase tracking-wide block">
                Transcription Model
              </label>
              <select
                id="model-mobile"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                disabled={isSubmitting}
                className="select-field py-2 text-sm min-h-[44px]"
              >
                {availableModels.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>

            {/* URL Toggle */}
            <div className="section-container-mobile mb-4">
              <label className="flex items-center gap-3 cursor-pointer min-h-[44px]">
                <input
                  type="checkbox"
                  checked={includeUrl}
                  onChange={(e) => setIncludeUrl(e.target.checked)}
                  disabled={isSubmitting}
                  className="checkbox-field"
                />
                <span className="text-text-primary text-sm font-medium">Include URL</span>
              </label>

              {includeUrl && (
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com"
                  disabled={isSubmitting}
                  className="input-field mt-3 text-sm min-h-[44px]"
                />
              )}
            </div>

            {/* Diarization Toggle */}
            <div className="section-container-mobile mb-4">
              <label className="flex items-center gap-3 cursor-pointer min-h-[44px]">
                <input
                  type="checkbox"
                  checked={enableDiarization}
                  onChange={(e) => setEnableDiarization(e.target.checked)}
                  disabled={isSubmitting}
                  className="checkbox-field"
                />
                <span className="text-text-primary text-sm font-medium">Speaker Diarization</span>
              </label>
              {enableDiarization && (
                <div className="mt-3">
                  <label htmlFor="speakers-mobile" className="text-xs font-semibold text-text-secondary mb-2 uppercase tracking-wide block">
                    Number of Speakers (optional)
                  </label>
                  <input
                    id="speakers-mobile"
                    type="number"
                    min="1"
                    max="10"
                    value={numSpeakers || ''}
                    onChange={(e) => setNumSpeakers(e.target.value ? parseInt(e.target.value) : undefined)}
                    placeholder="Auto-detect"
                    disabled={isSubmitting}
                    className="input-field text-sm min-h-[44px]"
                  />
                  <p className="text-text-tertiary text-xs mt-2">Leave empty to auto-detect</p>
                </div>
              )}
            </div>

            {/* Warning */}
            <div className="rounded-card bg-yellow-500/10 border border-yellow-500/20 p-4 mb-6">
              <p className="text-yellow-300 text-sm">
                ⚠️ This will replace the current transcription text with new results.
              </p>
            </div>
          </form>

          {/* Bottom Action Bar */}
          <div className="mobile-slider-actions">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="mobile-slider-action-btn"
            >
              <span className="text-xs font-medium">Cancel</span>
            </button>

            <button
              type="submit"
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="mobile-slider-action-btn mobile-slider-action-btn-accent"
            >
              {isSubmitting ? (
                <>
                  <div className="spinner w-5 h-5" />
                  <span className="text-xs font-medium">Starting...</span>
                </>
              ) : (
                <>
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span className="text-xs font-medium">Re-Transcribe</span>
                </>
              )}
            </button>
          </div>
        </div>
      </>
    )
  }

  // Desktop centered modal
  return (
    <>
      {/* Overlay */}
      <div
        className="modal-overlay fixed inset-0 z-40 flex items-center justify-center p-4"
        onClick={onClose}
      >
        {/* Modal */}
        <div
          className="modal-content modal-scrollable relative w-full max-w-md mx-auto"
          onClick={(e) => e.stopPropagation()}
        >
          <form onSubmit={handleSubmit} className="p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-text-primary">Re-Transcribe</h2>
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="text-text-tertiary hover:text-text-primary transition-colors p-1"
                aria-label="Close"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <p className="text-text-secondary text-sm mb-6">
              Re-process this recording with different options. Your audio file will be re-analyzed with the settings you choose below.
            </p>

            {/* Model Selection */}
            <div className="mb-5">
              <label htmlFor="model-desktop" className="block text-sm font-semibold text-text-secondary mb-2">
                Transcription Model
              </label>
              <select
                id="model-desktop"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                disabled={isSubmitting}
                className="select-field py-2.5 text-sm"
              >
                {availableModels.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>

            {/* URL Toggle */}
            <div className="mb-5">
              <label className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeUrl}
                  onChange={(e) => setIncludeUrl(e.target.checked)}
                  disabled={isSubmitting}
                  className="checkbox-field"
                />
                <span className="text-text-primary text-sm font-medium">Include URL</span>
              </label>

              {includeUrl && (
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com"
                  disabled={isSubmitting}
                  className="input-field mt-3 text-sm"
                />
              )}
            </div>

            {/* Diarization Toggle */}
            <div className="mb-5">
              <label className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableDiarization}
                  onChange={(e) => setEnableDiarization(e.target.checked)}
                  disabled={isSubmitting}
                  className="checkbox-field"
                />
                <span className="text-text-primary text-sm font-medium">Speaker Diarization</span>
              </label>

              {enableDiarization && (
                <div className="mt-3">
                  <label htmlFor="speakers-desktop" className="block text-xs font-semibold text-text-secondary mb-2">
                    Number of Speakers (optional)
                  </label>
                  <input
                    id="speakers-desktop"
                    type="number"
                    min="1"
                    max="10"
                    value={numSpeakers || ''}
                    onChange={(e) => setNumSpeakers(e.target.value ? parseInt(e.target.value) : undefined)}
                    placeholder="Auto-detect"
                    disabled={isSubmitting}
                    className="input-field text-sm"
                  />
                  <p className="text-text-tertiary text-xs mt-2">Leave empty to auto-detect</p>
                </div>
              )}
            </div>

            {/* Warning */}
            <div className="rounded-card bg-yellow-500/10 border border-yellow-500/20 p-4 mb-6">
              <p className="text-yellow-300 text-sm">
                ⚠️ This will replace the current transcription text with new results.
              </p>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="btn-secondary flex-1"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="btn-accent flex-1"
              >
                {isSubmitting ? (
                  <>
                    <div className="spinner w-5 h-5" />
                    <span>Starting...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    <span>Re-Transcribe</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
