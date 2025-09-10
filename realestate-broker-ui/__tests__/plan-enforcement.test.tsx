/**
 * @jest-environment jsdom
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import AssetsPage from '@/app/assets/page'
import { authAPI } from '@/lib/auth'

// Mock the authAPI
jest.mock('@/lib/auth', () => ({
  authAPI: {
    getAssets: jest.fn(),
    createAsset: jest.fn(),
    getPlanInfo: jest.fn(),
  },
  useAuth: () => ({
    isAuthenticated: true,
    user: { id: 1, username: 'testuser' }
  })
}))

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  })),
}))

// Mock next/navigation useRouter
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}))

const mockAuthAPI = authAPI as jest.Mocked<typeof authAPI>

describe('Plan Enforcement Integration', () => {
  const mockPlanInfo = {
    plan_name: 'basic',
    display_name: 'Basic Plan',
    description: 'Basic plan for advanced users',
    price: 149.00,
    currency: 'ILS',
    billing_period: 'monthly',
    is_active: true,
    is_expired: false,
    expires_at: null,
    limits: {
      assets: { limit: 25, used: 24, remaining: 1 },
      reports: { limit: 50, used: 5, remaining: 45 },
      alerts: { limit: 25, used: 3, remaining: 22 }
    },
    features: {
      advanced_analytics: true,
      data_export: true,
      api_access: false,
      priority_support: false,
      custom_reports: false
    }
  }

  const mockAssets = [
    {
      id: 1,
      address: 'Test Address 1',
      city: 'Test City',
      price: 100000,
      rooms: 3,
      created_at: '2023-01-01T00:00:00Z'
    },
    {
      id: 2,
      address: 'Test Address 2',
      city: 'Test City',
      price: 200000,
      rooms: 4,
      created_at: '2023-01-02T00:00:00Z'
    }
  ]

  beforeEach(() => {
    jest.clearAllMocks()
    mockAuthAPI.getAssets.mockResolvedValue(mockAssets)
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockPlanInfo)
  })

  it('displays plan information for authenticated users', async () => {
    render(<AssetsPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Basic plan for advanced users')).toBeInTheDocument()
    expect(screen.getByText('149 ₪')).toBeInTheDocument()
    expect(screen.getByText('נכסים: 24/25')).toBeInTheDocument()
  })

  it('shows plan limit dialog when asset creation fails due to limit', async () => {
    // Mock asset creation failure due to plan limit
    mockAuthAPI.createAsset.mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({
        error: 'asset_limit_exceeded',
        message: 'הגעת למגבלת הנכסים בחבילה הנוכחית (Basic Plan).',
        current_plan: 'Basic Plan',
        asset_limit: 25,
        assets_used: 25,
        remaining: 0
      })
    })

    render(<AssetsPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    // Open asset creation form
    const createButton = screen.getByText('הוסף נכס חדש')
    fireEvent.click(createButton)
    
    // Fill form
    fireEvent.change(screen.getByLabelText('כתובת'), { target: { value: 'New Test Address' } })
    fireEvent.change(screen.getByLabelText('עיר'), { target: { value: 'Test City' } })
    fireEvent.change(screen.getByLabelText('מחיר'), { target: { value: '300000' } })
    fireEvent.change(screen.getByLabelText('מספר חדרים'), { target: { value: '5' } })
    
    // Submit form
    const submitButton = screen.getByText('שמור נכס')
    fireEvent.click(submitButton)
    
    // Should show plan limit dialog
    await waitFor(() => {
      expect(screen.getByText('הגעת למגבלת הנכסים!')).toBeInTheDocument()
    })
    
    expect(screen.getByText('הגעת למגבלת הנכסים בחבילה הנוכחית (Basic Plan).')).toBeInTheDocument()
    expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    expect(screen.getByText('25 נכסים')).toBeInTheDocument()
  })

  it('allows asset creation when within plan limits', async () => {
    // Mock successful asset creation
    mockAuthAPI.createAsset.mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({
        id: 3,
        address: 'New Test Address',
        city: 'Test City',
        price: 300000,
        rooms: 5,
        created_at: '2023-01-03T00:00:00Z'
      })
    })

    render(<AssetsPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    // Open asset creation form
    const createButton = screen.getByText('הוסף נכס חדש')
    fireEvent.click(createButton)
    
    // Fill form
    fireEvent.change(screen.getByLabelText('כתובת'), { target: { value: 'New Test Address' } })
    fireEvent.change(screen.getByLabelText('עיר'), { target: { value: 'Test City' } })
    fireEvent.change(screen.getByLabelText('מחיר'), { target: { value: '300000' } })
    fireEvent.change(screen.getByLabelText('מספר חדרים'), { target: { value: '5' } })
    
    // Submit form
    const submitButton = screen.getByText('שמור נכס')
    fireEvent.click(submitButton)
    
    // Should not show plan limit dialog
    await waitFor(() => {
      expect(screen.queryByText('הגעת למגבלת הנכסים!')).not.toBeInTheDocument()
    })
  })

  it('navigates to billing page when upgrade button is clicked', async () => {
    // Mock asset creation failure due to plan limit
    mockAuthAPI.createAsset.mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({
        error: 'asset_limit_exceeded',
        message: 'הגעת למגבלת הנכסים בחבילה הנוכחית (Basic Plan).',
        current_plan: 'Basic Plan',
        asset_limit: 25,
        assets_used: 25,
        remaining: 0
      })
    })

    render(<AssetsPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    // Open asset creation form and trigger limit error
    const createButton = screen.getByText('הוסף נכס חדש')
    fireEvent.click(createButton)
    
    fireEvent.change(screen.getByLabelText('כתובת'), { target: { value: 'New Test Address' } })
    fireEvent.change(screen.getByLabelText('עיר'), { target: { value: 'Test City' } })
    fireEvent.change(screen.getByLabelText('מחיר'), { target: { value: '300000' } })
    fireEvent.change(screen.getByLabelText('מספר חדרים'), { target: { value: '5' } })
    
    const submitButton = screen.getByText('שמור נכס')
    fireEvent.click(submitButton)
    
    // Wait for dialog to appear
    await waitFor(() => {
      expect(screen.getByText('הגעת למגבלת הנכסים!')).toBeInTheDocument()
    })
    
    // Click upgrade button
    const upgradeButton = screen.getByText('שדרג חבילה')
    fireEvent.click(upgradeButton)
    
    // Should navigate to billing page
    expect(mockPush).toHaveBeenCalledWith('/billing')
  })

  it('closes plan limit dialog when close button is clicked', async () => {
    // Mock asset creation failure due to plan limit
    mockAuthAPI.createAsset.mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({
        error: 'asset_limit_exceeded',
        message: 'הגעת למגבלת הנכסים בחבילה הנוכחית (Basic Plan).',
        current_plan: 'Basic Plan',
        asset_limit: 25,
        assets_used: 25,
        remaining: 0
      })
    })

    render(<AssetsPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    // Open asset creation form and trigger limit error
    const createButton = screen.getByText('הוסף נכס חדש')
    fireEvent.click(createButton)
    
    fireEvent.change(screen.getByLabelText('כתובת'), { target: { value: 'New Test Address' } })
    fireEvent.change(screen.getByLabelText('עיר'), { target: { value: 'Test City' } })
    fireEvent.change(screen.getByLabelText('מחיר'), { target: { value: '300000' } })
    fireEvent.change(screen.getByLabelText('מספר חדרים'), { target: { value: '5' } })
    
    const submitButton = screen.getByText('שמור נכס')
    fireEvent.click(submitButton)
    
    // Wait for dialog to appear
    await waitFor(() => {
      expect(screen.getByText('הגעת למגבלת הנכסים!')).toBeInTheDocument()
    })
    
    // Click close button
    const closeButton = screen.getByText('סגור')
    fireEvent.click(closeButton)
    
    // Dialog should be closed
    await waitFor(() => {
      expect(screen.queryByText('הגעת למגבלת הנכסים!')).not.toBeInTheDocument()
    })
  })

  it('handles different plan types correctly', async () => {
    const freePlanInfo = {
      ...mockPlanInfo,
      plan_name: 'free',
      display_name: 'Free Plan',
      limits: {
        assets: { limit: 5, used: 4, remaining: 1 },
        reports: { limit: 10, used: 2, remaining: 8 },
        alerts: { limit: 5, used: 1, remaining: 4 }
      }
    }

    mockAuthAPI.getPlanInfo.mockResolvedValue(freePlanInfo)

    render(<AssetsPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Free Plan')).toBeInTheDocument()
    })
    
    expect(screen.getByText('נכסים: 4/5')).toBeInTheDocument()
  })

  it('handles unlimited plans correctly', async () => {
    const proPlanInfo = {
      ...mockPlanInfo,
      plan_name: 'pro',
      display_name: 'Pro Plan',
      limits: {
        assets: { limit: -1, used: 100, remaining: -1 },
        reports: { limit: -1, used: 50, remaining: -1 },
        alerts: { limit: -1, used: 25, remaining: -1 }
      }
    }

    mockAuthAPI.getPlanInfo.mockResolvedValue(proPlanInfo)

    render(<AssetsPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Pro Plan')).toBeInTheDocument()
    })
    
    expect(screen.getByText('נכסים: 100/∞')).toBeInTheDocument()
  })

  it('updates plan info after successful asset creation', async () => {
    const updatedPlanInfo = {
      ...mockPlanInfo,
      limits: {
        assets: { limit: 25, used: 25, remaining: 0 },
        reports: { limit: 50, used: 5, remaining: 45 },
        alerts: { limit: 25, used: 3, remaining: 22 }
      }
    }

    // Mock successful asset creation
    mockAuthAPI.createAsset.mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({
        id: 3,
        address: 'New Test Address',
        city: 'Test City',
        price: 300000,
        rooms: 5,
        created_at: '2023-01-03T00:00:00Z'
      })
    })

    // Mock updated plan info after creation
    mockAuthAPI.getPlanInfo
      .mockResolvedValueOnce(mockPlanInfo) // Initial load
      .mockResolvedValueOnce(updatedPlanInfo) // After asset creation

    render(<AssetsPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    // Create asset
    const createButton = screen.getByText('הוסף נכס חדש')
    fireEvent.click(createButton)
    
    fireEvent.change(screen.getByLabelText('כתובת'), { target: { value: 'New Test Address' } })
    fireEvent.change(screen.getByLabelText('עיר'), { target: { value: 'Test City' } })
    fireEvent.change(screen.getByLabelText('מחיר'), { target: { value: '300000' } })
    fireEvent.change(screen.getByLabelText('מספר חדרים'), { target: { value: '5' } })
    
    const submitButton = screen.getByText('שמור נכס')
    fireEvent.click(submitButton)
    
    // Plan info should be updated
    await waitFor(() => {
      expect(screen.getByText('נכסים: 25/25')).toBeInTheDocument()
    })
  })

  it('handles API errors gracefully', async () => {
    mockAuthAPI.getPlanInfo.mockRejectedValue(new Error('API Error'))

    render(<AssetsPage />)
    
    // Should not crash and should show error state
    await waitFor(() => {
      expect(screen.queryByText('Basic Plan')).not.toBeInTheDocument()
    })
  })
})
