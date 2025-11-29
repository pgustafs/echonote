/**
 * AI Actions configuration
 * Defines all available AI actions organized by category
 */

import type { AIAction } from '../types'

// Icon helper for consistent SVG styling
const Icon = ({ path }: { path: string }) => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d={path} />
  </svg>
)

export const AI_ACTIONS: AIAction[] = [
  // Analyze
  {
    id: 'analyze',
    category: 'analyze',
    label: 'Analyze',
    description: 'Extract summary, tasks, and next actions',
    icon: <Icon path="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />,
    endpoint: '/analyze',
  },

  // Create
  {
    id: 'create-linkedin-post',
    category: 'create',
    label: 'LinkedIn Post',
    description: 'Generate a professional LinkedIn post',
    icon: <Icon path="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />,
    endpoint: '/create/linkedin-post',
  },
  {
    id: 'create-email-draft',
    category: 'create',
    label: 'Email Draft',
    description: 'Create a professional email',
    icon: <Icon path="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />,
    endpoint: '/create/email-draft',
  },
  {
    id: 'create-blog-post',
    category: 'create',
    label: 'Blog Post',
    description: 'Generate a blog post',
    icon: <Icon path="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />,
    endpoint: '/create/blog-post',
  },
  {
    id: 'create-social-caption',
    category: 'create',
    label: 'Social Media Caption',
    description: 'Create engaging social media caption',
    icon: <Icon path="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />,
    endpoint: '/create/social-media-caption',
  },

  // Improve/Transform
  {
    id: 'improve-summarize',
    category: 'improve',
    label: 'Summarize',
    description: 'Create a concise summary',
    icon: <Icon path="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />,
    endpoint: '/improve/summarize',
  },
  {
    id: 'improve-summarize-bullets',
    category: 'improve',
    label: 'Bullet Points',
    description: 'Summarize as bullet points',
    icon: <Icon path="M4 6h16M4 12h16M4 18h16" />,
    endpoint: '/improve/summarize-bullets',
  },
  {
    id: 'improve-rewrite-formal',
    category: 'improve',
    label: 'Make Formal',
    description: 'Rewrite in formal tone',
    icon: <Icon path="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />,
    endpoint: '/improve/rewrite-formal',
  },
  {
    id: 'improve-rewrite-friendly',
    category: 'improve',
    label: 'Make Friendly',
    description: 'Rewrite in friendly tone',
    icon: <Icon path="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />,
    endpoint: '/improve/rewrite-friendly',
  },
  {
    id: 'improve-rewrite-simple',
    category: 'improve',
    label: 'Simplify',
    description: 'Rewrite in simple language',
    icon: <Icon path="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />,
    endpoint: '/improve/rewrite-simple',
  },
  {
    id: 'improve-expand',
    category: 'improve',
    label: 'Expand',
    description: 'Add more detail and context',
    icon: <Icon path="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />,
    endpoint: '/improve/expand',
  },
  {
    id: 'improve-shorten',
    category: 'improve',
    label: 'Shorten',
    description: 'Make more concise',
    icon: <Icon path="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />,
    endpoint: '/improve/shorten',
  },

  // Translate
  {
    id: 'translate-english',
    category: 'translate',
    label: 'To English',
    description: 'Translate to English',
    icon: <Icon path="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />,
    endpoint: '/translate/to-english',
  },
  {
    id: 'translate-swedish',
    category: 'translate',
    label: 'To Swedish',
    description: 'Translate to Swedish',
    icon: <Icon path="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />,
    endpoint: '/translate/to-swedish',
  },
  {
    id: 'translate-czech',
    category: 'translate',
    label: 'To Czech',
    description: 'Translate to Czech',
    icon: <Icon path="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />,
    endpoint: '/translate/to-czech',
  },

  // Voice-specific
  {
    id: 'voice-clean-fillers',
    category: 'voice',
    label: 'Clean Filler Words',
    description: 'Remove um, uh, like, etc.',
    icon: <Icon path="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />,
    endpoint: '/voice/clean-filler-words',
  },
  {
    id: 'voice-fix-grammar',
    category: 'voice',
    label: 'Fix Grammar',
    description: 'Correct grammar mistakes',
    icon: <Icon path="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />,
    endpoint: '/voice/fix-grammar',
  },
  {
    id: 'voice-spoken-to-written',
    category: 'voice',
    label: 'Spoken → Written',
    description: 'Convert spoken style to written',
    icon: <Icon path="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />,
    endpoint: '/voice/convert-spoken-to-written',
  },
]

export const AI_ACTION_CATEGORIES = [
  {
    id: 'analyze',
    label: 'Analyze',
    icon: <Icon path="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  },
  {
    id: 'create',
    label: 'Create',
    icon: <Icon path="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  },
  {
    id: 'improve',
    label: 'Improve',
    icon: <Icon path="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
  },
  {
    id: 'translate',
    label: 'Translate',
    icon: <Icon path="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  },
  {
    id: 'voice',
    label: 'Voice Cleanup',
    icon: <Icon path="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
  },
] as const

export function getActionsByCategory(category: string): AIAction[] {
  return AI_ACTIONS.filter(action => action.category === category)
}
