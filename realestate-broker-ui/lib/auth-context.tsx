'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { User, authAPI, LoginCredentials, RegisterCredentials, ProfileUpdateData } from './auth'
import { validateTokens } from './token-utils'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  register: (credentials: RegisterCredentials) => Promise<void>
  logout: () => Promise<void>
  updateProfile: (data: ProfileUpdateData) => Promise<void>
  refreshUser: () => Promise<void>
  googleLogin: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
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
      const refreshToken = authAPI.getRefreshToken()
      
      if (accessToken || refreshToken) {
        // Validate both tokens
        const tokenValidation = validateTokens(accessToken, refreshToken)
        
        if (tokenValidation.shouldLogout) {
          console.log('❌ Both tokens are invalid, logging out user')
          authAPI.clearTokens()
          setUser(null)
          return
        }
        
        if (tokenValidation.canRefresh) {
          console.log('🔄 Access token expired, attempting refresh...')
          try {
            const newToken = await authAPI.refreshAccessToken()
            if (!newToken) {
              console.log('❌ Token refresh failed, logging out user')
              authAPI.clearTokens()
              setUser(null)
              return
            }
            console.log('✅ Token refreshed successfully')
          } catch (refreshError) {
            console.error('❌ Token refresh error:', refreshError)
            authAPI.clearTokens()
            setUser(null)
            return
          }
        }

        const response = await authAPI.getProfile()
        setUser(response.user)
      } else {
        setUser(null)
      }
    } catch (error) {
      console.error('Failed to refresh user:', error)
      // Token might be invalid, clear it
      authAPI.clearTokens()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (credentials: LoginCredentials) => {
    try {
      console.log('🔐 Starting login process...', credentials)
      setIsLoading(true)
      const response = await authAPI.login(credentials)
      console.log('✅ Login API response received:', response)
      authAPI.setTokens(response.access_token, response.refresh_token)
      console.log('💾 Tokens stored in localStorage')
      setUser(response.user)
      console.log('👤 User state updated:', response.user)
      console.log('🚀 Redirecting to /...')
      router.push('/')
      console.log('✅ Login process completed')
    } catch (error) {
      console.error('❌ Login failed:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (credentials: RegisterCredentials) => {
    try {
      setIsLoading(true)
      const response = await authAPI.register(credentials)
      authAPI.setTokens(response.access_token, response.refresh_token)
      setUser(response.user)
      router.push('/')
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      await authAPI.logout()
    } catch (error) {
      console.error('Logout API call failed:', error)
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
      console.error('Profile update failed:', error)
      throw error
    }
  }

  const googleLogin = async () => {
    try {
      console.log('🔐 Starting Google OAuth login...')
      setIsLoading(true)
      
      // Get Google OAuth URL from backend
      const response = await authAPI.googleLogin()
      console.log('✅ Google OAuth URL received:', response.auth_url)
      
      // Redirect to Google OAuth
      window.location.href = response.auth_url
      
    } catch (error) {
      console.error('❌ Google OAuth failed:', error)
      setIsLoading(false)
      throw error
    }
  }

  // Initialize auth state on mount
  useEffect(() => {
    refreshUser()
  }, [])

  // Set up periodic token validation
  useEffect(() => {
    if (!user) return

    const validateTokenPeriodically = async () => {
      try {
        const accessToken = authAPI.getAccessToken()
        const refreshToken = authAPI.getRefreshToken()
        
        const tokenValidation = validateTokens(accessToken, refreshToken)
        
        if (tokenValidation.shouldLogout) {
          console.log('❌ Periodic token validation failed - both tokens invalid, logging out user')
          authAPI.clearTokens()
          setUser(null)
          router.push('/auth')
          return
        }
        
        if (tokenValidation.canRefresh) {
          console.log('🔄 Periodic validation - access token expired, attempting refresh...')
          try {
            const newToken = await authAPI.refreshAccessToken()
            if (!newToken) {
              console.log('❌ Periodic refresh failed, logging out user')
              authAPI.clearTokens()
              setUser(null)
              router.push('/auth')
            } else {
              console.log('✅ Periodic token refresh successful')
            }
          } catch (refreshError) {
            console.error('❌ Periodic token refresh error:', refreshError)
            authAPI.clearTokens()
            setUser(null)
            router.push('/auth')
          }
        }
      } catch (error) {
        console.error('Token validation error:', error)
        authAPI.clearTokens()
        setUser(null)
        router.push('/auth')
      }
    }

    // Validate token every 5 minutes
    const interval = setInterval(validateTokenPeriodically, 5 * 60 * 1000)

    // Also validate on window focus (user returns to tab)
    const handleFocus = () => {
      validateTokenPeriodically()
    }
    window.addEventListener('focus', handleFocus)

    return () => {
      clearInterval(interval)
      window.removeEventListener('focus', handleFocus)
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
