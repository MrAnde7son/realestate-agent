import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest'
import { POST } from './route'
import { NextRequest } from 'next/server'

const originalFetch = global.fetch

describe('/api/assets/[id]/share-message', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
  })

  afterAll(() => {
    global.fetch = originalFetch
  })

  it('returns message from backend', async () => {
    ;(global.fetch as any).mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => 'application/json' },
      json: async () => ({ message: 'msg' }),
      text: async () => ''
    })
    const req = new NextRequest(
      'http://localhost:3000/api/assets/1/share-message',
      {
        method: 'POST',
        body: JSON.stringify({ language: 'en' }),
        headers: { 'Content-Type': 'application/json' }
      }
    )
    const params = { id: '1' }
    const res = await POST(req, { params })
    const data = await res.json()
    expect(res.status).toBe(200)
    expect(data.message).toBe('msg')
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/assets/1/share-message/',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: 'en' })
      }
    )
  })

  it('handles backend failure', async () => {
    ;(global.fetch as any).mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      headers: { get: () => 'application/json' },
      text: async () => 'fail'
    })

    const req = new NextRequest(
      'http://localhost:3000/api/assets/1/share-message',
      {
        method: 'POST',
        body: JSON.stringify({ language: 'en' }),
        headers: { 'Content-Type': 'application/json' }
      }
    )
    const params = { id: '1' }
    const res = await POST(req, { params })
    expect(res.status).toBe(500)
  })
})
