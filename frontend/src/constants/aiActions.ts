/**
 * AI Actions configuration
 * Defines all available AI actions organized by category
 */

import type { AIAction } from '../types'

export const AI_ACTIONS: AIAction[] = [
  // Analyze
  {
    id: 'analyze',
    category: 'analyze',
    label: 'Analyze',
    description: 'Extract summary, tasks, and next actions',
    icon: '📊',
    endpoint: '/analyze',
  },

  // Create
  {
    id: 'create-linkedin-post',
    category: 'create',
    label: 'LinkedIn Post',
    description: 'Generate a professional LinkedIn post',
    icon: '💼',
    endpoint: '/create/linkedin-post',
  },
  {
    id: 'create-email-draft',
    category: 'create',
    label: 'Email Draft',
    description: 'Create a professional email',
    icon: '✉️',
    endpoint: '/create/email-draft',
  },
  {
    id: 'create-blog-post',
    category: 'create',
    label: 'Blog Post',
    description: 'Generate a blog post',
    icon: '📝',
    endpoint: '/create/blog-post',
  },
  {
    id: 'create-social-caption',
    category: 'create',
    label: 'Social Media Caption',
    description: 'Create engaging social media caption',
    icon: '📱',
    endpoint: '/create/social-media-caption',
  },

  // Improve/Transform
  {
    id: 'improve-summarize',
    category: 'improve',
    label: 'Summarize',
    description: 'Create a concise summary',
    icon: '📄',
    endpoint: '/improve/summarize',
  },
  {
    id: 'improve-summarize-bullets',
    category: 'improve',
    label: 'Bullet Points',
    description: 'Summarize as bullet points',
    icon: '•',
    endpoint: '/improve/summarize-bullets',
  },
  {
    id: 'improve-rewrite-formal',
    category: 'improve',
    label: 'Make Formal',
    description: 'Rewrite in formal tone',
    icon: '👔',
    endpoint: '/improve/rewrite-formal',
  },
  {
    id: 'improve-rewrite-friendly',
    category: 'improve',
    label: 'Make Friendly',
    description: 'Rewrite in friendly tone',
    icon: '😊',
    endpoint: '/improve/rewrite-friendly',
  },
  {
    id: 'improve-rewrite-simple',
    category: 'improve',
    label: 'Simplify',
    description: 'Rewrite in simple language',
    icon: '💡',
    endpoint: '/improve/rewrite-simple',
  },
  {
    id: 'improve-expand',
    category: 'improve',
    label: 'Expand',
    description: 'Add more detail and context',
    icon: '📈',
    endpoint: '/improve/expand',
  },
  {
    id: 'improve-shorten',
    category: 'improve',
    label: 'Shorten',
    description: 'Make more concise',
    icon: '📉',
    endpoint: '/improve/shorten',
  },

  // Translate
  {
    id: 'translate-english',
    category: 'translate',
    label: 'To English',
    description: 'Translate to English',
    icon: '🇬🇧',
    endpoint: '/translate/to-english',
  },
  {
    id: 'translate-swedish',
    category: 'translate',
    label: 'To Swedish',
    description: 'Translate to Swedish',
    icon: '🇸🇪',
    endpoint: '/translate/to-swedish',
  },
  {
    id: 'translate-czech',
    category: 'translate',
    label: 'To Czech',
    description: 'Translate to Czech',
    icon: '🇨🇿',
    endpoint: '/translate/to-czech',
  },

  // Voice-specific
  {
    id: 'voice-clean-fillers',
    category: 'voice',
    label: 'Clean Filler Words',
    description: 'Remove um, uh, like, etc.',
    icon: '🎤',
    endpoint: '/voice/clean-filler-words',
  },
  {
    id: 'voice-fix-grammar',
    category: 'voice',
    label: 'Fix Grammar',
    description: 'Correct grammar mistakes',
    icon: '✏️',
    endpoint: '/voice/fix-grammar',
  },
  {
    id: 'voice-spoken-to-written',
    category: 'voice',
    label: 'Spoken → Written',
    description: 'Convert spoken style to written',
    icon: '📖',
    endpoint: '/voice/convert-spoken-to-written',
  },
]

export const AI_ACTION_CATEGORIES = [
  { id: 'analyze', label: 'Analyze', icon: '📊' },
  { id: 'create', label: 'Create', icon: '✨' },
  { id: 'improve', label: 'Improve', icon: '📝' },
  { id: 'translate', label: 'Translate', icon: '🌍' },
  { id: 'voice', label: 'Voice Cleanup', icon: '🎤' },
] as const

export function getActionsByCategory(category: string): AIAction[] {
  return AI_ACTIONS.filter(action => action.category === category)
}
