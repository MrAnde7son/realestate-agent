import React from 'react'
import { render, waitFor, cleanup } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach, beforeAll, afterAll } from 'vitest'
import GoogleCallbackPage from '@/app/auth/google-callback/page'
import { useAuth } from '@/lib/auth-context'
import { useRouter, useSearchParams } from 'next/navigation'

vi.mock('@/lib/auth', () => ({
  authAPI: {
    setTokens: vi.fn(),
  },
}))

vi.mock('@/lib/auth-context')
vi.mock('next/navigation', () => ({
  useSearchParams: vi.fn(),
  useRouter: vi.fn(),
}))

const mockRefreshUser = vi.fn()
const mockReplace = vi.fn()
const mockPush = vi.fn()

const originalLocation = window.location

beforeAll(() => {
  Object.defineProperty(window, 'location', {
    value: {
      ...originalLocation,
      replace: mockReplace,
    },
    writable: true,
  })
})

afterAll(() => {
  Object.defineProperty(window, 'location', {
    value: originalLocation,
  })
})

beforeEach(() => {
  vi.clearAllMocks()
  sessionStorage.clear()
  localStorage.clear()
  ;(useAuth as unknown as vi.Mock).mockReturnValue({ refreshUser: mockRefreshUser })
  ;(useSearchParams as unknown as vi.Mock).mockReturnValue(
    new URLSearchParams('access_token=access123&refresh_token=refresh123')
  )
  ;(useRouter as unknown as vi.Mock).mockReturnValue({ push: mockPush })
})

afterEach(() => {
  cleanup()
})

describe('GoogleCallbackPage', () => {
  it('redirects to stored target after saving tokens', async () => {
    sessionStorage.setItem('post_google_redirect', '/assets')

    render(<GoogleCallbackPage />)

    const { authAPI } = await import('@/lib/auth')

    await waitFor(() => {
      expect(authAPI.setTokens).toHaveBeenCalledWith('access123', 'refresh123')
      expect(mockRefreshUser).toHaveBeenCalled()
      expect(mockReplace).toHaveBeenCalledWith('/assets')
    })

    expect(sessionStorage.getItem('post_google_redirect')).toBeNull()
  })

  it('falls back to assets when no redirect is stored', async () => {
    render(<GoogleCallbackPage />)

    const { authAPI } = await import('@/lib/auth')

    await waitFor(() => {
      expect(authAPI.setTokens).toHaveBeenCalled()
      expect(mockReplace).toHaveBeenCalledWith('/assets')
    })
  })
})
