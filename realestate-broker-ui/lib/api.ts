import { API_BASE } from './config'

async function handleResponse(res: Response) {
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  return res.json()
}

export async function register(username: string, password: string, email?: string) {
  const res = await fetch(`${API_BASE}/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, password, email }),
  })
  return handleResponse(res)
}

export async function login(username: string, password: string) {
  const res = await fetch(`${API_BASE}/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  })
  return handleResponse(res)
}

export async function googleLogin(token: string) {
  const res = await fetch(`${API_BASE}/google/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ token }),
  })
  return handleResponse(res)
}

export async function logout() {
  const res = await fetch(`${API_BASE}/logout/`, {
    method: 'POST',
    credentials: 'include',
  })
  return handleResponse(res)
}

export async function fetchProfile() {
  const res = await fetch(`${API_BASE}/profile/`, {
    method: 'GET',
    credentials: 'include',
  })
  return handleResponse(res)
}

export async function updateProfile(data: Record<string, any>) {
  const res = await fetch(`${API_BASE}/profile/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  })
  return handleResponse(res)
}

export async function fetchSettings() {
  const res = await fetch(`${API_BASE}/settings/`, {
    method: 'GET',
    credentials: 'include',
  })
  return handleResponse(res)
}

export async function updateSettings(data: Record<string, any>) {
  const res = await fetch(`${API_BASE}/settings/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  })
  return handleResponse(res)
}
