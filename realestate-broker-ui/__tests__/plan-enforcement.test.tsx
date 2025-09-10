/**
 * @vitest-environment jsdom
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { vi } from 'vitest'
import BillingPage from '@/app/billing/page'
import { authAPI } from '@/lib/auth'
import { AuthProvider } from '@/lib/auth-context'

// Mock the authAPI
vi.mock('@/lib/auth', () => ({
  authAPI: {
    getAssets: vi.fn(),
    createAsset: vi.fn(),
    getPlanInfo: vi.fn(),
  },
  useAuth: () => ({
    isAuthenticated: true,
    user: { id: 1, username: 'testuser' }
  })
}))

// Mock next/navigation
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => '/billing',
}))

const mockAuthAPI = authAPI as any

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
    vi.clearAllMocks()
    mockAuthAPI.getAssets.mockResolvedValue(mockAssets)
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockPlanInfo)
  })

  it('displays plan information for authenticated users', async () => {
    render(
      <AuthProvider>
        <BillingPage />
      </AuthProvider>
    )
    
    await waitFor(() => {
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Basic plan for advanced users')).toBeInTheDocument()
    expect(screen.getByText('149 ₪')).toBeInTheDocument()
    expect(screen.getByText('נכסים: 24/25')).toBeInTheDocument()
  })

  it('shows current plan button for user plan', async () => {
    render(
      <AuthProvider>
        <BillingPage />
      </AuthProvider>
    )
    
    await waitFor(() => {
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    // Should show "החבילה הנוכחית" for the user's current plan
    expect(screen.getByText('החבילה הנוכחית')).toBeInTheDocument()
  })

  it('shows plan features correctly', async () => {
    render(
      <AuthProvider>
        <BillingPage />
      </AuthProvider>
    )
    
    await waitFor(() => {
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    // Should show plan features
    expect(screen.getByText('ניתוח מתקדם')).toBeInTheDocument()
    expect(screen.getByText('ייצוא נתונים')).toBeInTheDocument()
  })

  it('shows available plan options', async () => {
    render(
      <AuthProvider>
        <BillingPage />
      </AuthProvider>
    )
    
    // Should show all available plans
    expect(screen.getByText('חבילה חינמית')).toBeInTheDocument()
    expect(screen.getByText('חבילה בסיסית')).toBeInTheDocument()
    expect(screen.getByText('חבילה מקצועית')).toBeInTheDocument()
  })

  it('shows different button text for different plans', async () => {
    // Test free plan
    const freePlanInfo = {
      ...mockPlanInfo,
      plan_name: 'free',
      display_name: 'Free Plan'
    }

    mockAuthAPI.getPlanInfo.mockResolvedValue(freePlanInfo)

    render(
      <AuthProvider>
        <BillingPage />
      </AuthProvider>
    )
    
    await waitFor(() => {
      expect(screen.getByText('Free Plan')).toBeInTheDocument()
    })
    
    // Should show "החבילה הנוכחית" for free plan
    expect(screen.getByText('החבילה הנוכחית')).toBeInTheDocument()
  })

  it('shows correct button text for pro plan', async () => {
    const proPlanInfo = {
      ...mockPlanInfo,
      plan_name: 'pro',
      display_name: 'Pro Plan'
    }

    mockAuthAPI.getPlanInfo.mockResolvedValue(proPlanInfo)

    render(
      <AuthProvider>
        <BillingPage />
      </AuthProvider>
    )
    
    await waitFor(() => {
      expect(screen.getByText('Pro Plan')).toBeInTheDocument()
    })
    
    // Should show "החבילה הנוכחית" for pro plan
    expect(screen.getByText('החבילה הנוכחית')).toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    mockAuthAPI.getPlanInfo.mockRejectedValue(new Error('API Error'))

    render(
      <AuthProvider>
        <BillingPage />
      </AuthProvider>
    )
    
    // Should not crash and should show error state
    await waitFor(() => {
      expect(screen.queryByText('Basic Plan')).not.toBeInTheDocument()
    })
  })
})
