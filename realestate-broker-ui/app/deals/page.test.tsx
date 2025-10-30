import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import DealsPage from './page'
import { DEAL_SUMMARIES_MOCK } from '@/app/assets/[id]/deal/mock-data'
import type { DealSummary } from '@/lib/deals/types'

const mockGet = vi.fn()
const mockPost = vi.fn()

vi.mock('next/link', () => ({
  default: ({ children, ...props }: { children: React.ReactNode }) => <a {...props}>{children}</a>,
}))

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid='layout'>{children}</div>,
}))

vi.mock('@/components/layout/dashboard-shell', () => ({
  DashboardShell: ({ children }: { children: React.ReactNode }) => <div data-testid='shell'>{children}</div>,
  DashboardHeader: ({ heading, text, children }: { heading?: React.ReactNode; text?: React.ReactNode; children?: React.ReactNode }) => (
    <div>
      {heading ? <h1>{heading}</h1> : null}
      {text ? <p>{text}</p> : null}
      {children}
    </div>
  ),
}))

vi.mock('@/components/ui/Card', () => ({
  Card: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
  CardHeader: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
  CardTitle: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
  CardDescription: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
  CardContent: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
}))

vi.mock('@/components/ui/Badge', () => ({
  Badge: ({ children, ...props }: React.HTMLAttributes<HTMLSpanElement>) => <span {...props}>{children}</span>,
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => <button {...props}>{children}</button>,
}))

vi.mock('@/components/ui/input', () => ({
  Input: (props: React.InputHTMLAttributes<HTMLInputElement>) => <input {...props} />,
}))

vi.mock('@/components/ui/skeleton', () => ({
  Skeleton: ({ className }: { className?: string }) => <div role='presentation' className={className} />,
}))

vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogDescription: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogFooter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogTrigger: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
  },
}))

const sampleDeals: DealSummary[] = DEAL_SUMMARIES_MOCK

beforeEach(() => {
  mockGet.mockReset()
  mockPost.mockReset()
  mockGet.mockImplementation((endpoint: string) => {
    if (endpoint.startsWith('/api/deals')) {
      return Promise.resolve({ ok: true, data: { deals: sampleDeals } })
    }
    if (endpoint.startsWith('/api/assets')) {
      return Promise.resolve({ ok: true, data: { rows: [] } })
    }
    return Promise.resolve({ ok: false, error: 'unknown endpoint' })
  })
  mockPost.mockResolvedValue({ ok: true, data: { deal: sampleDeals[0] } })
})

describe('DealsPage', () => {
  it('renders deals grouped by stage', async () => {
    render(<DealsPage />)

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/api/deals')
    })

    const firstAddress = sampleDeals[0]?.asset_summary?.address
    const secondAddress = sampleDeals[1]?.asset_summary?.address
    if (!firstAddress || !secondAddress) {
      throw new Error('expected mock deals to include addresses')
    }

    expect(screen.getByText(firstAddress)).toBeInTheDocument()
    expect(screen.getByText(secondAddress)).toBeInTheDocument()
    expect(screen.getAllByText('מו״מ').length).toBeGreaterThan(0)
  })

  it('filters deals by stage when selecting a column button', async () => {
    render(<DealsPage />)
    await waitFor(() => expect(mockGet).toHaveBeenCalledTimes(1))

    mockGet.mockClear()

    const negotiationButtons = screen.getAllByRole('button', { name: 'מו״מ' })
    const filterButton = negotiationButtons.find((button) => !button.hasAttribute('type')) ?? negotiationButtons[0]
    fireEvent.click(filterButton)

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/api/deals?stage=negotiation')
    })
  })

  it('requires selecting an asset before creating a deal', async () => {
    render(<DealsPage />)
    await waitFor(() => expect(mockGet).toHaveBeenCalled())

    const createButton = screen.getByRole('button', { name: 'פתיחת עסקה' })
    fireEvent.click(createButton)

    expect(screen.getByText('בחרו נכס כדי לפתוח עסקה')).toBeInTheDocument()
    expect(mockPost).not.toHaveBeenCalled()
  })

  it('falls back to mock deals when the API returns an error', async () => {
    mockGet.mockImplementationOnce(() => Promise.resolve({ ok: false, error: 'network error' }))

    render(<DealsPage />)

    const fallbackAddress = DEAL_SUMMARIES_MOCK[0]?.asset_summary?.address
    if (!fallbackAddress) {
      throw new Error('expected fallback mock to include address')
    }

    await waitFor(() => {
      expect(screen.getByText(fallbackAddress)).toBeInTheDocument()
    })

    expect(screen.getByText('שגיאה בטעינת העסקאות - מוצגים נתוני דמו')).toBeInTheDocument()
  })
})
