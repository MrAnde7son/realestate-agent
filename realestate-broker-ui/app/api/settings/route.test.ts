import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

process.env.BACKEND_URL = 'http://backend'

// Create a valid JWT token for testing (expires in 1 hour)
const createMockJWT = () => {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const payload = btoa(JSON.stringify({ 
    exp: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
    iat: Math.floor(Date.now() / 1000),
    sub: 'test-user'
  }))
  const signature = 'mock-signature'
  return `${header}.${payload}.${signature}`
}

const mockCookies = { get: vi.fn() }
vi.mock('next/headers', () => ({ cookies: () => mockCookies }))

import { GET, PUT } from './route'

describe('/api/settings', () => {
  beforeEach(() => {
    mockCookies.get.mockReset()
  })

  it('returns 401 when missing token', async () => {
    mockCookies.get.mockReturnValue(undefined)
    const res = await GET()
    expect(res.status).toBe(401)
  })

  it('proxies GET to backend', async () => {
    mockCookies.get.mockReturnValue({ value: createMockJWT() })
    const settings = { language: 'en' }
    const fetchMock = vi.spyOn(global, 'fetch' as any).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => settings
    } as any)
    const res = await GET()
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/settings/'), expect.objectContaining({
      headers: { Authorization: expect.stringMatching(/^Bearer eyJ/) }
    }))
    const data = await res.json()
    expect(data).toEqual(settings)
  })

  it('proxies PUT to backend', async () => {
    mockCookies.get.mockReturnValue({ value: createMockJWT() })
    const fetchMock = vi.spyOn(global, 'fetch' as any).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ success: true })
    } as any)
    const req = new NextRequest('http://127.0.0.1/api/settings', {
      method: 'PUT',
      body: JSON.stringify({ language: 'he' })
    })
    const res = await PUT(req)
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/settings/'),
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({ language: 'he' })
      })
    )
    const data = await res.json()
    expect(data).toEqual({ success: true })
  })
})
