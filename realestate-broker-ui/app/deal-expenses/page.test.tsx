import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import DealExpensesPage from './page'

const mockTrackCalculatorUsage = vi.fn()
const mockTrackCalculatorCalculation = vi.fn()
const mockTrackCalculatorExport = vi.fn()

const mockSearchParamsGet = vi.fn()

vi.mock('@/hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackCalculatorUsage: mockTrackCalculatorUsage,
    trackCalculatorCalculation: mockTrackCalculatorCalculation,
    trackCalculatorExport: mockTrackCalculatorExport,
    trackFeatureUsage: vi.fn()
  })
}))

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}))

vi.mock('@/components/layout/dashboard-shell', () => ({
  DashboardShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DashboardHeader: ({ title, description }: { title?: React.ReactNode; description?: React.ReactNode }) => (
    <div>
      {title}
      {description}
    </div>
  )
}))

vi.mock('@/components/ui/Card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardDescription: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardBody: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}))

vi.mock('@/components/ui/input', () => ({
  Input: (props: React.InputHTMLAttributes<HTMLInputElement>) => <input {...props} />
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button {...props}>{children}</button>
  )
}))

vi.mock('@/components/ui/switch', () => ({
  Switch: ({ checked, onCheckedChange, ...props }: { checked?: boolean; onCheckedChange?: (value: boolean) => void }) => (
    <input
      type="checkbox"
      checked={checked}
      onChange={event => onCheckedChange?.(event.target.checked)}
      {...props}
    />
  )
}))

vi.mock('@/components/ui/label', () => ({
  Label: ({ children, ...props }: React.LabelHTMLAttributes<HTMLLabelElement>) => <label {...props}>{children}</label>
}))

vi.mock('@/components/ui/Badge', () => ({
  Badge: ({ children }: { children: React.ReactNode }) => <span>{children}</span>
}))

vi.mock('@/components/ui/separator', () => ({
  Separator: () => <hr />
}))

vi.mock('@/components/ui/select', () => ({
  Select: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectItem: ({ children, ...props }: { children: React.ReactNode }) => <div {...props}>{children}</div>,
  SelectTrigger: ({ children, ...props }: { children: React.ReactNode }) => <button {...props}>{children}</button>,
  SelectValue: ({ children }: { children: React.ReactNode }) => <span>{children}</span>
}))

vi.mock('next/navigation', () => ({
  useSearchParams: () => ({
    get: mockSearchParamsGet
  }),
  useRouter: () => ({
    push: vi.fn(),
    prefetch: vi.fn()
  })
}))

vi.mock('@/lib/deal-expenses', () => ({
  calculateServiceCosts: vi.fn(() => ({ total: 0, breakdown: [] })),
  fetchBuildCostEstimate: vi.fn(() => Promise.resolve(null)),
  fetchCostOptions: vi.fn(() => Promise.resolve(null)),
  mergeBuildEstimateIntoDeal: vi.fn((deal) => deal)
}))

describe('DealExpensesPage query param prefill', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    const mockAsset = {
      id: 123,
      address: 'Mock Asset',
      city: 'Tel Aviv',
      price: 2000000,
      area: 90,
      type: 'דירה'
    }

    global.fetch = vi.fn((url: RequestInfo | URL) => {
      if (url === '/api/vat') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ success: false })
        }) as any
      }

      if (url === '/api/assets') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ rows: [mockAsset] })
        }) as any
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({})
      }) as any
    })
  })

  it('prefills selected asset and price from query params', async () => {
    mockSearchParamsGet.mockImplementation((key: string) => {
      if (key === 'assetId') return '123'
      if (key === 'price') return '2500000'
      return null
    })

    render(<DealExpensesPage />)

    await screen.findByText('Mock Asset')

    await waitFor(() => {
      expect((screen.getByLabelText('מחיר הנכס') as HTMLInputElement).value).toBe('2500000')
    })
  })

  it('falls back to asset price when price param missing', async () => {
    mockSearchParamsGet.mockImplementation((key: string) => {
      if (key === 'assetId') return '123'
      return null
    })

    render(<DealExpensesPage />)

    await screen.findByText('Mock Asset')

    await waitFor(() => {
      expect((screen.getByLabelText('מחיר הנכס') as HTMLInputElement).value).toBe('2000000')
    })
  })

  it('uses price param even without asset selection', async () => {
    mockSearchParamsGet.mockImplementation((key: string) => {
      if (key === 'price') return '1750000'
      return null
    })

    render(<DealExpensesPage />)

    await waitFor(() => {
      expect((screen.getByLabelText('מחיר הנכס') as HTMLInputElement).value).toBe('1750000')
    })
  })
})
