import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import AssetDetailPage from './page'
import AssetDetailPageClient from './AssetDetailPageClient'
import { useRouter } from 'next/navigation'

const mockUseAuth = {
  isAuthenticated: true,
  user: { id: '1', onboarding_flags: {} },
}

const searchParamsGetMock = vi.fn((key: string) => null)

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
    trackFeatureUsage: vi.fn()
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

describe('AssetDetailPage', () => {
  const mockUseRouter = { 
    push: vi.fn(),
    replace: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
    ;(useRouter as any).mockReturnValue(mockUseRouter)
    searchParamsGetMock.mockImplementation((key: string) => null)
    // Stub alert for tests
    // @ts-ignore
    global.alert = vi.fn()
    global.fetch = vi.fn((url: string) => {
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
      if (url === '/api/documents/by_category/?asset_id=1') {
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
      expect(element.props.assetId).toBe('server-test')
    }
  })

  it('shows error message when message creation fails', async () => {
    await act(async () => {
      render(<AssetDetailPageClient assetId="1" />)
    })

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
      expect(global.alert).toHaveBeenCalledWith('Quota exceeded')
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

  it('loads rights data only after the rights tab is activated', async () => {
    const callCounts: Record<string, number> = {}

    ;(global.fetch as any).mockImplementation((url: string) => {
      callCounts[url] = (callCounts[url] ?? 0) + 1

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
      if (url === '/api/assets/1/rights') {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            calculated_rights: null,
            tabu_data: [],
            gis_rights: [],
            detailed_rights: [],
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
      if (url === '/api/documents/by_category/?asset_id=1') {
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
        return Promise.resolve({
          ok: false,
          json: async () => ({ details: 'Quota exceeded' })
        })
      }
      return Promise.reject(new Error(`Unhandled fetch call: ${url}`))
    })

    let currentTab: string | null = null
    searchParamsGetMock.mockImplementation((key: string) => (key === 'tab' ? currentTab : null))

    const { rerender } = render(<AssetDetailPageClient assetId="1" />)

    await waitFor(() => {
      expect(screen.getByText('צור הודעת פרסום')).toBeInTheDocument()
    })

    expect(callCounts['/api/assets/1/rights']).toBeUndefined()

    currentTab = 'rights'
    await act(async () => {
      rerender(<AssetDetailPageClient assetId="1" />)
    })

    await waitFor(() => {
      expect(callCounts['/api/assets/1/rights']).toBe(1)
    })
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
      if (url === '/api/documents/by_category/?asset_id=1') {
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
})
