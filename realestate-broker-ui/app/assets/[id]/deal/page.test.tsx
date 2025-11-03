import React from 'react'
import { render, screen, fireEvent, waitFor, within, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import DealWorkspacePage from './page'
import DealWorkspacePageClient from './DealWorkspacePageClient'
import { INITIAL_DOCUMENTS } from './mock-data'

const { mockGet, mockRequest, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockRequest: vi.fn(),
  mockPost: vi.fn(),
}))

vi.mock('@/lib/api-client', () => {
  const client = {
    get: mockGet,
    request: mockRequest,
    post: mockPost,
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
  }
  return {
    apiClient: client,
    api: {
      get: client.get,
      post: client.post,
      put: client.put,
      delete: client.delete,
      patch: client.patch,
    },
  }
})

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid='layout'>{children}</div>,
}))

vi.mock('@/components/layout/dashboard-shell', () => ({
  DashboardShell: ({ children }: { children: React.ReactNode }) => <div data-testid='shell'>{children}</div>,
  DashboardHeader: ({ heading, text }: { heading?: React.ReactNode; text?: React.ReactNode }) => (
    <div>
      {heading ? <h1>{heading}</h1> : null}
      {text ? <p>{text}</p> : null}
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
  Button: React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement> & { asChild?: boolean }>(
    ({ children, asChild, ...props }, ref) => {
      if (asChild && React.isValidElement(children)) {
        return React.cloneElement(children, { ...props, ref } as any)
      }
      return (
        <button ref={ref} {...props}>
          {children}
        </button>
      )
    }
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

vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ children, open }: { children: React.ReactNode; open: boolean }) => (
    <div data-testid='dialog'>{open ? children : null}</div>
  ),
  DialogContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogFooter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: React.ReactNode }) => <h2>{children}</h2>,
  DialogDescription: ({ children }: { children: React.ReactNode }) => <p>{children}</p>,
}))

vi.mock('@/components/ui/select', () => ({
  Select: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectValue: ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>,
  SelectContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectItem: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

vi.mock('@/components/ui/label', () => ({
  Label: ({ children, ...props }: React.LabelHTMLAttributes<HTMLLabelElement>) => (
    <label {...props}>{children}</label>
  ),
}))

const backendDeals = [{ id: 999, stage: 'legal' as const }]
let backendDocuments: Array<{
  id: number
  deal: number
  asset: number
  kind: string
  title: string
  storage_url?: string
  visibility_scope: string
  status: string
  created_at: string
  updated_at: string
  extracted_json: Record<string, unknown>
}>

beforeEach(() => {
  vi.clearAllMocks()
  backendDocuments = INITIAL_DOCUMENTS.map((doc, index) => ({
    id: index + 1,
    deal: backendDeals[0].id,
    asset: 501,
    kind: doc.kind,
    title: doc.title,
    storage_url: doc.storageUrl,
    visibility_scope: doc.visibility,
    status: doc.status ?? 'ready',
    created_at: doc.uploadedAt,
    updated_at: doc.uploadedAt,
    extracted_json: {
      summary: doc.summary,
      uploader: doc.uploader,
      linked_offer_id: doc.linkedOfferId,
    },
  }))

  mockGet.mockImplementation((endpoint: string) => {
    if (endpoint.startsWith('/api/deals')) {
      return Promise.resolve({ ok: true, status: 200, data: { deals: backendDeals } })
    }
    if (endpoint.startsWith('/api/deal-workspace/documents')) {
      return Promise.resolve({ ok: true, status: 200, data: { documents: backendDocuments } })
    }
    return Promise.resolve({ ok: false, status: 404, error: 'Not found' })
  })

  mockRequest.mockResolvedValue({ ok: true, status: 200, data: {} })
  mockPost.mockResolvedValue({ ok: true, status: 200, data: {} })
})

describe('DealWorkspacePage', () => {
  it('resolves params promise for server component', async () => {
    const element = await DealWorkspacePage({ params: Promise.resolve({ id: '321' }) })
    expect(React.isValidElement(element)).toBe(true)
    if (React.isValidElement(element)) {
      expect((element as React.ReactElement<{ assetId: string }>).props.assetId).toBe('321')
    }
  })
})

describe('DealWorkspacePageClient', () => {
  it('renders stage badge and parties summary', async () => {
    render(<DealWorkspacePageClient assetId='501' />)

    expect(screen.getByText('נכס 501')).toBeInTheDocument()
    expect(screen.getByText('טיוטות חוזה, הערות וחתימות')).toBeInTheDocument()
    await waitFor(() => {
      const partyMentions = screen.getAllByText(/דנה לוי/)
      expect(partyMentions.length).toBeGreaterThan(0)
    })
  })

  it('filters timeline events by documents category', async () => {
    render(<DealWorkspacePageClient assetId='88' />)

    await screen.findByText('מסמכים ותובנות')

    fireEvent.click(screen.getByRole('button', { name: 'מסמכים' }))

    await screen.findByText('שומת שמאי הועלה')
    expect(screen.queryByText(/הצעת קונה/)).not.toBeInTheDocument()
  })

  it('updates diff preview when editing counter amount', async () => {
    render(<DealWorkspacePageClient assetId='90' />)

    const amountInput = screen.getByLabelText('סכום ההצעה (₪)') as HTMLInputElement
    fireEvent.change(amountInput, { target: { value: '4300000' } })

    const diffRow = await screen.findByText('סכום ההצעה')
    const diffContainer = diffRow.nextSibling as HTMLElement
    expect(diffContainer).toHaveTextContent('4,320,000')
    expect(diffContainer).toHaveTextContent('4,300,000')
  })

  it('filters documents by type', async () => {
    render(<DealWorkspacePageClient assetId='42' />)

    await screen.findByText('מסמכים ותובנות')

    const appraisalFilters = screen.getAllByRole('button', { name: /שומה/ })
    expect(appraisalFilters.length).toBeGreaterThan(0)

    await act(async () => {
      fireEvent.click(appraisalFilters[0])
    })

    await waitFor(() => {
      const appraisalTexts = screen.getAllByText('שומת שמאי')
      expect(appraisalTexts.length).toBeGreaterThan(0)
      expect(screen.queryByText('טיוטת הסכם מכר')).not.toBeInTheDocument()
    }, { timeout: 2000 })
  })

  it('marks legal task as completed and moves it to completed section', async () => {
    render(<DealWorkspacePageClient assetId='55' />)

    const completeButtons = screen.getAllByRole('button', { name: 'סמן כהושלם' })
    fireEvent.click(completeButtons[0])

    const completedHeader = screen.getAllByText('משימות שהושלמו')[0]
    const completedSection = completedHeader.parentElement as HTMLElement
    await waitFor(() => {
      expect(within(completedSection).getByText('תיאום בדיקת חשמל')).toBeInTheDocument()
    })

    const activeHeader = screen.getAllByText('משימות פעילות')[0]
    const activeSection = activeHeader.parentElement as HTMLElement
    expect(within(activeSection).queryByText('תיאום בדיקת חשמל')).not.toBeInTheDocument()
  })

  it('marks mortgage offer as recommended', async () => {
    render(<DealWorkspacePageClient assetId='101' />)

    const rows = screen.getAllByRole('row')
    const mizrahiRow = rows.find(row => within(row).queryByText('מזרחי טפחות'))
    expect(mizrahiRow).toBeDefined()
    const recommendButton = within(mizrahiRow as HTMLElement).getByRole('button', { name: 'סמן כמומלץ' })
    fireEvent.click(recommendButton)

    await waitFor(() => {
      expect(within(mizrahiRow as HTMLElement).getByRole('button', { name: 'מסלול מומלץ' })).toBeInTheDocument()
    })
  })

  it('links a document to the latest offer', async () => {
    render(<DealWorkspacePageClient assetId='77' />)

    await screen.findByText('מסמכים ותובנות')

    const appraisalTitle = await screen.findByText('דו״ח שמאי מילר - עדכון שווי')
    const cardContainer = appraisalTitle.closest('div')?.parentElement?.parentElement?.parentElement as HTMLElement | null
    expect(cardContainer).not.toBeNull()

    const appraisalButton = within(cardContainer as HTMLElement).getByRole('button', { name: 'קשר להצעה האחרונה' })

    fireEvent.click(appraisalButton)

    await waitFor(() => {
      expect(cardContainer?.textContent).toMatch(/מקושר להצעה/)
    })
  })

  it('uploads a document through the dialog and shows it in the list', async () => {
    const newDoc = {
      id: 5000,
      deal: backendDeals[0].id,
      asset: 501,
      kind: 'mortgage',
      title: 'אישור משכנתא בנק הפועלים',
      storage_url: 'https://example.com/mortgage.pdf',
      visibility_scope: 'buyer_side',
      status: 'ready',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      extracted_json: { summary: 'אישור עקרוני עדכני', uploader: 'בנק הפועלים' },
    }

    mockRequest.mockResolvedValueOnce({ ok: true, status: 201, data: { document: newDoc } })

    render(<DealWorkspacePageClient assetId='77' />)

    await screen.findByRole('button', { name: 'העלה מסמך' })
    fireEvent.click(screen.getByRole('button', { name: 'העלה מסמך' }))

    const fileInput = screen.getByLabelText('בחר קובץ') as HTMLInputElement
    const file = new File(['pdf-content'], 'mortgage.pdf', { type: 'application/pdf' })
    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [file] } })
    })

    const submitButton = screen.getByRole('button', { name: 'שמור מסמך' })
    await act(async () => {
      fireEvent.click(submitButton)
    })

    await screen.findByText('אישור משכנתא בנק הפועלים')
    expect(mockRequest).toHaveBeenCalledWith(
      '/api/deal-workspace/documents/upload',
      expect.objectContaining({ method: 'POST', body: expect.any(FormData) })
    )
  })
})
