import { render, screen, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: ReactNode }) => (
    <div data-testid="dashboard-layout-mock">{children}</div>
  ),
}))

vi.mock('@/hooks/useAnalytics', async () => {
  const actual = await vi.importActual<any>('@/hooks/useAnalytics')
  return {
    ...actual,
    useAnalytics: () => ({
      trackCalculatorUsage: vi.fn(),
      trackCalculatorCalculation: vi.fn(),
    }),
  }
})

vi.mock('@/lib/auth-context', async () => {
  const actual = await vi.importActual<any>('@/lib/auth-context')
  return {
    ...actual,
    useOptionalAuth: () => ({ user: null }),
  }
})

import MortgageAnalyzePage from '@/app/mortgage/analyze/page'

describe('MortgageAnalyzePage auto-calculated loan amount field', () => {
  it('renders the helper label without overlapping the calculated value', async () => {
    const fetchMock = vi.mocked(global.fetch)
    fetchMock.mockClear()

    const previousFetchCalls = fetchMock.mock.calls.length

    render(<MortgageAnalyzePage />)

    await waitFor(() => {
      expect(fetchMock.mock.calls.length).toBeGreaterThan(previousFetchCalls)
    })

    const loanInput = screen.getByPlaceholderText('2,800,000') as HTMLInputElement

    await waitFor(() => {
      expect(loanInput.value).not.toBe('')
    })

    expect(loanInput).toHaveClass('text-right')
    expect(loanInput).toHaveClass('ps-28')

    const autoLabel = await screen.findByText('מחושב אוטומטית')
    expect(autoLabel).toHaveAttribute('aria-hidden', 'true')
    expect(autoLabel).toHaveAttribute('dir', 'rtl')
    expect(autoLabel).toHaveClass('pointer-events-none')
    expect(autoLabel).toHaveClass('whitespace-nowrap')
  })
})
