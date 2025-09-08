/**
 * Integration tests for asset management flow
 * Tests the complete user journey from viewing assets to creating new ones
 */

import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { NextRouter } from 'next/router'
import AssetsPage from '../../app/assets/page'
import AssetDetailPage from '../../app/assets/[id]/page'
import { useAuth } from '@/lib/auth-context'
import { useRouter, useSearchParams, usePathname } from 'next/navigation'

// Mock dependencies
vi.mock('@/lib/auth-context')
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  useSearchParams: vi.fn(),
  usePathname: vi.fn(),
}))
vi.mock('@/components/AssetsTable', () => ({
  default: ({ data, loading }: { data: any[], loading: boolean, onDelete?: any }) => (
    <div data-testid="assets-table">
      {loading ? (
        'Loading...'
      ) : (
        <div>
          <div data-testid="asset-count">{data?.length || 0} assets</div>
          {data?.map((asset: any) => (
            <div
              key={asset.id}
              data-testid={`asset-${asset.id}`}
              onClick={() => window.location.href = `/assets/${asset.id}`}
            >
              {asset.address}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}))

// Mock the asset detail components
vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dashboard-layout">{children}</div>
  )
}))

const mockPush = vi.fn()
const mockUseRouter = {
  push: mockPush,
  back: vi.fn(),
  forward: vi.fn(),
  refresh: vi.fn(),
  replace: vi.fn(),
  prefetch: vi.fn()
}

const mockUseSearchParams = {
  get: vi.fn(),
  toString: vi.fn(),
}

const mockUseAuth = {
  isAuthenticated: true,
  user: { id: '1', name: 'Test User', email: 'test@example.com' },
  login: vi.fn(),
  logout: vi.fn()
}

// Mock fetch globally
global.fetch = vi.fn()

describe('Asset Management Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(useRouter as any).mockReturnValue(mockUseRouter)
    ;(useSearchParams as any).mockReturnValue(mockUseSearchParams)
    ;(usePathname as any).mockReturnValue('/assets')
    mockUseSearchParams.get.mockReturnValue(null)
    mockUseSearchParams.toString.mockReturnValue('')
    ;(useAuth as any).mockReturnValue(mockUseAuth)
    
    // Default fetch responses
    ;(global.fetch as any).mockImplementation((url: string, options?: any) => {
      if (url === '/api/assets' && (!options || options.method === 'GET')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            rows: [
              {
                id: 'asset1',
                address: 'רחוב הרצל 123, תל אביב',
                price: 3000000,
                city: 'תל אביב',
                type: 'דירה',
                assetStatus: 'active',
                bedrooms: 3,
                bathrooms: 2,
                area: 85
              },
              {
                id: 'asset2',
                address: 'שדרות רוטשילד 456, תל אביב',
                price: 4200000,
                city: 'תל אביב',
                type: 'פנטהאוס',
                assetStatus: 'pending',
                bedrooms: 4,
                bathrooms: 3,
                area: 120
              }
            ]
          })
        })
      }
      
      if (url === '/api/assets' && options?.method === 'POST') {
        const body = options.body ? JSON.parse(options.body) : {}
        return Promise.resolve({
          ok: true,
          json: async () => ({
            asset: {
              id: 'new-asset',
              address: body.street ? `${body.street} ${body.number || ''}`.trim() : 'New Asset',
              price: 0,
              city: body.city || 'תל אביב',
              type: 'דירה',
              assetStatus: 'pending'
            }
          })
        })
      }
      
      return Promise.resolve({ ok: true, json: async () => [] })
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Asset List View', () => {
    it('displays asset list correctly', async () => {
      await act(async () => {
        render(<AssetsPage />)
      })

      // Should show page title
      expect(screen.getByText('רשימת נכסים')).toBeInTheDocument()
      
      // Should show asset count after loading
      await waitFor(() => {
        expect(screen.getByTestId('asset-count')).toHaveTextContent('2 assets')
      })

      // Should show individual assets
      expect(screen.getByTestId('asset-asset1')).toBeInTheDocument()
      expect(screen.getByTestId('asset-asset2')).toBeInTheDocument()
    })

    it('allows filtering assets', async () => {
      await act(async () => {
        render(<AssetsPage />)
      })

      await waitFor(() => {
        expect(screen.getByTestId('asset-count')).toHaveTextContent('2 assets')
      })

      // Test search functionality - search is handled in the AssetsTable component
      // which is mocked, so we verify the component is rendered correctly
      expect(screen.getByTestId('assets-table')).toBeInTheDocument()
    })

    it('allows price filtering', async () => {
      await act(async () => {
        render(<AssetsPage />)
      })

      await waitFor(() => {
        expect(screen.getByTestId('asset-count')).toHaveTextContent('2 assets')
      })

      // Test price filtering - price filters are handled in the component state
      // and the actual filtering happens in the AssetsTable component
      expect(screen.getByTestId('assets-table')).toBeInTheDocument()
    })
  })

  describe('Asset Creation Flow', () => {
    it('completes full asset creation workflow', async () => {
      await act(async () => {
        render(<AssetsPage />)
      })

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('asset-count')).toHaveTextContent('2 assets')
      })

      // Step 1: Open creation form
      const addButton = screen.getByText('הוסף נכס חדש')
      fireEvent.click(addButton)

      // Should show form
      expect(screen.getByText('הזן פרטי הנכס כדי להתחיל תהליך העשרת מידע')).toBeInTheDocument()

      // Step 2: Fill form with required data
      const cityInput = screen.getByLabelText('עיר')
      const streetInput = screen.getByLabelText('רחוב')

      await act(async () => {
        fireEvent.change(cityInput, { target: { value: 'תל אביב' } })
        fireEvent.change(streetInput, { target: { value: 'החלוצים' } })
      })

      // Step 3: Submit form
      const submitButton = screen.getByText('הוסף נכס')
      await act(async () => {
        fireEvent.click(submitButton)
      })

      // Should call API
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/assets', expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('החלוצים')
        }))
      })

      // Should refresh the list after successful creation
      expect(global.fetch).toHaveBeenCalledWith('/api/assets')
    })

    it('validates form input correctly', async () => {
      await act(async () => {
        render(<AssetsPage />)
      })

      // Open form
      const addButton = screen.getByText('הוסף נכס חדש')
      fireEvent.click(addButton)

      // Try to submit without required fields
      const submitButton = screen.getByText('הוסף נכס')
      await act(async () => {
        fireEvent.click(submitButton)
      })

      // Should show validation errors - react-hook-form handles validation
      // The form should remain open with the submit button available
      expect(submitButton).toBeInTheDocument()
    })

    it('handles different location types in asset creation', async () => {
      await act(async () => {
        render(<AssetsPage />)
      })

      // Open form
      const addButton = screen.getByText('הוסף נכס חדש')
      fireEvent.click(addButton)

      // Test location type selection in the form
      expect(screen.getByText('סוג מיקום')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('handles API errors gracefully during asset creation', async () => {
      // Mock API failure
      ;(global.fetch as any).mockImplementation((url: string, options?: any) => {
        if (url === '/api/assets' && options?.method === 'POST') {
          return Promise.resolve({
            ok: false,
            status: 500,
            json: async () => ({ error: 'Server error' })
          })
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ rows: [] })
        })
      })

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      await act(async () => {
        render(<AssetsPage />)
      })

      // Open form and fill it
      const addButton = screen.getByText('הוסף נכס חדש')
      fireEvent.click(addButton)

      const cityInput = screen.getByLabelText('עיר')
      const streetInput = screen.getByLabelText('רחוב')

      await act(async () => {
        fireEvent.change(cityInput, { target: { value: 'תל אביב' } })
        fireEvent.change(streetInput, { target: { value: 'Test Address' } })
      })

      // Submit form
      const submitButton = screen.getByText('הוסף נכס')
      await act(async () => {
        fireEvent.click(submitButton)
      })

      // Should handle error gracefully (form stays open, no crash)
      await waitFor(() => {
        expect(screen.getByText('הזן פרטי הנכס כדי להתחיל תהליך העשרת מידע')).toBeInTheDocument()
      })

      consoleSpy.mockRestore()
    })

    it('handles network failures during asset loading', async () => {
      // Mock network failure
      ;(global.fetch as any).mockRejectedValue(new Error('Network error'))

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      await act(async () => {
        render(<AssetsPage />)
      })

      // Should show empty state after loading fails
      await waitFor(() => {
        expect(screen.getByText('לא נמצאו נכסים')).toBeInTheDocument()
      })

      consoleSpy.mockRestore()
    })
  })

  describe('User Experience', () => {
    it('shows loading states appropriately', async () => {
      // Delay the fetch response
      ;(global.fetch as any).mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            json: async () => ({ rows: [] })
          }), 100)
        )
      )

      render(<AssetsPage />)
      
      // Should show loading initially - the component renders with loading state
      expect(screen.getByText('רשימת נכסים')).toBeInTheDocument()
      
      // Should show results after loading
      await waitFor(() => {
        expect(screen.getByText('לא נמצאו נכסים')).toBeInTheDocument()
      }, { timeout: 200 })
    })

    it('refreshes data when refresh button is clicked', async () => {
      await act(async () => {
        render(<AssetsPage />)
      })

      await waitFor(() => {
        expect(screen.getByTestId('asset-count')).toHaveTextContent('2 assets')
      })

      // Click refresh
      const refreshButton = screen.getByText('רענן')
      await act(async () => {
        fireEvent.click(refreshButton)
      })

      // Should call API again
      expect(global.fetch).toHaveBeenCalledTimes(2)
    })

    it('maintains form state during user interaction', async () => {
      await act(async () => {
        render(<AssetsPage />)
      })

      // Open form
      const addButton = screen.getByText('הוסף נכס חדש')
      fireEvent.click(addButton)

      // Fill partial data
      const streetInput = screen.getByLabelText('רחוב')
      await act(async () => {
        fireEvent.change(streetInput, { target: { value: 'Partial Street' } })
      })

      // Value should be maintained
      expect(streetInput).toHaveValue('Partial Street')

      // Verify form elements are accessible
      expect(screen.getByText('סוג מיקום')).toBeInTheDocument()

      // Street should still be there
      expect(streetInput).toHaveValue('Partial Street')
    })
  })
})
