/* eslint-env jest */
import React from 'react'
import { render, screen, waitFor, within, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import MortgageAnalyzePage from './page'
import { vi } from 'vitest'
const mockAuthState: { user: any } = { user: null }

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
  useOptionalAuth: () => mockAuthState
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
  beforeAll(() => {
    Object.defineProperty(window.HTMLElement.prototype, 'scrollIntoView', {
      value: vi.fn(),
      writable: true
    })
  })

  beforeEach(() => {
    mockAuthState.user = null
    vi.clearAllMocks()
  })

  it('renders multi-track portfolio summary', async () => {
    render(<MortgageAnalyzePage />)

    expect(screen.getByText('מחשבון משכנתא')).toBeInTheDocument()
    expect(screen.getByText('תכנון תיק משכנתא רב-מסלולי עם תרחישי לחץ')).toBeInTheDocument()
    expect(screen.getByText('נתוני בסיס')).toBeInTheDocument()
    expect(screen.getByText('מסלולים')).toBeInTheDocument()
    expect(screen.getByText('הוסף מסלול')).toBeInTheDocument()

    const propertyValueInput = screen.getByDisplayValue('3500000') as HTMLInputElement
    expect(propertyValueInput).toBeInTheDocument()
    expect(propertyValueInput.value).toBe('3500000')

    const monthlyIncomeInput = screen.getByDisplayValue('65000') as HTMLInputElement
    expect(monthlyIncomeInput.value).toBe('65000')

    expect(screen.getByText('בנק ישראל +1%')).toBeInTheDocument()
    expect(screen.getByText('תוספת לעוגן אג״ח')).toBeInTheDocument()
    expect(screen.getByText('פריים (P-0.9)')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getAllByText('תשלום ראשון').length).toBeGreaterThan(0)
    })

    const currencyCells = screen.getAllByText((content: string) => content.includes('₪'))
    expect(currencyCells.length).toBeGreaterThan(0)

    expect(screen.getByText('סיכום תיק')).toBeInTheDocument()
    expect(screen.getByText('פירוט מסלולים')).toBeInTheDocument()
  })

  it('allows collapsing and expanding a tranche editor section', async () => {
    render(<MortgageAnalyzePage />)

    const trancheEditors = await screen.findAllByTestId('tranche-editor')
    expect(trancheEditors.length).toBeGreaterThan(0)

    const firstEditor = trancheEditors[0]
    const collapseButton = within(firstEditor).getByLabelText('צמצום מסלול')
    expect(collapseButton).toBeInTheDocument()

    fireEvent.click(collapseButton)

    await within(firstEditor).findByText('הרחבת מסלול')
    expect(within(firstEditor).queryByText('הנחת מדד שנתית (%)')).not.toBeInTheDocument()

    const expandButton = within(firstEditor).getByLabelText('הרחבת מסלול')
    fireEvent.click(expandButton)

    await within(firstEditor).findByText('צמצום מסלול')
    expect(await within(firstEditor).findByText('הנחת מדד שנתית (%)')).toBeInTheDocument()
  })

  it('prefills equity from authenticated user profile', async () => {
    mockAuthState.user = { role: 'private', equity: 250000 }

    render(<MortgageAnalyzePage />)

    const equityInput = await screen.findByLabelText('הון עצמי')
    expect((equityInput as HTMLInputElement).value).toBe('250000')
  })
})
