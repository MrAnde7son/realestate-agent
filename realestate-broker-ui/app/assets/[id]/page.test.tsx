import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import AssetDetailPage from './page'
import { useRouter } from 'next/navigation'

const mockUseAuth = {
  isAuthenticated: true,
  user: { id: '1', onboarding_flags: {} },
}

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  useSearchParams: vi.fn(() => ({
    get: vi.fn((key: string) => key === 'tab' ? null : null)
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
    // Stub alert for tests
    // @ts-ignore
    global.alert = vi.fn()
    global.fetch = vi.fn((url: string, options?: any) => {
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
          json: async () => ({ plans: { local: [], mavat: [] } })
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

  it('shows error message when message creation fails', async () => {
    await act(async () => {
      render(<AssetDetailPage params={{ id: '1' }} />)
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
      render(<AssetDetailPage params={{ id: '2' }} />)
    })

    await waitFor(() => {
      expect(screen.getByText('חזרה לרשימה')).toBeInTheDocument()
    })

    expect(document.body.textContent).not.toContain('undefined')
    expect(document.body.textContent).not.toContain('NaN')
  })
})
