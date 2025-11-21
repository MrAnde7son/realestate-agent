/* eslint-env jest */
import React from 'react'
import { render, screen, waitFor, within } from '@testing-library/react'
import '@testing-library/jest-dom'
import MortgageAnalyzePage from './page'
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'

const mockAuthState: { user: any } = { user: null }

// Mock components and hooks
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

vi.mock('@/lib/auth-context', () => ({
  useOptionalAuth: () => mockAuthState
}))

// Mock Next.js router
const mockPush = vi.fn()
const mockReplace = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    prefetch: vi.fn()
  }),
  useSearchParams: () => ({
    get: vi.fn(() => null)
  })
}))

// Create fetch mock
const createFetchMock = () => vi.fn((url: string | URL | Request) => {
  const urlString = typeof url === 'string' 
    ? url 
    : url instanceof URL 
      ? url.toString() 
      : url instanceof Request 
        ? url.url 
        : ''
  
  if (urlString.includes('/api/boi-rate')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: async () => ({
        success: true,
        data: { 
          baseRate: 4.5, 
          lastUpdated: new Date().toISOString(), 
          primeRate: 6 
        }
      })
    } as Response)
  }
  
  if (urlString.includes('/api/analytics')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: async () => ({ success: true })
    } as Response)
  }
  
  return Promise.resolve({
    ok: true,
    status: 200,
    json: async () => ({
      currentInterest: 4.5,
      nextInterestDate: new Date().toISOString()
    })
  } as Response)
})

describe('MortgageAnalyzePage', () => {
  beforeAll(() => {
    global.fetch = createFetchMock()
    
    Object.defineProperty(window.HTMLElement.prototype, 'scrollIntoView', {
      value: vi.fn(),
      writable: true
    })
    
    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/mortgage/analyze',
        search: '',
        hash: '',
        href: 'http://localhost:3000/mortgage/analyze',
        origin: 'http://localhost:3000',
        protocol: 'http:',
        host: 'localhost:3000',
        hostname: 'localhost',
        port: '3000',
        assign: vi.fn(),
        replace: vi.fn(),
        reload: vi.fn()
      },
      writable: true,
      configurable: true
    })
  })

  beforeEach(() => {
    mockAuthState.user = null
    vi.clearAllMocks()
    global.fetch = createFetchMock()
    
    mockTrackCalculatorUsage.mockClear()
    mockTrackCalculatorCalculation.mockClear()
    mockTrackCalculatorExport.mockClear()
    
    mockPush.mockClear()
    mockReplace.mockClear()
  })

  it('renders the mortgage calculator page with initial values', async () => {
    render(<MortgageAnalyzePage />)

    await waitFor(() => {
      expect(screen.getByText('מחשבון משכנתא')).toBeInTheDocument()
    })

    expect(screen.getByText('תכנון תיק משכנתא רב-מסלולי עם תרחישי לחץ')).toBeInTheDocument()
    expect(screen.getByText('נתוני בסיס')).toBeInTheDocument()

    const propertyValueInput = screen.getByDisplayValue('3500000') as HTMLInputElement
    expect(propertyValueInput.value).toBe('3500000')

    const monthlyIncomeInput = screen.getByDisplayValue('65000') as HTMLInputElement
    expect(monthlyIncomeInput.value).toBe('65000')
  })

  it('keeps the calculate CTA visible while scrolling', async () => {
    render(<MortgageAnalyzePage />)

    const stickyBar = await screen.findByTestId('sticky-action-bar')
    expect(stickyBar).toBeInTheDocument()
    expect(stickyBar.className).toContain('sticky')
    expect(within(stickyBar).getByRole('button', { name: /חשב תיק/ })).toBeInTheDocument()
  })

  it('prefills equity from authenticated user profile', async () => {
    mockAuthState.user = { role: 'private', equity: 250000 }

    render(<MortgageAnalyzePage />)

    await waitFor(() => {
      expect(screen.getByText('מחשבון משכנתא')).toBeInTheDocument()
    })

    const equityInput = await screen.findByLabelText('הון עצמי')
    expect((equityInput as HTMLInputElement).value).toBe('250000')
  })
})
