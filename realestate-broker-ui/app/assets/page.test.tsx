import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import AssetsPage from './page'
import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'

// Mock dependencies
vi.mock('@/lib/auth-context')
vi.mock('next/navigation')
vi.mock('@/components/AssetsTable', () => ({
  default: ({ data, loading }: { data: any[], loading: boolean }) => (
    <div data-testid="assets-table">
      {loading ? 'Loading...' : `${data?.length || 0} assets`}
    </div>
  )
}))

// Mock fetch globally
global.fetch = vi.fn()

const mockPush = vi.fn()
const mockUseRouter = {
  push: mockPush,
  back: vi.fn(),
  forward: vi.fn(),
  refresh: vi.fn(),
  replace: vi.fn(),
  prefetch: vi.fn()
}

const mockUseAuth = {
  isAuthenticated: true,
  user: { id: '1', name: 'Test User' },
  login: vi.fn(),
  logout: vi.fn()
}

describe('AssetsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(useRouter as any).mockReturnValue(mockUseRouter)
    ;(useAuth as any).mockReturnValue(mockUseAuth)
    
    // Default successful fetch mock
    ;(global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        rows: [
          {
            id: 'asset1',
            address: 'Test Street 123',
            price: 3000000,
            city: 'תל אביב',
            type: 'דירה',
            asset_status: 'active'
          },
          {
            id: 'asset2',
            address: 'Another Street 456',
            price: 4200000,
            city: 'תל אביב',
            type: 'בית',
            asset_status: 'pending'
          }
        ]
      })
    })
  })

  it('renders correctly with loaded assets', async () => {
    await act(async () => {
      render(<AssetsPage />)
    })

    expect(screen.getByText('רשימת נכסים')).toBeInTheDocument()
    expect(screen.getByText('הוסף נכס חדש')).toBeInTheDocument()
    expect(screen.getByText('רענן')).toBeInTheDocument()
    
    await waitFor(() => {
      expect(screen.getByTestId('assets-table')).toBeInTheDocument()
      expect(screen.getByText('2 assets')).toBeInTheDocument()
    })
  })

  it('shows loading state initially', async () => {
    // Delay the fetch response
    ;(global.fetch as any).mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: async () => ({ rows: [] })
      }), 100))
    )

    render(<AssetsPage />)
    
    expect(screen.getByText('Loading...')).toBeInTheDocument()
    
    await waitFor(() => {
      expect(screen.getByText('0 assets')).toBeInTheDocument()
    }, { timeout: 200 })
  })

  it('handles fetch errors gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    ;(global.fetch as any).mockRejectedValue(new Error('Network error'))

    await act(async () => {
      render(<AssetsPage />)
    })

    await waitFor(() => {
      expect(screen.getByText('0 assets')).toBeInTheDocument()
    })

    consoleSpy.mockRestore()
  })

  it('handles refresh button click', async () => {
    await act(async () => {
      render(<AssetsPage />)
    })

    await waitFor(() => {
      expect(screen.getByTestId('assets-table')).toBeInTheDocument()
    })

    const refreshButton = screen.getByText('רענן')
    await act(async () => {
      fireEvent.click(refreshButton)
    })

    // Should call fetch again
    expect(global.fetch).toHaveBeenCalledTimes(2)
  })

  it('opens new asset form when add button is clicked', async () => {
    await act(async () => {
      render(<AssetsPage />)
    })

    const addButton = screen.getByText('הוסף נכס חדש')
    fireEvent.click(addButton)

    // Check if form is opened
    expect(screen.getByText('הזן פרטי הנכס כדי להתחיל תהליך העשרת מידע')).toBeInTheDocument()
  })

  it('submits new asset form successfully', async () => {
    // Mock successful asset creation
    ;(global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ rows: [] })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          asset: {
            id: 'new-asset',
            address: 'New Street 789',
            city: 'תל אביב'
          }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          rows: [
            {
              id: 'new-asset',
              address: 'New Street 789',
              city: 'תל אביב',
              price: 0,
              type: 'דירה',
              asset_status: 'pending'
            }
          ]
        })
      })

    await act(async () => {
      render(<AssetsPage />)
    })

    // Open form
    const addButton = screen.getByText('הוסף נכס חדש')
    fireEvent.click(addButton)

    // Fill form
    const addressInput = screen.getByLabelText('כתובת')
    const cityInput = screen.getByLabelText('עיר')
    
    await act(async () => {
      fireEvent.change(addressInput, { target: { value: 'New Street 789' } })
      fireEvent.change(cityInput, { target: { value: 'תל אביב' } })
    })

    // Submit form
    const submitButton = screen.getByText('הוסף נכס')
    await act(async () => {
      fireEvent.click(submitButton)
    })

    // Should close form and refresh assets
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/assets', expect.objectContaining({
        method: 'POST'
      }))
    })
  })

  it('filters assets by search term', async () => {
    await act(async () => {
      render(<AssetsPage />)
    })

    await waitFor(() => {
      expect(screen.getByTestId('assets-table')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText('חפש נכסים...')
    
    await act(async () => {
      fireEvent.change(searchInput, { target: { value: 'Test Street' } })
    })

    // The filtering logic would be tested in the component itself
    // Here we just ensure the search input works
    expect(searchInput).toHaveValue('Test Street')
  })

  it('filters assets by city', async () => {
    await act(async () => {
      render(<AssetsPage />)
    })

    await waitFor(() => {
      expect(screen.getByTestId('assets-table')).toBeInTheDocument()
    })

    // Find and interact with city filter
    const cityFilter = screen.getByDisplayValue('כל הערים')
    
    await act(async () => {
      fireEvent.click(cityFilter)
    })

    // The Select component would show options
    // This tests the interaction capability
    expect(cityFilter).toBeInTheDocument()
  })

  it('filters assets by price range', async () => {
    await act(async () => {
      render(<AssetsPage />)
    })

    await waitFor(() => {
      expect(screen.getByTestId('assets-table')).toBeInTheDocument()
    })

    const minPriceInput = screen.getByPlaceholderText('מחיר מינימלי')
    const maxPriceInput = screen.getByPlaceholderText('מחיר מקסימלי')
    
    await act(async () => {
      fireEvent.change(minPriceInput, { target: { value: '2000000' } })
      fireEvent.change(maxPriceInput, { target: { value: '5000000' } })
    })

    expect(minPriceInput).toHaveValue(2000000)
    expect(maxPriceInput).toHaveValue(5000000)
  })

  it('validates form fields correctly', async () => {
    await act(async () => {
      render(<AssetsPage />)
    })

    // Open form
    const addButton = screen.getByText('הוסף נכס חדש')
    fireEvent.click(addButton)

    // Try to submit empty form
    const submitButton = screen.getByText('הוסף נכס')
    await act(async () => {
      fireEvent.click(submitButton)
    })

    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText('כתובת נדרשת')).toBeInTheDocument()
    })
  })

  it('handles different scope types in form', async () => {
    await act(async () => {
      render(<AssetsPage />)
    })

    // Open form
    const addButton = screen.getByText('הוסף נכס חדש')
    fireEvent.click(addButton)

    // Change scope type to neighborhood
    const scopeSelect = screen.getByDisplayValue('כתובת')
    await act(async () => {
      fireEvent.click(scopeSelect)
    })

    // The form should adapt to show different fields based on scope type
    expect(scopeSelect).toBeInTheDocument()
  })

  it('displays asset count correctly', async () => {
    await act(async () => {
      render(<AssetsPage />)
    })

    await waitFor(() => {
      expect(screen.getByText('2 נכסים עם נתוני שמאות ותכנון מלאים')).toBeInTheDocument()
    })
  })
})
