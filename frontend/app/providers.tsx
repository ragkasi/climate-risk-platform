'use client'

import { createContext, useContext, useState, useEffect } from 'react'
import { SWRConfig } from 'swr'
import axios from 'axios'

// Auth context
interface AuthContextType {
  user: any | null
  token: string | null
  login: (token: string) => void
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Theme context
interface ThemeContextType {
  theme: 'light' | 'dark'
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

// Auth provider
function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any | null>(null)
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    // Check for stored token on mount
    const storedToken = localStorage.getItem('auth_token')
    if (storedToken) {
      setToken(storedToken)
      // In a real app, you'd validate the token and fetch user data
      setUser({ email: 'demo@example.com', role: 'user' })
    }
  }, [])

  const login = (newToken: string) => {
    setToken(newToken)
    localStorage.setItem('auth_token', newToken)
    // In a real app, you'd fetch user data here
    setUser({ email: 'demo@example.com', role: 'user' })
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('auth_token')
  }

  const isAuthenticated = !!token

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  )
}

// Theme provider
function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    // Check for stored theme preference
    const storedTheme = localStorage.getItem('theme') as 'light' | 'dark'
    if (storedTheme) {
      setTheme(storedTheme)
    } else {
      // Check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      setTheme(prefersDark ? 'dark' : 'light')
    }
  }, [])

  useEffect(() => {
    // Apply theme to document
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

// SWR fetcher
const fetcher = async (url: string) => {
  const token = localStorage.getItem('auth_token')
  const response = await axios.get(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  return response.data
}

// Main providers component
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig
      value={{
        fetcher,
        revalidateOnFocus: false,
        revalidateOnReconnect: true,
        refreshInterval: 30000, // 30 seconds
      }}
    >
      <ThemeProvider>
        <AuthProvider>
          {children}
        </AuthProvider>
      </ThemeProvider>
    </SWRConfig>
  )
}
