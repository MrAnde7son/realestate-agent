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
    const expectedUrl = `${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/api/auth/update-profile`
    expect(global.fetch).toHaveBeenCalledWith(expectedUrl, expect.objectContaining({
      method: 'PUT'
    }))
  })

  it('sends preference fields when updating profile', async () => {
    await authAPI.updateProfile({ preference_city: 'תל אביב', preference_area_min: 70, preference_area_max: 120 })

    const lastCall = (global.fetch as any).mock.calls.at(-1)
    const options = lastCall[1]
    const body = JSON.parse(options.body)

    expect(body.preference_city).toBe('תל אביב')
    expect(body.preference_area_min).toBe(70)
    expect(body.preference_area_max).toBe(120)
  })
})
