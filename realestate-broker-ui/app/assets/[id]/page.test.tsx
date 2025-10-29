import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest'
import AssetDetailPage from './page'
import AssetDetailPageClient from './AssetDetailPageClient'
import { useRouter } from 'next/navigation'

// Local mock for matchMedia for this test file only
beforeAll(() => {
  // @ts-ignore
  if (typeof window !== 'undefined' && typeof window.matchMedia !== 'function') {
    // @ts-ignore
    window.matchMedia = (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(() => false),
    }) as any
  }
})

const mockUseAuth = {
  isAuthenticated: true,
  user: { id: '1', onboarding_flags: {} },
}

const searchParamsGetMock = vi.fn<(key: string) => string | null>(() => null)
const trackFeatureUsageMock = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  useSearchParams: vi.fn(() => ({
    get: searchParamsGetMock
  }))
}))
vi.mock('@/lib/auth-context', () => ({
  useAuth: () => mockUseAuth,
}))
vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}))
vi.mock('@/components/ui/page-loader', () => ({
  PageLoader: () => <div>Loading...</div>
}))
vi.mock('@/hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackFeatureUsage: trackFeatureUsageMock
  })
}))
vi.mock('@/components/OnboardingProgress', () => ({
  default: () => <div>Onboarding Progress</div>
}))
vi.mock('@/components/ImageGallery', () => ({
  default: () => <div>Image Gallery</div>
}))
vi.mock('@/components/DataBadge', () => ({
  default: () => <div>Data Badge</div>
}))
vi.mock('@/components/ui/dropdown-menu', async () => {
  const actual = await vi.importActual<typeof import('@/components/ui/dropdown-menu')>(
    '@/components/ui/dropdown-menu'
  )

  return {
    ...actual,
    DropdownMenu: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    DropdownMenuTrigger: ({ children, asChild }: { children: React.ReactNode; asChild?: boolean }) =>
      asChild ? children : <button>{children}</button>,
    DropdownMenuContent: ({ children }: { children: React.ReactNode }) => <div role="menu">{children}</div>,
    DropdownMenuLabel: ({ children }: { children: React.ReactNode }) => (
      <div role="presentation" className="dropdown-menu-label">
        {children}
      </div>
    ),
    DropdownMenuItem: ({ children, onClick, disabled, className }: { children: React.ReactNode; onClick?: () => void; disabled?: boolean; className?: string }) => (
      <div role="menuitem" onClick={disabled ? undefined : onClick} className={className}>{children}</div>
    ),
    DropdownMenuCheckboxItem: ({
      children,
      checked,
      onCheckedChange,
      className,
      disabled,
    }: {
      children: React.ReactNode
      checked?: boolean
      onCheckedChange?: (checked: boolean) => void
      className?: string
      disabled?: boolean
    }) => (
      <div
        role="menuitemcheckbox"
        aria-checked={checked}
        onClick={disabled ? undefined : () => onCheckedChange?.(!checked)}
        className={className}
      >
        {children}
      </div>
    ),
    DropdownMenuRadioGroup: ({
      children,
      onValueChange,
    }: {
      children: React.ReactNode
      onValueChange?: (value: string) => void
    }) => (
      <div role="radiogroup">
        {React.Children.map(children, (child) => {
          if (!React.isValidElement(child)) return child
          const originalOnSelect = (child.props as { onSelect?: (value: string) => void }).onSelect
          return React.cloneElement(child, {
            onSelect: (value: string) => {
              originalOnSelect?.(value)
              onValueChange?.(value)
            },
          })
        })}
      </div>
    ),
    DropdownMenuRadioItem: ({
      children,
      value,
      onSelect,
      className,
      disabled,
    }: {
      children: React.ReactNode
      value: string
      onSelect?: (value: string) => void
      className?: string
      disabled?: boolean
    }) => (
      <div
        role="menuitemradio"
        data-value={value}
        onClick={disabled ? undefined : () => onSelect?.(value)}
        className={className}
      >
        {children}
      </div>
    ),
    DropdownMenuSeparator: () => <hr />,
  }
})
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}))

describe('AssetDetailPage', () => {
  const mockUseRouter = {
    push: vi.fn(),
    replace: vi.fn()
  }
  let lastShareMessagePayload: any = null

  beforeEach(() => {
    vi.clearAllMocks()
    lastShareMessagePayload = null
    searchParamsGetMock.mockImplementation(() => null)
    trackFeatureUsageMock.mockReset()
    ;(useRouter as any).mockReturnValue(mockUseRouter)
    // Stub alert for tests
    // @ts-ignore
    global.alert = vi.fn()
    global.fetch = vi.fn((url: string, options?: RequestInit) => {
      if (url === '/api/assets/1') {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            id: '1',
            address: 'Test Street 1',
            city: 'Tel Aviv',
            type: 'house',
            area: 80,
            price: 1000000,
            pricePerSqm: 12500,
            documents: [],
          })
        })
      }
      if (url === '/api/assets/2') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ id: '2', address: 'Empty', documents: [] })
        })
      }
      if (url === '/api/assets/1/rights') {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            calculated_rights: null,
            tabu_data: [],
            gis_rights: [],
            detailed_rights: []
          })
        })
      }
      if (url.startsWith('/api/documents/table')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            results: [],
            count: 0,
            filters: { category: [], type: [], source: [], status: [] }
          })
        })
      }
      if (url === '/api/documents/by_category?asset_id=1') {
        return Promise.resolve({
          ok: true,
          json: async () => ({})
        })
      }
      if (url === '/api/settings') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ report_sections: ['summary', 'plans'] })
        })
      }
      if (url === '/api/assets/1/share-message') {
        const rawBody = options?.body
        if (typeof rawBody === 'string') {
          lastShareMessagePayload = JSON.parse(rawBody)
        } else if (rawBody instanceof URLSearchParams) {
          lastShareMessagePayload = Object.fromEntries(rawBody.entries())
        } else if (rawBody && typeof rawBody === 'object') {
          lastShareMessagePayload = rawBody
        } else {
          lastShareMessagePayload = rawBody ?? null
        }
        return Promise.resolve({
          ok: false,
          json: async () => ({ details: 'Quota exceeded' })
        })
      }
      if (url === '/api/assets/1/appraisal') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ comps: [], appraisal: null, decisive_appraisals: [], rami_appraisals: [], comparable_transactions: [] })
        })
      }
      if (url === '/api/assets/1/permits') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ permits: [] })
        })
      }
      if (url === '/api/assets/1/plans') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ plans: [] })
        })
      }
      if (url === '/api/assets/1/transactions') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ transactions: [], market_analysis: null })
        })
      }
      if (url === '/api/analytics/track') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ success: true })
        })
      }
      return Promise.reject(new Error('Unhandled fetch call'))
    }) as any
  })

  it('resolves params promise in server wrapper', async () => {
    const element = await AssetDetailPage({ params: Promise.resolve({ id: 'server-test' }) })

    expect(React.isValidElement(element)).toBe(true)
    if (React.isValidElement(element)) {
      expect((element as React.ReactElement<{ assetId: string }>).props.assetId).toBe('server-test')
    }
  })

  it('aborts in-flight asset fetch when assetId changes', async () => {
    const defaultFetch = global.fetch as unknown as vi.Mock
    let firstSignal: AbortSignal | undefined

    const abortingFetch = vi.fn((url: string, options?: RequestInit) => {
      if (url === '/api/assets/1') {
        const signal = options?.signal as AbortSignal | undefined
        firstSignal = signal
        return new Promise((_resolve, reject) => {
          signal?.addEventListener('abort', () => {
            const abortError = new Error('Aborted')
            abortError.name = 'AbortError'
            reject(abortError)
          })
        })
      }
      if (url === '/api/assets/2') {
        const signal = options?.signal as AbortSignal | undefined
        signal?.addEventListener('abort', () => {})
        return Promise.resolve({
          ok: true,
          json: async () => ({ id: '2', address: 'Second Asset', documents: [] })
        })
      }
      return defaultFetch(url, options)
    })

    global.fetch = abortingFetch as any

    const { rerender } = render(<AssetDetailPageClient assetId="1" />)

    await waitFor(() => {
      expect(firstSignal).toBeDefined()
    })

    await act(async () => {
      rerender(<AssetDetailPageClient assetId="2" />)
    })

    await waitFor(() => {
      expect(firstSignal?.aborted).toBe(true)
    })
  })

  it('shows error message when message creation fails', async () => {
    await act(async () => {
      render(<AssetDetailPageClient assetId="1" />)
    })

    await waitFor(() => {
      expect(screen.getByText('עוד פעולות')).toBeInTheDocument()
    })

    // Open the dropdown menu
    const moreActionsButton = screen.getByText('עוד פעולות')
    await act(async () => {
      fireEvent.click(moreActionsButton)
    })

    // Wait for dropdown to be visible and find the share message item
    await waitFor(() => {
      expect(screen.getByText('צור הודעת פרסום')).toBeInTheDocument()
    })

    const shareMessageButton = screen.getByText('צור הודעת פרסום')
    await act(async () => {
      fireEvent.click(shareMessageButton)
    })

    const createButton = await screen.findByText('צור הודעה')
    await act(async () => {
      fireEvent.click(createButton)
    })

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith('Quota exceeded')
      expect(lastShareMessagePayload).toEqual({ language: 'he', provider: 'gemini' })
    })
  })

  it('navigates to deal expenses calculator with asset price prefilled', async () => {
    await act(async () => {
      render(<AssetDetailPageClient assetId="1" />)
    })

    await waitFor(() => {
      expect(screen.getByText('עוד פעולות')).toBeInTheDocument()
    })

    // Open the dropdown menu
    const moreActionsButton = screen.getByText('עוד פעולות')
    await act(async () => {
      fireEvent.click(moreActionsButton)
    })

    // Wait for dropdown to be visible and find the deal expenses item
    await waitFor(() => {
      expect(screen.getByText('חשב הוצאות עסקה')).toBeInTheDocument()
    })

    const ctaButton = screen.getByText('חשב הוצאות עסקה')
    await act(async () => {
      fireEvent.click(ctaButton)
    })

    expect(mockUseRouter.push).toHaveBeenCalledWith('/deal-expenses?assetId=1&price=1000000')
    expect(trackFeatureUsageMock).toHaveBeenCalledWith(
      'deal_expense_cta',
      1,
      expect.objectContaining({
        price: 1000000,
        source: 'asset_detail'
      })
    )
  })

  it('passes provider from search params when creating a share message', async () => {
    searchParamsGetMock.mockImplementation((key: string) =>
      key === 'provider' ? 'openai' : null
    )

    await act(async () => {
      render(<AssetDetailPageClient assetId="1" />)
    })

    await waitFor(() => {
      expect(screen.getByText('עוד פעולות')).toBeInTheDocument()
    })

    // Open the dropdown menu
    const moreActionsButton = screen.getByText('עוד פעולות')
    await act(async () => {
      fireEvent.click(moreActionsButton)
    })

    // Wait for dropdown to be visible and find the share message item
    await waitFor(() => {
      expect(screen.getByText('צור הודעת פרסום')).toBeInTheDocument()
    })

    const button = screen.getByText('צור הודעת פרסום')
    await act(async () => {
      fireEvent.click(button)
    })

    const createButton = await screen.findByText('צור הודעה')
    await act(async () => {
      fireEvent.click(createButton)
    })

    await waitFor(() => {
      expect(lastShareMessagePayload).toEqual({ language: 'he', provider: 'openai' })
    })
  })

  it('renders placeholders for missing optional fields', async () => {
    await act(async () => {
      render(<AssetDetailPageClient assetId="2" />)
    })

    await waitFor(() => {
      expect(screen.getByText('חזרה לרשימה')).toBeInTheDocument()
    })

    expect(document.body.textContent).not.toContain('undefined')
    expect(document.body.textContent).not.toContain('NaN')
  })

  it('avoids duplicate backend fetches when rendered in StrictMode', async () => {
    const callCounts: Record<string, number> = {}
    ;(global.fetch as any).mockImplementation((url: string) => {
      callCounts[url] = (callCounts[url] ?? 0) + 1

      if (url === '/api/assets/1') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ id: '1', address: 'Test Street 1', documents: [] })
        })
      }
      if (url === '/api/assets/1/appraisal') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ comps: [], appraisal: null, decisive_appraisals: [], rami_appraisals: [] })
        })
      }
      if (url === '/api/assets/1/transactions') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ transactions: [], market_analysis: null })
        })
      }
      if (url === '/api/assets/1/permits') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ permits: [] })
        })
      }
      if (url === '/api/assets/1/plans') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ plans: [] })
        })
      }
      if (url === '/api/assets/1/rights') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ calculated_rights: null, tabu_data: [], gis_rights: [], detailed_rights: [] })
        })
      }
      if (url === '/api/documents/by_category?asset_id=1') {
        return Promise.resolve({ ok: true, json: async () => ({}) })
      }
      if (url === '/api/settings') {
        return Promise.resolve({ ok: true, json: async () => ({ report_sections: [] }) })
      }
      return Promise.resolve({ ok: true, json: async () => ({}) })
    })

    await act(async () => {
      render(
        <React.StrictMode>
          <AssetDetailPageClient assetId="1" />
        </React.StrictMode>
      )
    })

    await waitFor(() => {
      expect(callCounts['/api/assets/1']).toBe(1)
    })
  })

  it('loads documents data when switching to the documents tab in StrictMode', async () => {
    const callCounts: Record<string, number> = {}

    ;(global.fetch as any).mockImplementation((input: any) => {
      const url = typeof input === 'string' ? input : input?.url ?? String(input)
      callCounts[url] = (callCounts[url] ?? 0) + 1

      if (url === '/api/assets/1') {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            id: '1',
            address: 'Test Street 1',
            documents: [],
          })
        })
      }
      if (url === '/api/assets/1/appraisal') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ comps: [], appraisal: null, decisive_appraisals: [], rami_appraisals: [] })
        })
      }
      if (url === '/api/assets/1/transactions') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ transactions: [], market_analysis: null })
        })
      }
      if (url === '/api/assets/1/permits') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ permits: [] })
        })
      }
      if (url === '/api/assets/1/plans') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ plans: [] })
        })
      }
      if (url === '/api/assets/1/rights') {
        return Promise.resolve({
          ok: true,
          json: async () => ({ calculated_rights: null, tabu_data: [], gis_rights: [], detailed_rights: [] })
        })
      }
      if (url.startsWith('/api/documents/table')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            results: [
              {
                id: 'doc-1',
                title: 'Doc 1',
                category: 'tabu',
                document_type: 'tabu',
                status: 'active',
                source: 'manual',
              }
            ],
            count: 1,
            filters: { category: [], type: [], source: [], status: [] }
          })
        })
      }
      if (url === '/api/settings') {
        return Promise.resolve({ ok: true, json: async () => ({ report_sections: [] }) })
      }
      return Promise.resolve({ ok: true, json: async () => ({}) })
    })

    await act(async () => {
      render(
        <React.StrictMode>
          <AssetDetailPageClient assetId="1" />
        </React.StrictMode>
      )
    })

    await screen.findByRole('tablist')

    const documentsTab = await screen.findByRole('tab', { name: 'מסמכים' })

    await act(async () => {
      fireEvent.mouseDown(documentsTab)
      fireEvent.click(documentsTab)
      await Promise.resolve()
    })

    await waitFor(() => {
      const documentsCall = Object.keys(callCounts).find((key) => key.startsWith('/api/documents/table'))
      expect(documentsCall).toBeDefined()
      expect(callCounts[documentsCall!]).toBe(1)
    })
  })
})
