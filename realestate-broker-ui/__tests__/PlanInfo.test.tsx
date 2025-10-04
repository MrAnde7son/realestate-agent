/**
 * @vitest-environment jsdom
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { vi } from 'vitest'
import PlanInfo from '@/components/PlanInfo'
import { authAPI } from '@/lib/auth'

// Mock the authAPI
vi.mock('@/lib/auth', () => ({
  authAPI: {
    getPlanInfo: vi.fn(),
  },
}))

const mockAuthAPI = authAPI as any

describe('PlanInfo Component', () => {
  const mockPlanInfo = {
    plan_name: 'basic',
    display_name: 'Basic Plan',
    description: 'Basic plan for advanced users',
    price: 399.00,
    currency: 'ILS',
    billing_period: 'monthly',
    is_active: true,
    is_expired: false,
    expires_at: null,
    limits: {
      assets: { limit: 10, used: 4, remaining: 6 },
      reports: { limit: 25, used: 5, remaining: 20 },
      alerts: { limit: 25, used: 3, remaining: 22 }
    },
    features: {
      advanced_analytics: false,
      data_export: true,
      api_access: false,
      priority_support: false,
      custom_reports: true
    }
  }

  const mockFreePlanInfo = {
    plan_name: 'free',
    display_name: 'Free Plan',
    description: 'Free plan for basic users',
    price: 79,
    currency: 'ILS',
    billing_period: 'monthly',
    is_active: true,
    is_expired: false,
    expires_at: null,
    limits: {
      assets: { limit: 1, used: 0, remaining: 1 },
      reports: { limit: 1, used: 0, remaining: 1 },
      alerts: { limit: 0, used: 0, remaining: 0 }
    },
    features: {
      advanced_analytics: false,
      data_export: false,
      api_access: false,
      priority_support: false,
      custom_reports: false
    }
  }

  const mockProPlanInfo = {
    plan_name: 'pro',
    display_name: 'Pro Plan',
    description: 'Professional plan for power users',
    price: 0,
    currency: 'ILS',
    billing_period: 'monthly',
    is_active: true,
    is_expired: false,
    expires_at: null,
    limits: {
      assets: { limit: -1, used: 100, remaining: -1 },
      reports: { limit: -1, used: 50, remaining: -1 },
      alerts: { limit: -1, used: 25, remaining: -1 }
    },
    features: {
      advanced_analytics: true,
      data_export: true,
      api_access: true,
      priority_support: true,
      custom_reports: true
    }
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('falls back to API-provided names when translation is unavailable', async () => {
    const customPlan = {
      ...mockPlanInfo,
      plan_name: 'enterprise',
      display_name: 'Enterprise Plan',
      description: 'Enterprise description',
    }

    mockAuthAPI.getPlanInfo.mockResolvedValue(customPlan)

    render(<PlanInfo />)

    await waitFor(() => {
      expect(screen.getByText('Enterprise Plan')).toBeInTheDocument()
    })

    expect(screen.getByText('Enterprise description')).toBeInTheDocument()
  })

  it('renders loading state initially', () => {
    mockAuthAPI.getPlanInfo.mockImplementation(() => new Promise(() => {})) // Never resolves
    
    render(<PlanInfo />)
    
    // Check for loading skeleton instead of text
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('renders plan information correctly for basic plan', async () => {
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockPlanInfo)

    render(<PlanInfo />)

    await waitFor(() => {
      expect(screen.getByText('בסיסי')).toBeInTheDocument()
    })

    expect(screen.getByText('מנוי חודשי עם עד 10 נכסים, עד 25 דוחות וייצוא דוחות ממותגים')).toBeInTheDocument()
    // Price information is no longer displayed in the component

    // Check limits
    expect(screen.getByText('4 / 10')).toBeInTheDocument()

    // Check features
    expect(screen.getByText('ניתוח מתקדם')).toBeInTheDocument()
    expect(screen.getByText('ייצוא נתונים')).toBeInTheDocument()
    expect(screen.getByText('דוחות מותאמים')).toBeInTheDocument()
  })

  it('renders plan information correctly for free plan', async () => {
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockFreePlanInfo)

    render(<PlanInfo />)

    await waitFor(() => {
      expect(screen.getByText('פרטי')).toBeInTheDocument()
    })

    expect(screen.getByText('דוח חד פעמי הכולל נתוני נכס, הערכת שווי ועלויות עסקה ומשכנתא')).toBeInTheDocument()

    // Check limits
    expect(screen.getByText('0 / 1')).toBeInTheDocument()
  })

  it('renders unlimited plan correctly for pro plan', async () => {
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockProPlanInfo)

    render(<PlanInfo />)

    await waitFor(() => {
      expect(screen.getByText('עיסקי')).toBeInTheDocument()
    })

    expect(screen.getByText('לצוותים מקצועיים עם נכסים והתראות ללא הגבלה ויכולות AI מתקדמות')).toBeInTheDocument()

    // Check unlimited limits
    expect(screen.getByText('100 / ∞')).toBeInTheDocument()
    
    // Check all features
    expect(screen.getByText('ניתוח מתקדם')).toBeInTheDocument()
    expect(screen.getByText('ייצוא נתונים')).toBeInTheDocument()
    expect(screen.getByText('גישת API')).toBeInTheDocument()
    expect(screen.getByText('תמיכה מועדפת')).toBeInTheDocument()
    expect(screen.getByText('דוחות מותאמים')).toBeInTheDocument()
  })

  it('renders progress bar correctly', async () => {
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockPlanInfo)

    render(<PlanInfo />)

    await waitFor(() => {
      expect(screen.getByText('בסיסי')).toBeInTheDocument()
    })

    // Check that progress bar is rendered (custom div-based progress bar)
    const progressBar = document.querySelector('.w-full.bg-gray-200.rounded-full.h-2')
    expect(progressBar).toBeInTheDocument()
    
    // Check progress bar fill element
    const progressFill = progressBar?.querySelector('.bg-primary.h-2.rounded-full')
    expect(progressFill).toBeInTheDocument()
    expect(progressFill).toHaveStyle('width: 40%')
  })

  it('does not render progress bar for unlimited plans', async () => {
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockProPlanInfo)
    
    render(<PlanInfo />)
    
    await waitFor(() => {
      expect(screen.getByText('עיסקי')).toBeInTheDocument()
    })
    
    // Should not have progress bar for unlimited plans
    expect(screen.queryByRole('progressbar', { hidden: true })).not.toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    mockAuthAPI.getPlanInfo.mockRejectedValue(new Error('API Error'))
    
    render(<PlanInfo />)
    
    await waitFor(() => {
      expect(screen.getByText('אירעה שגיאה בעת טעינת פרטי החבילה')).toBeInTheDocument()
    })
  })



  it('handles expired plans correctly', async () => {
    const expiredPlanInfo = {
      ...mockPlanInfo,
      is_expired: true,
      expires_at: '2023-01-01T00:00:00Z'
    }
    
    mockAuthAPI.getPlanInfo.mockResolvedValue(expiredPlanInfo)
    
    render(<PlanInfo />)
    
    await waitFor(() => {
      expect(screen.getByText('בסיסי')).toBeInTheDocument()
    })

    // Should show expired status
    expect(screen.getByText('פג תוקף')).toBeInTheDocument()
  })
})
