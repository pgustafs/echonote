/**
 * Utility functions and constants for transcription categories
 */

import { Category } from '../types'

/**
 * Human-readable labels for each category
 */
export const CATEGORY_LABELS: Record<Category, string> = {
  voice_memo: 'Voice Memo',
  meeting_notes: 'Meeting Notes',
  linkedin_post: 'LinkedIn Post',
  email_draft: 'Email Draft',
  blog_post: 'Blog Post',
  todo_list: 'TODO List',
  tweet: 'Tweet/X Post',
  youtube_description: 'YouTube',
  product_requirements: 'PRD',
  customer_feedback: 'Feedback',
  brainstorm: 'Brainstorm',
  interview_notes: 'Interview',
  journal_entry: 'Journal',
  newsletter: 'Newsletter',
  documentation: 'Documentation',
}

/**
 * Short labels for mobile/compact views
 */
export const CATEGORY_LABELS_SHORT: Record<Category, string> = {
  voice_memo: 'Memo',
  meeting_notes: 'Meeting',
  linkedin_post: 'LinkedIn',
  email_draft: 'Email',
  blog_post: 'Blog',
  todo_list: 'TODO',
  tweet: 'Tweet',
  youtube_description: 'YouTube',
  product_requirements: 'PRD',
  customer_feedback: 'Feedback',
  brainstorm: 'Idea',
  interview_notes: 'Interview',
  journal_entry: 'Journal',
  newsletter: 'Newsletter',
  documentation: 'Docs',
}

/**
 * Get CSS class name for category badge
 */
export function getCategoryClassName(category: Category): string {
  return `category-badge category-${category.replace(/_/g, '-')}`
}

/**
 * All available categories in order
 */
export const ALL_CATEGORIES: Category[] = [
  'voice_memo',
  'meeting_notes',
  'linkedin_post',
  'email_draft',
  'blog_post',
  'todo_list',
  'tweet',
  'youtube_description',
  'product_requirements',
  'customer_feedback',
  'brainstorm',
  'interview_notes',
  'journal_entry',
  'newsletter',
  'documentation',
]
