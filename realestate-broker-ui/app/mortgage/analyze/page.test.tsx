/* eslint-env jest */
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import MortgageAnalyzePage from './page'
import { vi } from 'vitest'

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}))

vi.mock('@/hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackCalculatorUsage: vi.fn(),
    trackCalculatorCalculation: vi.fn(),
    trackCalculatorExport: vi.fn()
  })
}))

vi.mock('@/lib/auth-context', () => ({
  useOptionalAuth: () => ({ user: null })
}))

global.fetch = vi.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({
      success: true,
      data: { baseRate: 4.5, lastUpdated: new Date().toISOString(), primeRate: 6 }
    })
  } as any)
) as any

describe('MortgageAnalyzePage', () => {
  it('renders multi-track portfolio summary', async () => {
    render(<MortgageAnalyzePage />)

    expect(screen.getByText('מחשבון משכנתא')).toBeInTheDocument()
    expect(screen.getByText('תכנון תיק משכנתא רב-מסלולי עם תרחישי לחץ')).toBeInTheDocument()
    expect(screen.getByText('נתוני בסיס')).toBeInTheDocument()
    expect(screen.getByText('מסלולים')).toBeInTheDocument()

    const propertyValueInput = screen.getByDisplayValue('3500000') as HTMLInputElement
    expect(propertyValueInput).toBeInTheDocument()
    expect(propertyValueInput.value).toBe('3500000')

    const monthlyIncomeInput = screen.getByDisplayValue('65000') as HTMLInputElement
    expect(monthlyIncomeInput.value).toBe('65000')

    await waitFor(() => {
      expect(screen.getAllByText('תשלום ראשון').length).toBeGreaterThan(0)
    })

    const currencyCells = screen.getAllByText((content: string) => content.includes('₪'))
    expect(currencyCells.length).toBeGreaterThan(0)

    expect(screen.getByText('סיכום תיק')).toBeInTheDocument()
    expect(screen.getByText('פירוט מסלולים')).toBeInTheDocument()
  })
})
