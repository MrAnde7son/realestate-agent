/**
 * Centralized API client that handles authentication and 401 responses
 */

import { authAPI } from './auth'

export interface ApiResponse<T = any> {
  data?: T
  error?: string
  status: number
  ok: boolean
}

class ApiClient {
  private baseUrl = ''

  /**
   * Make an authenticated API request with automatic 401 handling
   */
  async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`
    
    // Get the access token
    const token = authAPI.getAccessToken()
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    }

    try {
      console.log('📡 API Client - Making request:', { url, method: options.method || 'GET' })
      
      const response = await fetch(url, config)
      
      console.log('📨 API Client - Response:', { 
        url, 
        status: response.status, 
        ok: response.ok 
      })
      
      // Handle 401 Unauthorized - token expired or invalid
      if (response.status === 401) {
        console.log('🔄 API Client - 401 received, clearing tokens and redirecting to login')
        
        // Clear tokens
        authAPI.clearTokens()
        
        // Redirect to login page
        if (typeof window !== 'undefined') {
          window.location.href = '/auth'
        }
        
        return {
          data: undefined,
          error: 'Session expired. Please log in again.',
          status: 401,
          ok: false
        }
      }
      
      // Parse response data
      let data: T | undefined
      let error: string | undefined
      
      try {
        data = await response.json()
      } catch (parseError) {
        console.error('❌ API Client - Failed to parse response:', parseError)
        error = 'Failed to parse response'
      }
      
      if (!response.ok) {
        error = (data as any)?.error || `HTTP error! status: ${response.status}`
      }
      
      return {
        data,
        error,
        status: response.status,
        ok: response.ok
      }
      
    } catch (error) {
      console.error('❌ API Client - Request failed:', error)
      return {
        data: undefined,
        error: error instanceof Error ? error.message : 'Request failed',
        status: 0,
        ok: false
      }
    }
  }

  /**
   * GET request
   */
  async get<T = any>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'GET' })
  }

  /**
   * POST request
   */
  async post<T = any>(endpoint: string, data?: any, options: RequestInit = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /**
   * PUT request
   */
  async put<T = any>(endpoint: string, data?: any, options: RequestInit = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /**
   * DELETE request
   */
  async delete<T = any>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' })
  }

  /**
   * PATCH request
   */
  async patch<T = any>(endpoint: string, data?: any, options: RequestInit = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    })
  }
}

// Export singleton instance
export const apiClient = new ApiClient()

// Export convenience functions
export const api = {
  get: <T = any>(endpoint: string, options?: RequestInit) => apiClient.get<T>(endpoint, options),
  post: <T = any>(endpoint: string, data?: any, options?: RequestInit) => apiClient.post<T>(endpoint, data, options),
  put: <T = any>(endpoint: string, data?: any, options?: RequestInit) => apiClient.put<T>(endpoint, data, options),
  delete: <T = any>(endpoint: string, options?: RequestInit) => apiClient.delete<T>(endpoint, options),
  patch: <T = any>(endpoint: string, data?: any, options?: RequestInit) => apiClient.patch<T>(endpoint, data, options),
}
