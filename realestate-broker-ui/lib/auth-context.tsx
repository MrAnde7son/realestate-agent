'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { User, authAPI, LoginCredentials, RegisterCredentials, ProfileUpdateData } from './auth'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  register: (credentials: RegisterCredentials) => Promise<void>
  logout: () => Promise<void>
  updateProfile: (data: ProfileUpdateData) => Promise<void>
  refreshUser: () => Promise<void>
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
      if (authAPI.isAuthenticated()) {
        const response = await authAPI.getProfile()
        setUser(response.user)
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

  // Initialize auth state on mount
  useEffect(() => {
    refreshUser()
  }, [])

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    updateProfile,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
