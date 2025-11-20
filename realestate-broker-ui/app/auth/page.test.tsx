import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import AuthPage from './page'
import { useAuth } from '@/lib/auth-context'
import { useRouter, useSearchParams, usePathname } from 'next/navigation'

vi.mock('@/lib/auth-context', () => ({
  useAuth: vi.fn(),
}))

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  useSearchParams: vi.fn(),
  usePathname: vi.fn(),
}))

describe('AuthPage', () => {
  let mockRouter: ReturnType<typeof createRouterMock>
  let mockSearchParams: ReturnType<typeof createSearchParamsMock>
  let modeParam: string | null
  let redirectParam: string | null
  let googleLoginMock: ReturnType<typeof vi.fn>

  function createRouterMock() {
    return {
      push: vi.fn(),
      replace: vi.fn((url: string) => {
        const [, query = ''] = url.split('?')
        const params = new URLSearchParams(query)
        modeParam = params.get('mode')
        redirectParam = params.get('redirect')
      }),
      prefetch: vi.fn(),
      refresh: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
    }
  }

  function createSearchParamsMock() {
    return {
      get: vi.fn((key: string) => {
        if (key === 'mode') {
          return modeParam
        }
        if (key === 'redirect') {
          return redirectParam
        }
        return null
      }),
      toString: vi.fn(() => {
        const params = new URLSearchParams()
        if (redirectParam) {
          params.set('redirect', redirectParam)
        }
        if (modeParam) {
          params.set('mode', modeParam)
        }
        return params.toString()
      }),
    }
  }

  beforeEach(() => {
    vi.clearAllMocks()

    modeParam = null
    redirectParam = null
    googleLoginMock = vi.fn()

    mockRouter = createRouterMock()
    mockSearchParams = createSearchParamsMock()

    ;(useRouter as any).mockReturnValue(mockRouter)
    ;(useSearchParams as any).mockReturnValue(mockSearchParams)
    ;(usePathname as any).mockReturnValue('/auth')

    ;(useAuth as any).mockReturnValue({
      login: vi.fn(),
      register: vi.fn(),
      googleLogin: googleLoginMock,
      isLoading: false,
    })
  })

  it('switches between login and signup without triggering a push navigation', async () => {
    render(<AuthPage />)

    expect(screen.getByRole('heading', { name: 'ברוכים הבאים' })).toBeInTheDocument()

    const signupTab = screen.getByRole('button', { name: 'הרשמה' })
    fireEvent.click(signupTab)

    expect(mockRouter.push).not.toHaveBeenCalled()
    expect(mockRouter.replace).toHaveBeenCalledWith('/auth?mode=signup', { scroll: false })

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'הרשמה' })).toBeInTheDocument()
    })
    expect(screen.queryByRole('heading', { name: 'ברוכים הבאים' })).not.toBeInTheDocument()

    const loginTab = screen.getByRole('button', { name: 'התחברות' })
    fireEvent.click(loginTab)

    await waitFor(() => {
      expect(mockRouter.replace).toHaveBeenLastCalledWith('/auth', { scroll: false })
      expect(screen.getByRole('heading', { name: 'ברוכים הבאים' })).toBeInTheDocument()
    })
  })

  it('shows the signup form when the mode query parameter is set', async () => {
    modeParam = 'signup'

    render(<AuthPage />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'הרשמה' })).toBeInTheDocument()
    })

    expect(mockRouter.replace).not.toHaveBeenCalled()
    expect(screen.queryByRole('heading', { name: 'ברוכים הבאים' })).not.toBeInTheDocument()
  })

  it('provides a Google signup option that uses redirect parameter', async () => {
    modeParam = 'signup'
    redirectParam = '/welcome'

    render(<AuthPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'הירשם עם Google' })).toBeInTheDocument()
    })

    const googleButton = screen.getByRole('button', { name: 'הירשם עם Google' })
    fireEvent.click(googleButton)

    expect(googleLoginMock).toHaveBeenCalledWith('/welcome')
  })
})

