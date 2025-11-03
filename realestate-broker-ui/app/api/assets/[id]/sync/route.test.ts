import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { NextRequest } from 'next/server'
import { POST } from './route'

const mockCookiesGet = vi.fn()

vi.mock('next/headers', () => ({
  cookies: () => ({
    get: mockCookiesGet
  })
}))

describe('/api/assets/[id]/sync', () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    mockCookiesGet.mockReset()
  })

  afterEach(() => {
    global.fetch = originalFetch
  })

  const createRequest = (assetId = '1', body: Record<string, unknown> = { address: 'Test 123' }) =>
    new NextRequest(`http://localhost/api/assets/${assetId}/sync`, {
      method: 'POST',
      body: JSON.stringify(body),
      headers: {
        'Content-Type': 'application/json'
      }
    })

  it('returns unauthorized response with redirect header when backend returns 401', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      text: async () => JSON.stringify({ error: 'Unauthorized' })
    }) as any

    const response = await POST(createRequest('123'), { params: Promise.resolve({ id: '123' }) })

    expect(response.status).toBe(401)
    expect(response.headers.get('x-redirect-to')).toBe('/auth?redirect=%2Fassets%2F123')
    const data = await response.json()
    expect(data.redirect).toBe('/auth?redirect=%2Fassets%2F123')
    expect(data.error).toBe('נדרש להתחבר מחדש')
  })

  it('includes authorization header when access token cookie exists', async () => {
    mockCookiesGet.mockImplementation((name: string) => {
      if (name === 'access_token') {
        return { value: 'token-123' }
      }
      return undefined
    })

    const backendResponse = {
      ok: true,
      status: 200,
      json: async () => ({ message: 'ok' })
    }

    global.fetch = vi.fn().mockResolvedValue(backendResponse) as any

    const response = await POST(createRequest('456'), { params: Promise.resolve({ id: '456' }) })

    expect(response.status).toBe(200)
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/assets/456/sync'),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer token-123'
        })
      })
    )
  })
})
