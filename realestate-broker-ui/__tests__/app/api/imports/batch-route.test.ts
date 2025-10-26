import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest'

vi.mock('next/headers', () => ({
  cookies: vi.fn(),
}))

import { NextRequest } from 'next/server'
import { cookies } from 'next/headers'

import { GET, POST } from '@/app/api/imports/[batchId]/route'

type ViMock = ReturnType<typeof vi.fn>
const cookiesMock = cookies as unknown as ViMock

describe('app/api/imports/[batchId] route handlers', () => {
  const originalFetch = globalThis.fetch
  const tokenValue = 'test-token'

  beforeEach(() => {
    const responseBody = { status: 'ok' }
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(responseBody), { status: 200 }),
    )
    globalThis.fetch = fetchMock as unknown as typeof fetch
    cookiesMock.mockReturnValue({
      get: vi.fn().mockReturnValue({ value: tokenValue }),
    })
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.clearAllMocks()
  })

  it('issues an authenticated request to the backend for GET', async () => {
    const request = new NextRequest('http://localhost/api/imports/123')

    const response = await GET(request, { params: { batchId: '123' } })

    const fetchMock = globalThis.fetch as unknown as ViMock
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0]
    expect(String(url)).toBe('http://127.0.0.1:8000/api/imports/123')
    expect(init).toMatchObject({
      cache: 'no-store',
      headers: expect.objectContaining({
        Authorization: `Bearer ${tokenValue}`,
        'Content-Type': 'application/json',
      }),
    })
    expect(await response.json()).toEqual({ status: 'ok' })
    expect(response.status).toBe(200)
  })

  it('uses the first batch id when multiple values provided', async () => {
    const request = new NextRequest('http://localhost/api/imports/123')

    const response = await GET(request, { params: { batchId: ['123', '456'] } })

    const fetchMock = globalThis.fetch as unknown as ViMock
    const [url] = fetchMock.mock.calls[0]
    expect(String(url)).toBe('http://127.0.0.1:8000/api/imports/123')
    expect(response.status).toBe(200)
  })

  it('forwards POST payloads without authorization when the token is missing', async () => {
    cookiesMock.mockReturnValue({
      get: vi.fn().mockReturnValue(undefined),
    })
    const body = { dry_run: true }
    const request = new NextRequest('http://localhost/api/imports/123', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    const response = await POST(request, { params: { batchId: '123' } })

    const fetchMock = globalThis.fetch as unknown as ViMock
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('http://127.0.0.1:8000/api/imports/123')
    expect(init).toMatchObject({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    expect(await response.json()).toEqual({ status: 'ok' })
    expect(response.status).toBe(200)
  })

  it('returns 400 when batch id is missing on GET', async () => {
    const request = new NextRequest('http://localhost/api/imports/')

    const response = await GET(request, { params: {} })

    expect(response.status).toBe(400)
    expect(await response.json()).toEqual({ error: 'Missing batch identifier' })
    expect(globalThis.fetch).not.toHaveBeenCalled()
  })

  it('returns 400 when batch id is missing on POST', async () => {
    const request = new NextRequest('http://localhost/api/imports/', { method: 'POST' })

    const response = await POST(request, { params: {} })

    expect(response.status).toBe(400)
    expect(await response.json()).toEqual({ error: 'Missing batch identifier' })
    expect(globalThis.fetch).not.toHaveBeenCalled()
  })
})
