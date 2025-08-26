import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import AssetDetailPage from './page'
import { useRouter } from 'next/navigation'

vi.mock('next/navigation')
vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}))
vi.mock('@/components/ui/page-loader', () => ({
  PageLoader: () => <div>Loading...</div>
}))

describe('AssetDetailPage', () => {
  const mockUseRouter = { push: vi.fn() }

  beforeEach(() => {
    vi.clearAllMocks()
    ;(useRouter as any).mockReturnValue(mockUseRouter)
    global.fetch = vi.fn((url: string, options?: any) => {
      if (url === '/api/assets/1') {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            id: '1',
            address: 'Test Street 1',
            city: 'Tel Aviv',
            type: 'house',
            netSqm: 80,
            price: 1000000,
            pricePerSqm: 12500,
            documents: [],
          })
        })
      }
      if (url === '/api/assets/1/share-message') {
        return Promise.resolve({
          ok: false,
          json: async () => ({ details: 'Quota exceeded' })
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

    await waitFor(() => {
      expect(screen.getByText('Quota exceeded')).toBeInTheDocument()
    })
  })
})
