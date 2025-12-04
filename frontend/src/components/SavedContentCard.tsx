/**
 * SavedContentCard Component
 *
 * Displays a saved AI-generated content item with title, content preview,
 * metadata, and action buttons for editing and deleting.
 */

import { useState } from 'react'
import type { SavedContent } from '../api'

interface SavedContentCardProps {
  savedContent: SavedContent
  onEdit?: (id: number) => void
  onDelete?: (id: number) => void
  onView?: (savedContent: SavedContent) => void
  isMobile?: boolean
}

export default function SavedContentCard({
  savedContent,
  onEdit,
  onDelete,
  onView,
  isMobile = false,
}: SavedContentCardProps) {
  const [isDeleting, setIsDeleting] = useState(false)

  const handleDelete = async () => {
    if (!onDelete) return

    const confirmed = confirm('Delete this saved content? This action cannot be undone.')
    if (!confirmed) return

    setIsDeleting(true)
    try {
      await onDelete(savedContent.id)
    } catch (error) {
      console.error('Failed to delete saved content:', error)
      setIsDeleting(false)
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

  const getContentTypeLabel = (contentType: string): string => {
    const typeLabels: Record<string, string> = {
      linkedin_post: 'LinkedIn Post',
      email_draft: 'Email Draft',
      blog_post: 'Blog Post',
      todo_list: 'Todo List',
      tweet: 'Tweet',
      youtube_description: 'YouTube Description',
      meeting_summary: 'Meeting Summary',
      product_requirements: 'Product Requirements',
      customer_feedback: 'Customer Feedback',
      brainstorm_notes: 'Brainstorm Notes',
      interview_summary: 'Interview Summary',
      other: 'Other',
    }

    return typeLabels[contentType] || contentType
  }

  const truncateContent = (content: string, maxLength: number = 150): string => {
    if (content.length <= maxLength) return content
    return content.substring(0, maxLength) + '...'
  }

  return (
    <div className={isMobile ? 'card p-4' : 'card'}>
      <div className="flex flex-col gap-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="badge-secondary text-xs">
                {getContentTypeLabel(savedContent.content_type)}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-text-primary truncate">
              {savedContent.title || 'Untitled'}
            </h3>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {onEdit && (
              <button
                onClick={() => onEdit(savedContent.id)}
                className="btn-icon-secondary"
                title="Edit"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
              </button>
            )}
            {onDelete && (
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="btn-icon-danger"
                title="Delete"
              >
                {isDeleting ? (
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Content Preview */}
        <div
          onClick={() => onView && onView(savedContent)}
          className={onView ? 'cursor-pointer' : ''}
        >
          <p className="text-sm text-text-secondary leading-relaxed">
            {truncateContent(savedContent.content)}
          </p>
        </div>

        {/* Footer Metadata */}
        <div className="flex items-center justify-between text-xs text-text-tertiary pt-2 border-t border-stroke-subtle">
          <div className="flex items-center gap-4">
            <span title="Created">
              Created {formatDate(savedContent.created_at)}
            </span>
            {savedContent.updated_at !== savedContent.created_at && (
              <span title="Updated">
                Updated {formatDate(savedContent.updated_at)}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
