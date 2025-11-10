/**
 * Login/Register page component
 * Provides authentication UI matching the neo-minimal dark mode theme
 */

import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

export default function Login() {
  const { login, register } = useAuth()
  const [isRegisterMode, setIsRegisterMode] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form fields
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      if (isRegisterMode) {
        await register(username, email, password)
      } else {
        await login(username, password)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed')
    } finally {
      setIsLoading(false)
    }
  }

  const toggleMode = () => {
    setIsRegisterMode(!isRegisterMode)
    setError(null)
    setEmail('')
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      {/* Background gradient */}
      <div className="fixed inset-0 gradient-header opacity-20" style={{ zIndex: 0 }}></div>

      {/* Login card */}
      <div className="w-full max-w-md relative" style={{ zIndex: 1 }}>
        <div className="enterprise-card-dark p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-white/10 backdrop-blur-md rounded-2xl shadow-lg flex items-center justify-center border border-white/20">
              <svg
                className="w-9 h-9 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                />
              </svg>
            </div>
            <h1 className="text-3xl font-bold mb-2" style={{ color: '#E6E8EB' }}>
              {isRegisterMode ? 'Create Account' : 'Welcome Back'}
            </h1>
            <p className="text-sm" style={{ color: '#9BA4B5' }}>
              {isRegisterMode
                ? 'Sign up to start using EchoNote'
                : 'Sign in to access your transcriptions'}
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div
              className="mb-6 rounded-2xl p-4"
              style={{
                background: 'rgba(228, 76, 101, 0.1)',
                border: '1px solid rgba(228, 76, 101, 0.3)',
              }}
            >
              <div className="flex items-start space-x-3">
                <svg
                  className="w-5 h-5 flex-shrink-0 mt-0.5"
                  style={{ color: '#E44C65' }}
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                <p className="text-sm font-medium" style={{ color: '#E44C65' }}>
                  {error}
                </p>
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username field */}
            <div>
              <label
                htmlFor="username"
                className="block text-sm font-semibold mb-2"
                style={{ color: '#E6E8EB' }}
              >
                Username
              </label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                minLength={3}
                maxLength={50}
                className="w-full px-4 py-3 rounded-2xl transition-all duration-200 outline-none focus:outline-none"
                style={{
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  color: '#E6E8EB',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)'
                  e.currentTarget.style.borderColor = 'rgba(92, 124, 250, 0.5)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)'
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)'
                }}
                placeholder="Enter your username"
                disabled={isLoading}
              />
            </div>

            {/* Email field (only for registration) */}
            {isRegisterMode && (
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-semibold mb-2"
                  style={{ color: '#E6E8EB' }}
                >
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-3 rounded-2xl transition-all duration-200 outline-none focus:outline-none"
                  style={{
                    background: 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    color: '#E6E8EB',
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)'
                    e.currentTarget.style.borderColor = 'rgba(92, 124, 250, 0.5)'
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)'
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)'
                  }}
                  placeholder="Enter your email"
                  disabled={isLoading}
                />
              </div>
            )}

            {/* Password field */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-semibold mb-2"
                style={{ color: '#E6E8EB' }}
              >
                Password
              </label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full px-4 py-3 rounded-2xl transition-all duration-200 outline-none focus:outline-none"
                style={{
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  color: '#E6E8EB',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)'
                  e.currentTarget.style.borderColor = 'rgba(92, 124, 250, 0.5)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)'
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)'
                }}
                placeholder="Enter your password"
                disabled={isLoading}
              />
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full px-6 py-3 font-semibold rounded-2xl transition-all duration-200 min-h-[48px] disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background: 'linear-gradient(135deg, #5C7CFA 0%, #9775FA 100%)',
                color: 'white',
                boxShadow: '0 4px 12px rgba(92, 124, 250, 0.25)',
              }}
              onMouseEnter={(e) => {
                if (!isLoading) {
                  e.currentTarget.style.boxShadow = '0 6px 20px rgba(92, 124, 250, 0.35)'
                  e.currentTarget.style.transform = 'translateY(-1px)'
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(92, 124, 250, 0.25)'
                e.currentTarget.style.transform = 'translateY(0)'
              }}
            >
              {isLoading ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>{isRegisterMode ? 'Creating Account...' : 'Signing In...'}</span>
                </div>
              ) : (
                <span>{isRegisterMode ? 'Create Account' : 'Sign In'}</span>
              )}
            </button>
          </form>

          {/* Toggle between login and register */}
          <div className="mt-6 text-center">
            <button
              onClick={toggleMode}
              disabled={isLoading}
              className="text-sm font-medium transition-colors disabled:opacity-50"
              style={{ color: '#5C7CFA' }}
              onMouseEnter={(e) => e.currentTarget.style.color = '#4ADEDE'}
              onMouseLeave={(e) => e.currentTarget.style.color = '#5C7CFA'}
            >
              {isRegisterMode
                ? 'Already have an account? Sign in'
                : "Don't have an account? Sign up"}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
