/**
 * AI Actions Drawer/Sheet Component
 *
 * Shows as bottom sheet on mobile, side drawer on desktop
 * Displays categorized AI actions for a transcription
 */

import { useState } from 'react'
import { AI_ACTION_CATEGORIES, getActionsByCategory } from '../constants/aiActions'
import type { AIAction } from '../types'

interface AIActionsDrawerProps {
  isOpen: boolean
  onClose: () => void
  onSelectAction: (action: AIAction) => void
  isMobile?: boolean
}

export default function AIActionsDrawer({
  isOpen,
  onClose,
  onSelectAction,
  isMobile = false,
}: AIActionsDrawerProps) {
  const [expandedCategory, setExpandedCategory] = useState<string | null>('analyze')

  if (!isOpen) return null

  const toggleCategory = (categoryId: string) => {
    setExpandedCategory(expandedCategory === categoryId ? null : categoryId)
  }

  const handleActionClick = (action: AIAction) => {
    onSelectAction(action)
  }

  const drawerContent = (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}>
        <h2 className="text-lg font-semibold flex items-center gap-2" style={{ color: '#E6E8EB' }}>
          <span>✨</span>
          <span>AI Actions</span>
        </h2>
        <button
          onClick={onClose}
          className="p-2 rounded-lg transition-all duration-200 touch-target"
          style={{ background: 'rgba(255, 255, 255, 0.04)' }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)'
          }}
          aria-label="Close"
        >
          <svg
            className="w-5 h-5"
            style={{ color: '#9BA4B5' }}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Categories - Scrollable */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3" style={{ minHeight: 0 }}>
        {AI_ACTION_CATEGORIES.map((category) => {
          const actions = getActionsByCategory(category.id)
          const isExpanded = expandedCategory === category.id

          return (
            <div
              key={category.id}
              className="rounded-lg overflow-hidden"
              style={{
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              {/* Category Header */}
              <button
                onClick={() => toggleCategory(category.id)}
                className="w-full flex items-center justify-between p-3 transition-all duration-200"
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)'
                }}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xl">{category.icon}</span>
                  <span className="font-medium" style={{ color: '#E6E8EB' }}>{category.label}</span>
                  <span className="text-xs" style={{ color: '#9BA4B5' }}>({actions.length})</span>
                </div>
                <svg
                  className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                  style={{ color: '#9BA4B5' }}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Actions List */}
              {isExpanded && (
                <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
                  {actions.map((action) => (
                    <button
                      key={action.id}
                      onClick={() => handleActionClick(action)}
                      className="w-full flex items-start gap-3 p-3 transition-all duration-200 text-left touch-target"
                      style={{
                        background: 'transparent',
                        borderTop: '1px solid rgba(255, 255, 255, 0.04)',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'rgba(92, 124, 250, 0.08)'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'transparent'
                      }}
                    >
                      <span className="text-2xl flex-shrink-0">{action.icon}</span>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium" style={{ color: '#E6E8EB' }}>{action.label}</div>
                        <div className="text-sm" style={{ color: '#9BA4B5' }}>{action.description}</div>
                      </div>
                      <svg
                        className="w-5 h-5 flex-shrink-0 mt-1"
                        style={{ color: '#5C7CFA' }}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )

  if (isMobile) {
    // Mobile: Bottom Sheet
    return (
      <>
        {/* Backdrop */}
        <div
          className="fixed inset-0 z-40 transition-opacity"
          style={{ background: 'rgba(0, 0, 0, 0.7)' }}
          onClick={onClose}
          aria-hidden="true"
        />

        {/* Bottom Sheet */}
        <div
          className="fixed inset-x-0 bottom-0 z-50 rounded-t-2xl shadow-2xl flex flex-col animate-slide-up"
          style={{
            background: 'rgba(15, 23, 42, 0.95)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderBottom: 'none',
            maxHeight: '85vh',
            height: '85vh',
          }}
        >
          {/* Handle */}
          <div className="flex justify-center pt-3 pb-2 flex-shrink-0">
            <div className="w-12 h-1 rounded-full" style={{ background: 'rgba(255, 255, 255, 0.3)' }} />
          </div>
          {drawerContent}
        </div>
      </>
    )
  }

  // Desktop: Side Drawer
  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 transition-opacity"
        style={{ background: 'rgba(0, 0, 0, 0.7)' }}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Side Drawer */}
      <div
        className="fixed right-0 top-0 bottom-0 z-50 shadow-2xl w-96 max-w-full animate-slide-left"
        style={{
          background: 'rgba(15, 23, 42, 0.95)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRight: 'none',
        }}
      >
        {drawerContent}
      </div>
    </>
  )
}
