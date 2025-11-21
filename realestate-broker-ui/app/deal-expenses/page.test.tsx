/* eslint-env jest */
import React from 'react'
import { render, screen, waitFor, within } from '@testing-library/react'
import '@testing-library/jest-dom'
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import DealExpensesPage from './page'

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}))

const mockTrackCalculatorUsage = vi.fn()
const mockTrackCalculatorCalculation = vi.fn()
const mockTrackCalculatorExport = vi.fn()

vi.mock('@/hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackCalculatorUsage: mockTrackCalculatorUsage,
    trackCalculatorCalculation: mockTrackCalculatorCalculation,
    trackCalculatorExport: mockTrackCalculatorExport
  })
}))

vi.mock('next/navigation', () => ({
  useSearchParams: () => ({
    get: vi.fn(() => null)
  })
}))

const createFetchMock = () =>
  vi.fn((url: string | URL | Request) => {
    const urlString =
      typeof url === 'string'
        ? url
        : url instanceof URL
          ? url.toString()
          : url instanceof Request
            ? url.url
            : ''

    if (urlString.includes('/api/vat')) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ success: true, data: { rate: 0.18, updatedAt: '2024-01-01' } })
      } as Response)
    }

    if (urlString.includes('/api/assets')) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ rows: [] })
      } as Response)
    }

    if (urlString.includes('/api/cost/options')) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ regions: [], qualities: [], scopes: [] })
      } as Response)
    }

    return Promise.resolve({
      ok: true,
      json: async () => ({})
    } as Response)
  })

describe('DealExpensesPage', () => {
  beforeAll(() => {
    global.fetch = createFetchMock()
  })

  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = createFetchMock()
  })

  it('renders a sticky calculate CTA', async () => {
    render(<DealExpensesPage />)

    await waitFor(() => {
      expect(screen.getByText('מחשבון הוצאות עסקה')).toBeInTheDocument()
    })

    const stickyBar = await screen.findByTestId('sticky-action-bar')
    expect(stickyBar).toBeInTheDocument()
    expect(stickyBar.className).toContain('sticky')
    expect(within(stickyBar).getByRole('button', { name: /חשב הוצאות/ })).toBeInTheDocument()
  })
})
