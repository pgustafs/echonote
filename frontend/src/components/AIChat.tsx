/**
 * AI Chat Component
 *
 * Free-form chat interface with the AI model
 * Supports multi-turn conversations and transcription context
 */

import { useState, useEffect, useRef } from 'react'
import { chatWithAI, cleanupAISession } from '../api'
import type { AIActionResponse } from '../types'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isLoading?: boolean
  error?: string | null
}

interface AIChatProps {
  transcriptionId?: number | null
  transcriptionText?: string | null
  onClose?: () => void
  isMobile?: boolean
}

export default function AIChat({
  transcriptionId = null,
  transcriptionText = null,
  onClose,
  isMobile = false,
}: AIChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [quotaRemaining, setQuotaRemaining] = useState<number | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Cleanup session on unmount
  useEffect(() => {
    return () => {
      if (sessionId) {
        cleanupAISession(sessionId).catch(err => {
          console.warn('Failed to cleanup chat session:', err)
        })
      }
    }
  }, [sessionId])

  // Initial message if transcription context provided
  useEffect(() => {
    if (transcriptionText && messages.length === 0) {
      setMessages([
        {
          id: Date.now().toString(),
          role: 'assistant',
          content: 'Hello! I have access to your transcription. Feel free to ask me anything about it, or request help with any writing task!',
          timestamp: new Date(),
        },
      ])
    }
  }, [transcriptionText, messages.length])

  const handleSend = async () => {
    const message = inputMessage.trim()
    if (!message || isLoading) return

    // Add user message to chat
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    // Add loading assistant message
    const loadingMessage: Message = {
      id: `${Date.now()}-loading`,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    }
    setMessages(prev => [...prev, loadingMessage])

    try {
      const response: AIActionResponse = await chatWithAI({
        message,
        session_id: sessionId,
        transcription_id: transcriptionId,
      })

      // Update session ID from response
      if (response.session_id) {
        setSessionId(response.session_id)
      }

      // Update quota
      setQuotaRemaining(response.quota_remaining)

      // Replace loading message with actual response
      setMessages(prev =>
        prev.map(msg =>
          msg.id === loadingMessage.id
            ? {
                ...msg,
                content: response.message || 'No response from AI',
                isLoading: false,
              }
            : msg
        )
      )
    } catch (err) {
      console.error('Chat error:', err)

      // Replace loading message with error
      setMessages(prev =>
        prev.map(msg =>
          msg.id === loadingMessage.id
            ? {
                ...msg,
                content: 'Sorry, I encountered an error. Please try again.',
                isLoading: false,
                error: err instanceof Error ? err.message : 'Unknown error',
              }
            : msg
        )
      )
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const clearChat = () => {
    if (window.confirm('Clear all messages and start a new conversation?')) {
      // Cleanup old session
      if (sessionId) {
        cleanupAISession(sessionId).catch(console.warn)
      }

      setMessages([])
      setSessionId(null)
      setQuotaRemaining(null)

      // Add initial message if transcription context
      if (transcriptionText) {
        setMessages([
          {
            id: Date.now().toString(),
            role: 'assistant',
            content: 'Conversation cleared. How can I help you with your transcription?',
            timestamp: new Date(),
          },
        ])
      }
    }
  }

  const chatContent = (
    <div className={`flex flex-col ${isMobile ? 'h-full' : 'h-[600px]'}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 flex-shrink-0 drawer-header gap-2">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <span className="text-2xl flex-shrink-0">💬</span>
          <h2 className="text-lg font-semibold text-text-primary truncate">
            {transcriptionId ? 'Chat About Transcription' : 'Chat with AI'}
          </h2>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {quotaRemaining !== null && (
            <span className="text-xs text-text-secondary px-2 py-1 card rounded whitespace-nowrap">
              {quotaRemaining} left
            </span>
          )}
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="icon-button"
              aria-label="Clear chat"
              title="Clear chat"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="icon-button"
              aria-label="Close"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 w-full" style={{ minHeight: 0 }}>
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <svg className="w-16 h-16 text-icon mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <h3 className="text-lg font-medium text-text-primary mb-2">Start a Conversation</h3>
            <p className="text-sm text-text-secondary max-w-sm">
              {transcriptionId
                ? 'Ask questions about your transcription, request summaries, or get help with writing tasks.'
                : 'Get help with writing, ask questions, or just have a conversation with the AI model.'}
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex w-full ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 overflow-hidden ${
                message.role === 'user'
                  ? 'bg-accent-blue text-white'
                  : message.error
                  ? 'alert-error'
                  : 'card text-text-primary'
              }`}
            >
              {message.isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="spinner w-4 h-4" />
                  <span className="text-sm">Thinking...</span>
                </div>
              ) : (
                <div className="whitespace-pre-wrap font-sans text-sm leading-relaxed break-words overflow-wrap-anywhere">
                  {message.content}
                </div>
              )}
              <div className="mt-1 text-xs opacity-60">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 flex-shrink-0 border-t border-stroke-subtle">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isMobile ? "Type your message..." : "Type your message... (Shift+Enter for new line)"}
            className="input-field flex-1 text-sm resize-none min-w-0"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!inputMessage.trim() || isLoading}
            className="btn-ai px-4 self-end"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )

  if (isMobile || !onClose) {
    // Full page view - z-50 to appear above BottomNav (z-30)
    return <div className="fixed inset-0 z-50 drawer-glass overflow-hidden">{chatContent}</div>
  }

  // Modal view
  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/70 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="rounded-2xl shadow-2xl w-full max-w-3xl drawer-glass">
          {chatContent}
        </div>
      </div>
    </>
  )
}
