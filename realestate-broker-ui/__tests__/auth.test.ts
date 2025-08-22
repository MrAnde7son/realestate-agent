import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { authAPI } from '@/lib/auth'

// Mock global fetch
beforeEach(() => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    headers: new Headers(),
    json: async () => ({ user: {} })
  }) as unknown as typeof fetch
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('authAPI', () => {
  it('uses correct endpoint for updateProfile', async () => {
    await authAPI.updateProfile({ first_name: 'John' })
    const expectedUrl = `${process.env.BACKEND_URL || 'http://localhost:8000'}/api/auth/update-profile/`
    expect(global.fetch).toHaveBeenCalledWith(expectedUrl, expect.objectContaining({
      method: 'PUT'
    }))
  })
})
