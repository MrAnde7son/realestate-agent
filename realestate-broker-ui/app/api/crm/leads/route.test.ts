import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { NextRequest } from 'next/server'

import { GET } from './route'

describe('/api/crm/leads route', () => {
  const token = 'Bearer test-token'

  beforeEach(() => {
    delete process.env.DJANGO_BASE_URL
    process.env.BACKEND_URL = 'http://backend'
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('proxies GET requests to the backend using BACKEND_URL when DJANGO_BASE_URL is not set', async () => {
    const responsePayload = [{ id: 1 }]
    const fetchMock = vi.spyOn(global, 'fetch' as any).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => responsePayload
    } as any)

    const request = new NextRequest('http://localhost/api/crm/leads', {
      headers: { authorization: token }
    })

    const response = await GET(request)

    expect(fetchMock).toHaveBeenCalledWith(
      'http://backend/api/crm/leads/',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ Authorization: token })
      })
    )

    expect(await response.json()).toEqual(responsePayload)
  })

  it('returns 401 when authorization header is missing', async () => {
    const request = new NextRequest('http://localhost/api/crm/leads')

    const response = await GET(request)

    expect(response.status).toBe(401)
  })
})
