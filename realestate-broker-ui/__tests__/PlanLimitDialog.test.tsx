/**
 * @jest-environment jsdom
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import PlanLimitDialog from '@/components/PlanLimitDialog'
import { useRouter } from 'next/navigation'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

const mockPush = jest.fn()
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>

describe('PlanLimitDialog Component', () => {
  const mockError = {
    error: 'asset_limit_exceeded',
    message: 'הגעת למגבלת הנכסים בחבילה הנוכחית (Free Plan).',
    current_plan: 'Free Plan',
    asset_limit: 5,
    assets_used: 5,
    remaining: 0
  }

  const mockBasicError = {
    error: 'asset_limit_exceeded',
    message: 'הגעת למגבלת הנכסים בחבילה הנוכחית (Basic Plan).',
    current_plan: 'Basic Plan',
    asset_limit: 25,
    assets_used: 25,
    remaining: 0
  }

  beforeEach(() => {
    jest.clearAllMocks()
    mockUseRouter.mockReturnValue({
      push: mockPush,
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
    })
  })

  it('renders nothing when error is null', () => {
    const { container } = render(
      <PlanLimitDialog
        open={true}
        onOpenChange={jest.fn()}
        error={null}
      />
    )
    
    expect(container.firstChild).toBeNull()
  })

  it('renders dialog when error is provided', () => {
    render(
      <PlanLimitDialog
        open={true}
        onOpenChange={jest.fn()}
        error={mockError}
      />
    )
    
    expect(screen.getByText('הגעת למגבלת הנכסים!')).toBeInTheDocument()
    expect(screen.getByText(mockError.message)).toBeInTheDocument()
  })

  it('displays correct plan information', () => {
    render(
      <PlanLimitDialog
        open={true}
        onOpenChange={jest.fn()}
        error={mockError}
      />
    )
    
    expect(screen.getByText('Free Plan')).toBeInTheDocument()
    expect(screen.getByText('5 נכסים')).toBeInTheDocument()
    expect(screen.getByText('5 נכסים בשימוש')).toBeInTheDocument()
    expect(screen.getByText('0 נכסים נותרו')).toBeInTheDocument()
  })

  it('displays correct plan information for basic plan', () => {
    render(
      <PlanLimitDialog
        open={true}
        onOpenChange={jest.fn()}
        error={mockBasicError}
      />
    )
    
    expect(screen.getByText('Basic Plan')).toBeInTheDocument()
    expect(screen.getByText('25 נכסים')).toBeInTheDocument()
    expect(screen.getByText('25 נכסים בשימוש')).toBeInTheDocument()
    expect(screen.getByText('0 נכסים נותרו')).toBeInTheDocument()
  })

  it('shows correct plan icon for free plan', () => {
    render(
      <PlanLimitDialog
        open={true}
        onOpenChange={jest.fn()}
        error={mockError}
      />
    )
    
    // Should show Star icon for free plan
    const starIcon = screen.getByTestId('plan-icon')
    expect(starIcon).toBeInTheDocument()
  })

  it('shows correct plan icon for basic plan', () => {
    render(
      <PlanLimitDialog
        open={true}
        onOpenChange={jest.fn()}
        error={mockBasicError}
      />
    )
    
    // Should show Zap icon for basic plan
    const zapIcon = screen.getByTestId('plan-icon')
    expect(zapIcon).toBeInTheDocument()
  })

  it('calls onOpenChange when close button is clicked', () => {
    const mockOnOpenChange = jest.fn()
    
    render(
      <PlanLimitDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        error={mockError}
      />
    )
    
    const closeButton = screen.getByText('סגור')
    fireEvent.click(closeButton)
    
    expect(mockOnOpenChange).toHaveBeenCalledWith(false)
  })

  it('calls onOpenChange and navigates to billing when upgrade button is clicked', () => {
    const mockOnOpenChange = jest.fn()
    
    render(
      <PlanLimitDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        error={mockError}
      />
    )
    
    const upgradeButton = screen.getByText('שדרג חבילה')
    fireEvent.click(upgradeButton)
    
    expect(mockOnOpenChange).toHaveBeenCalledWith(false)
    expect(mockPush).toHaveBeenCalledWith('/billing')
  })

  it('shows upgrade suggestions for free plan', () => {
    render(
      <PlanLimitDialog
        open={true}
        onOpenChange={jest.fn()}
        error={mockError}
      />
    )
    
    expect(screen.getByText('שדרג ל-Basic Plan')).toBeInTheDocument()
    expect(screen.getByText('עד 25 נכסים')).toBeInTheDocument()
    expect(screen.getByText('149 ₪ לחודש')).toBeInTheDocument()
  })

  it('shows upgrade suggestions for basic plan', () => {
    render(
      <PlanLimitDialog
        open={true}
        onOpenChange={jest.fn()}
        error={mockBasicError}
      />
    )
    
    expect(screen.getByText('שדרג ל-Pro Plan')).toBeInTheDocument()
    expect(screen.getByText('נכסים ללא הגבלה')).toBeInTheDocument()
    expect(screen.getByText('299 ₪ לחודש')).toBeInTheDocument()
  })

  it('handles missing error properties gracefully', () => {
    const incompleteError = {
      error: 'asset_limit_exceeded',
      message: 'Test message',
      // Missing other properties
    }
    
    render(
      <PlanLimitDialog
        open={true}
        onOpenChange={jest.fn()}
        error={incompleteError}
      />
    )
    
    expect(screen.getByText('הגעת למגבלת הנכסים!')).toBeInTheDocument()
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })

  it('does not render when open is false', () => {
    const { container } = render(
      <PlanLimitDialog
        open={false}
        onOpenChange={jest.fn()}
        error={mockError}
      />
    )
    
    expect(container.firstChild).toBeNull()
  })

  it('displays correct styling for different plan types', () => {
    const { rerender } = render(
      <PlanLimitDialog
        open={true}
        onOpenChange={jest.fn()}
        error={mockError}
      />
    )
    
    // Free plan should have specific styling
    expect(screen.getByText('Free Plan')).toBeInTheDocument()
    
    // Rerender with basic plan
    rerender(
      <PlanLimitDialog
        open={true}
        onOpenChange={jest.fn()}
        error={mockBasicError}
      />
    )
    
    // Basic plan should have different styling
    expect(screen.getByText('Basic Plan')).toBeInTheDocument()
  })

  it('handles very large numbers correctly', () => {
    const largeNumberError = {
      ...mockError,
      asset_limit: 1000000,
      assets_used: 999999,
      remaining: 1
    }
    
    render(
      <PlanLimitDialog
        open={true}
        onOpenChange={jest.fn()}
        error={largeNumberError}
      />
    )
    
    expect(screen.getByText('1,000,000 נכסים')).toBeInTheDocument()
    expect(screen.getByText('999,999 נכסים בשימוש')).toBeInTheDocument()
    expect(screen.getByText('1 נכסים נותרו')).toBeInTheDocument()
  })

  it('handles zero values correctly', () => {
    const zeroError = {
      ...mockError,
      asset_limit: 0,
      assets_used: 0,
      remaining: 0
    }
    
    render(
      <PlanLimitDialog
        open={true}
        onOpenChange={jest.fn()}
        error={zeroError}
      />
    )
    
    expect(screen.getByText('0 נכסים')).toBeInTheDocument()
    expect(screen.getByText('0 נכסים בשימוש')).toBeInTheDocument()
    expect(screen.getByText('0 נכסים נותרו')).toBeInTheDocument()
  })

  it('shows correct error icon', () => {
    render(
      <PlanLimitDialog
        open={true}
        onOpenChange={jest.fn()}
        error={mockError}
      />
    )
    
    // Should show AlertCircle icon
    const alertIcon = screen.getByTestId('alert-icon')
    expect(alertIcon).toBeInTheDocument()
  })

  it('handles keyboard navigation', () => {
    const mockOnOpenChange = jest.fn()
    
    render(
      <PlanLimitDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        error={mockError}
      />
    )
    
    // Test Escape key
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(mockOnOpenChange).toHaveBeenCalledWith(false)
  })

  it('renders with correct accessibility attributes', () => {
    render(
      <PlanLimitDialog
        open={true}
        onOpenChange={jest.fn()}
        error={mockError}
      />
    )
    
    const dialog = screen.getByRole('alertdialog')
    expect(dialog).toBeInTheDocument()
    
    const title = screen.getByRole('heading', { level: 2 })
    expect(title).toBeInTheDocument()
    expect(title).toHaveTextContent('הגעת למגבלת הנכסים!')
  })
})
