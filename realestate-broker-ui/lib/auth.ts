export interface User {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  company: string
  role: string
  is_verified: boolean
  created_at?: string
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
}

export interface ChangePasswordData {
  current_password: string
  new_password: string
}

const API_BASE_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

class AuthAPI {
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

  // Token management
  setTokens(accessToken: string, refreshToken: string): void {
    if (typeof window !== 'undefined') {
      // Store in localStorage
      localStorage.setItem('access_token', accessToken)
      localStorage.setItem('refresh_token', refreshToken)
      
      // Also set cookies for middleware with proper settings
      const cookieOptions = [
        `path=/`,
        `max-age=3600`,
        `SameSite=Lax`,
        `secure=${window.location.protocol === 'https:'}`,
        `domain=${window.location.hostname}`
      ].join('; ')
      
      document.cookie = `access_token=${accessToken}; ${cookieOptions}`
      document.cookie = `refresh_token=${refreshToken}; ${cookieOptions.replace('max-age=3600', 'max-age=86400')}`
      
      console.log('🍪 Cookies set:', {
        access_token: accessToken ? 'set' : 'not set',
        refresh_token: refreshToken ? 'set' : 'not set',
        domain: window.location.hostname,
        secure: window.location.protocol === 'https:'
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
      const domain = window.location.hostname
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
}

export const authAPI = new AuthAPI()
