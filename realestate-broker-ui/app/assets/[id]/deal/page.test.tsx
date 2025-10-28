import React from 'react'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import DealWorkspacePage from './page'
import DealWorkspacePageClient from './DealWorkspacePageClient'

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid='layout'>{children}</div>,
}))

vi.mock('@/components/layout/dashboard-shell', () => ({
  DashboardShell: ({ children }: { children: React.ReactNode }) => <div data-testid='shell'>{children}</div>,
  DashboardHeader: ({ title, description }: { title?: React.ReactNode; description?: React.ReactNode }) => (
    <div>
      {title ? <h1>{title}</h1> : null}
      {description ? <p>{description}</p> : null}
    </div>
  ),
}))

vi.mock('@/components/ui/Card', () => ({
  Card: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
  CardHeader: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
  CardTitle: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
  CardDescription: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
  CardContent: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
  CardFooter: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
}))

vi.mock('@/components/ui/Badge', () => ({
  Badge: ({ children, ...props }: React.HTMLAttributes<HTMLSpanElement>) => <span {...props}>{children}</span>,
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button {...props}>{children}</button>
  ),
}))

vi.mock('@/components/ui/input', () => ({
  Input: (props: React.InputHTMLAttributes<HTMLInputElement>) => <input {...props} />,
}))

vi.mock('@/components/ui/textarea', () => ({
  Textarea: (props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) => <textarea {...props} />,
}))

vi.mock('@/components/ui/separator', () => ({
  Separator: () => <hr />,
}))

vi.mock('@/components/ui/table', () => ({
  Table: ({ children, ...props }: React.TableHTMLAttributes<HTMLTableElement>) => <table {...props}>{children}</table>,
  TableHeader: ({ children, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) => <thead {...props}>{children}</thead>,
  TableHead: ({ children, ...props }: React.ThHTMLAttributes<HTMLTableCellElement>) => <th {...props}>{children}</th>,
  TableBody: ({ children, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) => <tbody {...props}>{children}</tbody>,
  TableRow: ({ children, ...props }: React.HTMLAttributes<HTMLTableRowElement>) => <tr {...props}>{children}</tr>,
  TableCell: ({ children, ...props }: React.TdHTMLAttributes<HTMLTableCellElement>) => <td {...props}>{children}</td>,
}))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('DealWorkspacePage', () => {
  it('resolves params promise for server component', async () => {
    const element = await DealWorkspacePage({ params: Promise.resolve({ id: '321' }) })
    expect(React.isValidElement(element)).toBe(true)
    if (React.isValidElement(element)) {
      expect(element.props.assetId).toBe('321')
    }
  })
})

describe('DealWorkspacePageClient', () => {
  it('renders stage badge and parties summary', () => {
    render(<DealWorkspacePageClient assetId='501' />)

    expect(screen.getByText('Asset 501')).toBeInTheDocument()
    expect(screen.getByText('Contract drafting & signatures')).toBeInTheDocument()
    const partyMentions = screen.getAllByText(/Dana Levi/)
    expect(partyMentions.length).toBeGreaterThan(0)
  })

  it('filters timeline events by documents category', () => {
    render(<DealWorkspacePageClient assetId='88' />)

    fireEvent.click(screen.getByRole('button', { name: 'Documents' }))

    expect(screen.getByText('Appraisal document uploaded')).toBeInTheDocument()
    expect(screen.queryByText(/Buyer offer/)).not.toBeInTheDocument()
  })

  it('updates diff preview when editing counter amount', async () => {
    render(<DealWorkspacePageClient assetId='90' />)

    const amountInput = screen.getByLabelText('Offer amount (₪)') as HTMLInputElement
    fireEvent.change(amountInput, { target: { value: '4300000' } })

    const diffRow = await screen.findByText('Offer amount')
    const diffContainer = diffRow.nextSibling as HTMLElement
    expect(diffContainer).toHaveTextContent('4,320,000')
    expect(diffContainer).toHaveTextContent('4,300,000')
  })

  it('filters documents by type', async () => {
    render(<DealWorkspacePageClient assetId='42' />)

    const appraisalFilters = screen.getAllByRole('button', { name: /Appraisal/ })
    fireEvent.click(appraisalFilters[0])

    await waitFor(() => {
      expect(screen.getByText('Appraisal Report')).toBeInTheDocument()
      expect(screen.queryByText('Draft Sale Agreement')).not.toBeInTheDocument()
    })
  })

  it('marks legal task as completed and moves it to completed section', async () => {
    render(<DealWorkspacePageClient assetId='55' />)

    const completeButtons = screen.getAllByRole('button', { name: 'Complete task' })
    fireEvent.click(completeButtons[0])

    const completedHeader = screen.getAllByText('Completed')[0]
    const completedSection = completedHeader.parentElement as HTMLElement
    await waitFor(() => {
      expect(within(completedSection).getByText('Title search results review')).toBeInTheDocument()
    })

    const activeHeader = screen.getAllByText('Active')[0]
    const activeSection = activeHeader.parentElement as HTMLElement
    expect(within(activeSection).queryByText('Title search results review')).not.toBeInTheDocument()
  })

  it('marks mortgage offer as recommended', async () => {
    render(<DealWorkspacePageClient assetId='101' />)

    const rows = screen.getAllByRole('row')
    const mizrahiRow = rows.find(row => within(row).queryByText('Mizrahi Tefahot'))
    expect(mizrahiRow).toBeDefined()
    const recommendButton = within(mizrahiRow as HTMLElement).getByRole('button', { name: 'Recommend' })
    fireEvent.click(recommendButton)

    await waitFor(() => {
      expect(within(mizrahiRow as HTMLElement).getByRole('button', { name: 'Recommended' })).toBeInTheDocument()
    })
  })

  it('links a document to the latest offer', async () => {
    render(<DealWorkspacePageClient assetId='77' />)

    const linkButtons = screen.getAllByRole('button', { name: 'Link to latest offer' })
    const appraisalButton = linkButtons.find(button => button.parentElement?.textContent?.includes('Appraisal Report'))
    expect(appraisalButton).toBeDefined()

    fireEvent.click(appraisalButton as HTMLButtonElement)

    await waitFor(() => {
      expect(appraisalButton?.parentElement?.textContent).toMatch(/Linked to offer/)
    })
  })
})
