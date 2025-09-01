import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

process.env.BACKEND_URL = 'http://backend'

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
    mockCookies.get.mockReturnValue({ value: 'abc' })
    const settings = { language: 'en' }
    const fetchMock = vi.spyOn(global, 'fetch' as any).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => settings
    } as any)
    const res = await GET()
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/settings/'), expect.objectContaining({
      headers: { Authorization: 'Bearer abc' }
    }))
    const data = await res.json()
    expect(data).toEqual(settings)
  })

  it('proxies PUT to backend', async () => {
    mockCookies.get.mockReturnValue({ value: 'abc' })
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
