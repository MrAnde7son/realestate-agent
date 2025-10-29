import { describe, it, expect, vi } from 'vitest'

vi.mock('./auth', () => ({
  authAPI: {
    getAccessToken: vi.fn(() => null),
    clearTokens: vi.fn(),
  },
}))

import { apiClient } from './api-client'

describe('apiClient', () => {
  it('rethrows abort errors from fetch', async () => {
    const controller = new AbortController()
    const fetchMock = vi.fn((_: string, init?: RequestInit) => {
      const signal = init?.signal as AbortSignal | undefined
      return new Promise((_resolve, reject) => {
        signal?.addEventListener('abort', () => {
          const abortError = new Error('Aborted')
          abortError.name = 'AbortError'
          reject(abortError)
        })
      })
    })

    const originalFetch = global.fetch
    global.fetch = fetchMock as any

    const promise = apiClient.get('/test', { signal: controller.signal })

    controller.abort()

    await expect(promise).rejects.toHaveProperty('name', 'AbortError')

    global.fetch = originalFetch as any
  })
})
