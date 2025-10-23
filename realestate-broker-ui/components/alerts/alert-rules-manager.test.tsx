import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import AlertRulesManager from './alert-rules-manager'

vi.mock('@/lib/auth-context', () => ({
  useAuth: () => ({
    refreshUser: vi.fn(),
  }),
}))

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()

vi.mock('@/lib/api-client', () => ({
  api: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    put: (...args: any[]) => mockPut(...args),
    delete: vi.fn(),
    patch: vi.fn(),
  },
}))

describe('AlertRulesManager', () => {
  beforeEach(() => {
    mockGet.mockReset()
    mockPost.mockReset()
    mockPut.mockReset()
  })

  it('automatically adds a new rule when requested after loading existing rules', async () => {
    mockGet.mockImplementation((endpoint: string) => {
      if (endpoint === '/api/alerts') {
        return Promise.resolve({
          ok: true,
          data: {
            rules: [
              {
                id: 1,
                trigger_type: 'PRICE_DROP',
                params: { pct: 5 },
                channels: ['email'],
                frequency: 'immediate',
                scope: 'global',
                active: true,
              },
            ],
          },
        })
      }

      if (endpoint === '/api/assets') {
        return Promise.resolve({
          ok: true,
          data: { rows: [] },
        })
      }

      return Promise.resolve({ ok: true })
    })

    const handleAutoCreateHandled = vi.fn()

    render(
      <AlertRulesManager
        autoCreateNewRule
        onAutoCreateHandled={handleAutoCreateHandled}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('עדכן')).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText('שמור')).toBeInTheDocument()
    })

    expect(handleAutoCreateHandled).toHaveBeenCalledTimes(1)
    expect(mockGet).toHaveBeenCalledWith('/api/alerts')
  })
})
