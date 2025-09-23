import { isTokenExpired as checkTokenExpired } from './token-utils'

export interface User {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  company: string
  role: string
  equity?: number | null
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
  role: 'broker' | 'appraiser' | 'private'
  equity?: number
}

export interface ProfileUpdateData {
  first_name?: string
  last_name?: string
  company?: string
  role?: string
  phone?: string
  notify_email?: boolean
  notify_whatsapp?: boolean
  equity?: number | null
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

export interface PlanInfo {
  plan_name: string
  display_name: string
  description: string
  price: number
  currency: string
  billing_period: string
  is_active: boolean
  is_expired: boolean
  expires_at?: string
  limits: {
    assets: {
      limit: number
      used: number
      remaining: number
    }
    reports: {
      limit: number
      used: number
      remaining: number
    }
    alerts: {
      limit: number
      used: number
      remaining: number
    }
  }
  features: {
    advanced_analytics: boolean
    data_export: boolean
    api_access: boolean
    priority_support: boolean
    custom_reports: boolean
  }
}

export interface PlanType {
  id: number
  name: string
  display_name: string
  description: string
  price: number
  currency: string
  billing_period: string
  asset_limit: number
  report_limit: number
  alert_limit: number
  advanced_analytics: boolean
  data_export: boolean
  api_access: boolean
  priority_support: boolean
  custom_reports: boolean
  is_active: boolean
}

const API_BASE_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

class AuthAPI {

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}/api${endpoint}`
    
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
      const response = await fetch(url, config)
      
      // Handle 401 Unauthorized - just throw error, let user re-login
      if (response.status === 401) {
        this.clearTokens()
        throw new Error('Session expired. Please log in again.')
      }
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      throw error
    }
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify(credentials),
    })
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


  async googleLogin(redirectTo?: string): Promise<{ auth_url: string }> {
    const url = redirectTo ? `/auth/google/login/?redirect=${encodeURIComponent(redirectTo)}` : '/auth/google/login/'
    return this.request<{ auth_url: string }>(url)
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

  async getPlanInfo(): Promise<PlanInfo> {
    return this.request<PlanInfo>('/plans/info/')
  }

  async getPlanTypes(): Promise<{ plans: PlanType[] }> {
    return this.request<{ plans: PlanType[] }>('/plans/types/')
  }

  async upgradePlan(planName: string): Promise<{ message: string }> {
    return this.request<{ message: string }>('/plans/upgrade/', {
      method: 'POST',
      body: JSON.stringify({ plan_name: planName }),
    })
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
      return false
    }

    return true
  }
}

export const authAPI = new AuthAPI()
