/**
 * Authentication context for managing user authentication state
 * Provides login, register, logout functionality with JWT token management
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { getApiBaseUrl, getCurrentUser } from '../api'

export interface User {
  id: number
  username: string
  email: string
  created_at: string
  is_active: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<boolean>
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const TOKEN_KEY = 'echonote_token'
const REFRESH_TOKEN_KEY = 'echonote_refresh_token'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Load token from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY)
    if (storedToken) {
      setToken(storedToken)
      // Fetch current user info
      fetchCurrentUser()
    } else {
      setIsLoading(false)
    }
  }, [])

  const fetchCurrentUser = async () => {
    try {
      const userData = await getCurrentUser()
      setUser(userData)
    } catch (error) {
      console.error('Error fetching user:', error)
      // Only clear tokens if it's not a session expired error (which already redirected)
      if (error instanceof Error && !error.message.includes('Session expired')) {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(REFRESH_TOKEN_KEY)
        setToken(null)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    const response = await fetch(`${getApiBaseUrl()}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }

    const data = await response.json()
    const accessToken = data.access_token
    const refreshToken = data.refresh_token

    // Store both tokens
    localStorage.setItem(TOKEN_KEY, accessToken)
    if (refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
    }
    setToken(accessToken)

    // Fetch user info
    await fetchCurrentUser()
  }

  const register = async (username: string, email: string, password: string) => {
    const response = await fetch(`${getApiBaseUrl()}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, email, password }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Registration failed')
    }

    // After successful registration, automatically log in
    await login(username, password)
  }

  const refreshToken = async (): Promise<boolean> => {
    const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    if (!storedRefreshToken) {
      return false
    }

    try {
      const response = await fetch(`${getApiBaseUrl()}/auth/refresh`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${storedRefreshToken}`,
        },
      })

      if (!response.ok) {
        // Refresh token is invalid or expired
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(REFRESH_TOKEN_KEY)
        setToken(null)
        setUser(null)
        return false
      }

      const data = await response.json()
      const newAccessToken = data.access_token

      // Update access token
      localStorage.setItem(TOKEN_KEY, newAccessToken)
      setToken(newAccessToken)

      return true
    } catch (error) {
      console.error('Error refreshing token:', error)
      return false
    }
  }

  const logout = async () => {
    const currentToken = token || localStorage.getItem(TOKEN_KEY)

    // Call logout endpoint to blacklist the token
    if (currentToken) {
      try {
        await fetch(`${getApiBaseUrl()}/auth/logout`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${currentToken}`,
          },
        })
      } catch (error) {
        console.error('Error during logout:', error)
        // Continue with local logout even if API call fails
      }
    }

    // Clear tokens and state
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        register,
        logout,
        refreshToken,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
