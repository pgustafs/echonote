/**
 * Login/Register page component
 * 2025 theme-aware authentication UI
 */

import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { Sun, Moon } from 'lucide-react'

export default function Login() {
  const { login, register } = useAuth()
  const { theme, toggleTheme } = useTheme()
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
    <div className="min-h-screen flex items-center justify-center px-4 bg-bg">
      {/* Theme toggle button - top right */}
      <button
        onClick={toggleTheme}
        className="fixed top-4 right-4 icon-button z-50"
        aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      >
        {theme === 'dark' ? (
          <Sun className="w-5 h-5" />
        ) : (
          <Moon className="w-5 h-5" />
        )}
      </button>

      {/* Login card */}
      <div className="w-full max-w-md">
        <div className="card p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-bg-tertiary rounded-card flex items-center justify-center border border-stroke-subtle">
              <svg
                className="w-9 h-9 text-icon"
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
            <h1 className="text-3xl font-bold mb-2 text-text-primary">
              {isRegisterMode ? 'Create Account' : 'Welcome Back'}
            </h1>
            <p className="text-sm text-text-secondary">
              {isRegisterMode
                ? 'Sign up to start using EchoNote'
                : 'Sign in to access your transcriptions'}
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="alert-error mb-6">
              <div className="flex items-start gap-3">
                <svg
                  className="w-5 h-5 flex-shrink-0 mt-0.5 text-error"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                <p className="alert-error-title">
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
                className="block text-sm font-semibold mb-2 text-text-primary"
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
                className="input-field"
                placeholder="Enter your username"
                disabled={isLoading}
              />
            </div>

            {/* Email field (only for registration) */}
            {isRegisterMode && (
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-semibold mb-2 text-text-primary"
                >
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="input-field"
                  placeholder="Enter your email"
                  disabled={isLoading}
                />
              </div>
            )}

            {/* Password field */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-semibold mb-2 text-text-primary"
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
                className="input-field"
                placeholder="Enter your password"
                disabled={isLoading}
              />
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn-accent-blue w-full"
            >
              {isLoading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 spinner"></div>
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
              className="text-sm font-medium text-accent-blue hover:text-accent-mint transition-colors disabled:opacity-disabled"
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
