/**
 * @jest-environment jsdom
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import PlanInfo from '@/components/PlanInfo'
import { authAPI } from '@/lib/auth'

// Mock the authAPI
jest.mock('@/lib/auth', () => ({
  authAPI: {
    getPlanInfo: jest.fn(),
  },
}))

const mockAuthAPI = authAPI as jest.Mocked<typeof authAPI>

describe('PlanInfo Component', () => {
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
      assets: { limit: 25, used: 10, remaining: 15 },
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

  const mockFreePlanInfo = {
    plan_name: 'free',
    display_name: 'Free Plan',
    description: 'Free plan for basic users',
    price: 0,
    currency: 'ILS',
    billing_period: 'monthly',
    is_active: true,
    is_expired: false,
    expires_at: null,
    limits: {
      assets: { limit: 5, used: 3, remaining: 2 },
      reports: { limit: 10, used: 1, remaining: 9 },
      alerts: { limit: 5, used: 0, remaining: 5 }
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
    price: 299.00,
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
    jest.clearAllMocks()
  })

  it('renders loading state initially', () => {
    mockAuthAPI.getPlanInfo.mockImplementation(() => new Promise(() => {})) // Never resolves
    
    render(<PlanInfo />)
    
    expect(screen.getByText('טוען מידע על החבילה...')).toBeInTheDocument()
  })

  it('renders plan information correctly for basic plan', async () => {
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockPlanInfo)
    
    render(<PlanInfo />)
    
    await waitFor(() => {
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Basic plan for advanced users')).toBeInTheDocument()
    expect(screen.getByText('149 ₪')).toBeInTheDocument()
    expect(screen.getByText('לחודש')).toBeInTheDocument()
    
    // Check limits
    expect(screen.getByText('נכסים: 10/25')).toBeInTheDocument()
    expect(screen.getByText('דוחות: 5/50')).toBeInTheDocument()
    expect(screen.getByText('התראות: 3/25')).toBeInTheDocument()
    
    // Check features
    expect(screen.getByText('ניתוח מתקדם')).toBeInTheDocument()
    expect(screen.getByText('ייצוא נתונים')).toBeInTheDocument()
  })

  it('renders plan information correctly for free plan', async () => {
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockFreePlanInfo)
    
    render(<PlanInfo />)
    
    await waitFor(() => {
      expect(screen.getByText('Free Plan')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Free plan for basic users')).toBeInTheDocument()
    expect(screen.getByText('0 ₪')).toBeInTheDocument()
    
    // Check limits
    expect(screen.getByText('נכסים: 3/5')).toBeInTheDocument()
    expect(screen.getByText('דוחות: 1/10')).toBeInTheDocument()
    expect(screen.getByText('התראות: 0/5')).toBeInTheDocument()
  })

  it('renders unlimited plan correctly for pro plan', async () => {
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockProPlanInfo)
    
    render(<PlanInfo />)
    
    await waitFor(() => {
      expect(screen.getByText('Pro Plan')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Professional plan for power users')).toBeInTheDocument()
    expect(screen.getByText('299 ₪')).toBeInTheDocument()
    
    // Check unlimited limits
    expect(screen.getByText('נכסים: 100/∞')).toBeInTheDocument()
    expect(screen.getByText('דוחות: 50/∞')).toBeInTheDocument()
    expect(screen.getByText('התראות: 25/∞')).toBeInTheDocument()
    
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
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    // Check that progress bar is rendered
    const progressBar = screen.getByRole('progressbar', { hidden: true })
    expect(progressBar).toBeInTheDocument()
    
    // Check progress bar width (10/25 = 40%)
    const progressFill = progressBar.querySelector('div')
    expect(progressFill).toHaveStyle('width: 40%')
  })

  it('does not render progress bar for unlimited plans', async () => {
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockProPlanInfo)
    
    render(<PlanInfo />)
    
    await waitFor(() => {
      expect(screen.getByText('Pro Plan')).toBeInTheDocument()
    })
    
    // Should not have progress bar for unlimited plans
    expect(screen.queryByRole('progressbar', { hidden: true })).not.toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    mockAuthAPI.getPlanInfo.mockRejectedValue(new Error('API Error'))
    
    render(<PlanInfo />)
    
    await waitFor(() => {
      expect(screen.getByText('שגיאה בטעינת מידע על החבילה')).toBeInTheDocument()
    })
  })

  it('shows upgrade button for non-pro plans', async () => {
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockPlanInfo)
    
    render(<PlanInfo />)
    
    await waitFor(() => {
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    expect(screen.getByText('שדרג חבילה')).toBeInTheDocument()
  })

  it('does not show upgrade button for pro plan', async () => {
    mockProPlanInfo.plan_name = 'pro'
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockProPlanInfo)
    
    render(<PlanInfo />)
    
    await waitFor(() => {
      expect(screen.getByText('Pro Plan')).toBeInTheDocument()
    })
    
    expect(screen.queryByText('שדרג חבילה')).not.toBeInTheDocument()
  })

  it('displays correct plan icon', async () => {
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockPlanInfo)
    
    render(<PlanInfo />)
    
    await waitFor(() => {
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    // Check that the correct icon is rendered (Zap for basic plan)
    const icon = screen.getByTestId('plan-icon')
    expect(icon).toBeInTheDocument()
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
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    // Should show expired status
    expect(screen.getByText('פג תוקף')).toBeInTheDocument()
  })

  it('formats currency correctly', async () => {
    const planWithUSD = {
      ...mockPlanInfo,
      currency: 'USD',
      price: 99.99
    }
    
    mockAuthAPI.getPlanInfo.mockResolvedValue(planWithUSD)
    
    render(<PlanInfo />)
    
    await waitFor(() => {
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    expect(screen.getByText('99.99 $')).toBeInTheDocument()
  })

  it('handles different billing periods', async () => {
    const yearlyPlan = {
      ...mockPlanInfo,
      billing_period: 'yearly',
      price: 1200
    }
    
    mockAuthAPI.getPlanInfo.mockResolvedValue(yearlyPlan)
    
    render(<PlanInfo />)
    
    await waitFor(() => {
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    expect(screen.getByText('1200 ₪')).toBeInTheDocument()
    expect(screen.getByText('לשנה')).toBeInTheDocument()
  })

  it('updates when plan info changes', async () => {
    const { rerender } = render(<PlanInfo />)
    
    // Initial load
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockFreePlanInfo)
    
    await waitFor(() => {
      expect(screen.getByText('Free Plan')).toBeInTheDocument()
    })
    
    // Change plan
    mockAuthAPI.getPlanInfo.mockResolvedValue(mockPlanInfo)
    rerender(<PlanInfo />)
    
    await waitFor(() => {
      expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    })
    
    expect(screen.queryByText('Free Plan')).not.toBeInTheDocument()
  })
})
