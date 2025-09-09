import { isTokenExpired as checkTokenExpired } from './token-utils'

export interface User {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  company: string
  role: string
  phone?: string
  notify_email?: boolean
  notify_whatsapp?: boolean
  is_verified: boolean
  created_at?: string
  onboarding_flags?: {
    connect_payment: boolean
    add_first_asset: boolean
    generate_first_report: boolean
    set_one_alert: boolean
  }
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  user: User
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterCredentials {
  email: string
  password: string
  username: string
  first_name?: string
  last_name?: string
  company?: string
  role?: string
}

export interface ProfileUpdateData {
  first_name?: string
  last_name?: string
  company?: string
  role?: string
  phone?: string
  notify_email?: boolean
  notify_whatsapp?: boolean
}

export interface ChangePasswordData {
  current_password: string
  new_password: string
}

export interface OnboardingStatus {
  steps: {
    add_first_asset: boolean
    generate_first_report: boolean
    set_one_alert: boolean
  }
  completed: boolean
}

const API_BASE_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

class AuthAPI {
  private isRefreshing = false
  private refreshPromise: Promise<string | null> | null = null

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}/api${endpoint}`
    console.log('🔗 Full URL:', url)
    console.log('🔧 Request options:', options)
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    // Add auth token if available
    const token = this.getAccessToken()
    if (token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      }
    }

    try {
      console.log('📡 Sending request...')
      const response = await fetch(url, config)
      console.log('📨 Response status:', response.status)
      console.log('📨 Response headers:', Object.fromEntries(response.headers.entries()))
      
      // Handle token expiration (401 Unauthorized)
      if (response.status === 401 && token) {
        console.log('🔄 Access token expired, attempting refresh...')
        const newToken = await this.refreshAccessToken()
        
        if (newToken) {
          // Retry the request with the new token
          config.headers = {
            ...config.headers,
            Authorization: `Bearer ${newToken}`,
          }
          console.log('🔄 Retrying request with new token...')
          const retryResponse = await fetch(url, config)
          
          if (!retryResponse.ok) {
            const errorData = await retryResponse.json().catch(() => ({}))
            console.error('❌ Retry response not OK:', errorData)
            throw new Error(errorData.error || `HTTP error! status: ${retryResponse.status}`)
          }
          
          const data = await retryResponse.json()
          console.log('📥 Retry response data:', data)
          return data
        } else {
          // Refresh failed, clear tokens and redirect to login
          console.log('❌ Token refresh failed, logging out user')
          this.clearTokens()
          if (typeof window !== 'undefined') {
            window.location.href = '/auth'
          }
          throw new Error('Session expired. Please log in again.')
        }
      }
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        console.error('❌ Response not OK:', errorData)
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log('📥 Response data:', data)
      return data
    } catch (error) {
      console.error('❌ API request failed:', error)
      throw error
    }
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    console.log('🌐 Making login request to:', `${API_BASE_URL}/api/auth/login/`)
    console.log('📤 Request payload:', credentials)
    const response = await this.request<AuthResponse>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify(credentials),
    })
    console.log('📥 Login response received:', response)
    return response
  }

  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(credentials),
    })
  }

  async logout(): Promise<{ message: string }> {
    return this.request<{ message: string }>('/auth/logout/', {
      method: 'POST',
    })
  }

  async getProfile(): Promise<{ user: User }> {
    return this.request<{ user: User }>('/auth/profile/')
  }

  async updateProfile(data: ProfileUpdateData): Promise<{ user: User }> {
    return this.request<{ user: User }>('/auth/update-profile/', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async refreshToken(refreshToken: string): Promise<{
    access_token: string
    refresh_token: string
  }> {
    return this.request<{
      access_token: string
      refresh_token: string
    }>('/auth/refresh/', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
  }

  private async refreshAccessToken(): Promise<string | null> {
    // Prevent multiple simultaneous refresh attempts
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise
    }

    this.isRefreshing = true
    this.refreshPromise = this.performTokenRefresh()

    try {
      const result = await this.refreshPromise
      return result
    } finally {
      this.isRefreshing = false
      this.refreshPromise = null
    }
  }

  private async performTokenRefresh(): Promise<string | null> {
    try {
      const refreshToken = this.getRefreshToken()
      if (!refreshToken) {
        console.log('❌ No refresh token available')
        return null
      }

      console.log('🔄 Refreshing access token...')
      const response = await this.refreshToken(refreshToken)
      
      // Update stored tokens
      this.setTokens(response.access_token, response.refresh_token)
      console.log('✅ Access token refreshed successfully')
      
      return response.access_token
    } catch (error) {
      console.error('❌ Token refresh failed:', error)
      // Clear tokens on refresh failure
      this.clearTokens()
      return null
    }
  }

  async googleLogin(): Promise<{ auth_url: string }> {
    return this.request<{ auth_url: string }>('/auth/google/login/')
  }

  async googleCallback(code: string): Promise<AuthResponse> {
    return this.request<AuthResponse>(`/auth/google/callback/?code=${code}`)
  }

  async changePassword(data: ChangePasswordData): Promise<{ message: string }> {
    return this.request<{ message: string }>('/auth/change-password/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getOnboardingStatus(): Promise<OnboardingStatus> {
    return this.request<OnboardingStatus>('/onboarding-status/')
  }

  // Token management
  private getCookieDomain(): string {
    if (typeof window === 'undefined') return ''
    const parts = window.location.hostname.split('.')
    return parts.length > 2 ? parts.slice(-2).join('.') : parts.join('.')
  }

  setTokens(accessToken: string, refreshToken: string): void {
    if (typeof window !== 'undefined') {
      // Store in localStorage
      localStorage.setItem('access_token', accessToken)
      localStorage.setItem('refresh_token', refreshToken)

      // Also set cookies for middleware with proper settings
      const domain = this.getCookieDomain()
      const secure = window.location.protocol === 'https:'
      const cookieOptions = [`path=/`, `SameSite=Lax`, `domain=${domain}`, secure ? 'secure' : ''].join('; ')

      document.cookie = `access_token=${accessToken}; max-age=3600; ${cookieOptions}`
      document.cookie = `refresh_token=${refreshToken}; max-age=86400; ${cookieOptions}`

      console.log('🍪 Cookies set:', {
        access_token: accessToken ? 'set' : 'not set',
        refresh_token: refreshToken ? 'set' : 'not set',
        domain,
        secure
      })
    }
  }

  getAccessToken(): string | null {
    if (typeof window !== 'undefined') {
      // First try localStorage
      const token = localStorage.getItem('access_token')
      if (token) return token
      
      // Fallback to cookies
      const cookies = document.cookie.split(';')
      const tokenCookie = cookies.find(cookie => cookie.trim().startsWith('access_token='))
      if (tokenCookie) {
        return tokenCookie.split('=')[1]
      }
    }
    return null
  }

  getRefreshToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('refresh_token')
    }
    return null
  }

  clearTokens(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')

      // Also clear cookies with proper domain and path
      const domain = this.getCookieDomain()
      const secure = window.location.protocol === 'https:'

      document.cookie = `access_token=; path=/; domain=${domain}; expires=Thu, 01 Jan 1970 00:00:00 GMT; ${secure ? 'secure;' : ''}`
      document.cookie = `refresh_token=; path=/; domain=${domain}; expires=Thu, 01 Jan 1970 00:00:00 GMT; ${secure ? 'secure;' : ''}`

      console.log('🧹 Tokens cleared from localStorage and cookies')
    }
  }

  isAuthenticated(): boolean {
    if (typeof window !== 'undefined') {
      // Check localStorage first
      if (localStorage.getItem('access_token')) return true
      
      // Check cookies as fallback
      const cookies = document.cookie.split(';')
      return cookies.some(cookie => cookie.trim().startsWith('access_token='))
    }
    return false
  }

  isTokenExpired(token: string): boolean {
    return checkTokenExpired(token)
  }

  async validateToken(): Promise<boolean> {
    const token = this.getAccessToken()
    if (!token) return false

    // Check if token is expired
    if (this.isTokenExpired(token)) {
      console.log('🔄 Access token is expired, attempting refresh...')
      const newToken = await this.refreshAccessToken()
      return !!newToken
    }

    return true
  }
}

export const authAPI = new AuthAPI()
