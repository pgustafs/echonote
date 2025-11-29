/**
 * Theme Context for managing dark/light mode
 *
 * Provides theme state and toggle functionality across the app
 * Persists user preference to localStorage
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

type Theme = 'dark' | 'light'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  // Initialize theme from localStorage or default to dark
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = localStorage.getItem('echonote-theme')
    return (stored === 'light' || stored === 'dark') ? stored : 'dark'
  })

  // Update document class and localStorage when theme changes
  useEffect(() => {
    const root = document.documentElement

    if (theme === 'light') {
      root.classList.add('light')
    } else {
      root.classList.remove('light')
    }

    localStorage.setItem('echonote-theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setThemeState(prev => prev === 'dark' ? 'light' : 'dark')
  }

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
