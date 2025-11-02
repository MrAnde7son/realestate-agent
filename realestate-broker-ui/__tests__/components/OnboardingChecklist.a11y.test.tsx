import { fireEvent, render, screen } from '@testing-library/react'

import OnboardingChecklist from '@/components/OnboardingChecklist'

const baseState = {
  connectPayment: false,
  addAsset: false,
  generateReport: false,
  createAlert: false,
} as const

describe('OnboardingChecklist accessibility affordances', () => {
  it('surfaces an accessible label for the collapse toggle', () => {
    render(<OnboardingChecklist state={baseState} />)

    const toggle = screen.getByRole('button', { name: 'סגור רשימת משימות' })
    expect(toggle).toBeInTheDocument()

    fireEvent.click(toggle)

    expect(
      screen.getByRole('button', { name: 'פתח רשימת משימות' })
    ).toBeInTheDocument()
  })
})
