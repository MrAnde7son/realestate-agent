import { authAPI } from '@/lib/auth'

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  process.env.BACKEND_URL ||
  'http://127.0.0.1:8000'

const ADMIN_USERS_ENDPOINT = `${API_BASE_URL}/api/admin/users/`

export type UserRole = 'admin' | 'broker' | 'appraiser' | 'investor' | 'viewer'

export interface AdminUser {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  full_name: string
  role: UserRole
  phone_number: string | null
  company: string | null
  organization_name: string
  is_active: boolean
  status: 'active' | 'inactive'
  created_at: string
  updated_at: string
  last_login: string | null
  temporary_password?: string
}

export interface AdminUserListResponse {
  data: AdminUser[]
  pagination: {
    count: number
    page: number
    page_size: number
    total_pages: number
  }
}

export interface AdminUserFilters {
  search?: string
  role?: UserRole | 'all'
  status?: 'all' | 'active' | 'inactive'
  registrationDate?: string
  ordering?: string
  page?: number
  pageSize?: number
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = authAPI.getAccessToken()
  if (!token) {
    throw new Error('Authentication required')
  }

  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
    ...options,
  }

  const response = await fetch(endpoint, config)
  if (response.status === 401) {
    authAPI.clearTokens()
    throw new Error('Session expired. Please log in again.')
  }

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}))
    throw new Error(errorPayload.error || response.statusText)
  }

  return response.json()
}

function buildQuery(filters: AdminUserFilters = {}): string {
  const params = new URLSearchParams()

  if (filters.search) {
    params.set('search', filters.search)
  }
  if (filters.role && filters.role !== 'all') {
    params.set('role', filters.role)
  }
  if (filters.status && filters.status !== 'all') {
    params.set('status', filters.status)
  }
  if (filters.registrationDate) {
    params.set('registration_date', filters.registrationDate)
  }
  if (filters.ordering) {
    params.set('ordering', filters.ordering)
  }
  if (filters.page && filters.page > 0) {
    params.set('page', String(filters.page))
  }
  if (filters.pageSize && filters.pageSize > 0) {
    params.set('page_size', String(filters.pageSize))
  }

  const query = params.toString()
  return query ? `?${query}` : ''
}

export async function listAdminUsers(filters: AdminUserFilters = {}): Promise<AdminUserListResponse> {
  const query = buildQuery(filters)
  return request<AdminUserListResponse>(`${ADMIN_USERS_ENDPOINT}${query}`)
}

export interface AdminUserPayload {
  email: string
  first_name?: string
  last_name?: string
  role: UserRole
  phone_number?: string | null
  organization_name?: string
  password?: string
  company?: string
  is_active?: boolean
}

export async function createAdminUser(payload: AdminUserPayload): Promise<AdminUser> {
  const data = await request<{ data: AdminUser }>(ADMIN_USERS_ENDPOINT, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
  return data.data
}

export async function updateAdminUser(id: number, payload: Partial<AdminUserPayload>): Promise<AdminUser> {
  const data = await request<{ data: AdminUser }>(`${ADMIN_USERS_ENDPOINT}${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
  return data.data
}

export async function deleteAdminUser(id: number): Promise<void> {
  await request(`${ADMIN_USERS_ENDPOINT}${id}/`, {
    method: 'DELETE',
  })
}

export async function setAdminUserStatus(id: number, isActive: boolean): Promise<AdminUser> {
  const action = isActive ? 'activate' : 'deactivate'
  const data = await request<{ data: AdminUser }>(`${ADMIN_USERS_ENDPOINT}${id}/${action}/`, {
    method: 'POST',
  })
  return data.data
}

export async function resetAdminUserPassword(id: number): Promise<{ user: AdminUser; temporaryPassword: string }> {
  const data = await request<{ data: AdminUser }>(`${ADMIN_USERS_ENDPOINT}${id}/reset-password/`, {
    method: 'POST',
  })

  return {
    user: data.data,
    temporaryPassword: data.data.temporary_password || '',
  }
}
