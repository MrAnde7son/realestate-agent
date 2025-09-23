'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { User, authAPI, LoginCredentials, RegisterCredentials, ProfileUpdateData } from './auth'
import { validateTokens } from './token-utils'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials, redirectTo?: string) => Promise<void>
  register: (credentials: RegisterCredentials, redirectTo?: string) => Promise<void>
  logout: () => Promise<void>
  updateProfile: (data: ProfileUpdateData) => Promise<void>
  refreshUser: () => Promise<void>
  googleLogin: (redirectTo?: string) => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useOptionalAuth() {
  return useContext(AuthContext)
}

export function useAuth() {
  const context = useOptionalAuth()
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  const isAuthenticated = !!user

  const refreshUser = async () => {
    try {
      // Check if we have tokens
      const accessToken = authAPI.getAccessToken()
      
      if (accessToken) {
        // Check if token is expired before making API call
        const isExpired = authAPI.isTokenExpired(accessToken)
        if (isExpired) {
          authAPI.clearTokens()
          setUser(null)
        } else {
          // Token is valid, try to get profile
          try {
            const response = await authAPI.getProfile()
            setUser(response.user)
          } catch (profileError: any) {
            // Only clear tokens if it's a 401 error, not network errors
            if (profileError.message?.includes('401') || profileError.message?.includes('Session expired')) {
              authAPI.clearTokens()
              setUser(null)
            }
            // For other errors (like network), keep the user state as is
          }
        }
      } else {
        // No tokens, user is not authenticated - this is normal for public pages
        setUser(null)
      }
    } catch (error: any) {
      // Only clear tokens for authentication errors, not network errors
      if (error.message?.includes('401') || error.message?.includes('Session expired')) {
        authAPI.clearTokens()
        setUser(null)
      }
      // For other errors, keep the current state
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (credentials: LoginCredentials, redirectTo?: string) => {
    try {
      setIsLoading(true)
      const response = await authAPI.login(credentials)
      authAPI.setTokens(response.access_token, response.refresh_token)
      setUser(response.user)
      router.push(redirectTo || '/')
    } catch (error: any) {
      // Provide more specific error messages
      if (error.message?.includes('401') || error.message?.includes('Unauthorized')) {
        throw new Error('שם משתמש או סיסמה שגויים')
      } else if (error.message?.includes('Network') || error.message?.includes('fetch')) {
        throw new Error('שגיאת רשת - בדוק את החיבור לאינטרנט')
      } else {
        throw new Error(error.message || 'שגיאה בהתחברות')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (credentials: RegisterCredentials, redirectTo?: string) => {
    try {
      setIsLoading(true)
      const response = await authAPI.register(credentials)
      authAPI.setTokens(response.access_token, response.refresh_token)
      setUser(response.user)
      router.push(redirectTo || '/')
    } catch (error) {
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      await authAPI.logout()
    } catch (error) {
      // Ignore logout API errors
    } finally {
      authAPI.clearTokens()
      setUser(null)
      router.push('/auth')
    }
  }

  const updateProfile = async (data: ProfileUpdateData) => {
    try {
      const response = await authAPI.updateProfile(data)
      setUser(response.user)
    } catch (error) {
      throw error
    }
  }

  const googleLogin = async (redirectTo?: string) => {
    try {
      setIsLoading(true)
      
      // Get Google OAuth URL from backend with redirect parameter
      const response = await authAPI.googleLogin(redirectTo)
      
      // Redirect to Google OAuth
      window.location.href = response.auth_url
      
    } catch (error) {
      setIsLoading(false)
      throw error
    }
  }


  // Initialize auth state on mount
  useEffect(() => {
    // Add a timeout to prevent infinite loading state
    const timeoutId = setTimeout(() => {
      setIsLoading(false)
    }, 5000) // 5 second timeout

    refreshUser().finally(() => {
      clearTimeout(timeoutId)
    })

    return () => clearTimeout(timeoutId)
  }, [])

  // Simple periodic check - just verify user is still logged in
  useEffect(() => {
    if (!user) return

    const checkUserStatus = async () => {
      try {
        const accessToken = authAPI.getAccessToken()
        if (!accessToken) {
          authAPI.clearTokens()
          setUser(null)
          router.push('/auth')
          return
        }
        
        // Try to get profile - if it fails, user needs to re-login
        try {
          await authAPI.getProfile()
        } catch (profileError) {
          authAPI.clearTokens()
          setUser(null)
          router.push('/auth')
        }
      } catch (error) {
        authAPI.clearTokens()
        setUser(null)
        router.push('/auth')
      }
    }

    // Check every 10 minutes
    const interval = setInterval(checkUserStatus, 10 * 60 * 1000)

    return () => {
      clearInterval(interval)
    }
  }, [user, router])

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    updateProfile,
    refreshUser,
    googleLogin,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
