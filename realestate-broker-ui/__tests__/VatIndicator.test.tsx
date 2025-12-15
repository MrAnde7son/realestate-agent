import React from 'react'
import { render, screen } from '@testing-library/react'

import { VatIndicator } from '@/components/vat-indicator'

describe('VatIndicator', () => {
  it('shows the current VAT rate in a compact badge', () => {
    render(<VatIndicator vatRate={0.18} vatUpdated="2024-05-15T12:00:00Z" />)

    // Text is split across elements, so use a function matcher
    expect(screen.getByText((content, element) => {
      return element?.textContent?.includes('מע״מ נוכחי') ?? false
    })).toBeInTheDocument()
    
    // Percentage might be split, so check for the number and % separately or together
    expect(screen.getByText((content, element) => {
      return element?.textContent?.includes('18.0') && element?.textContent?.includes('%')
    })).toBeInTheDocument()

    const lastUpdate = screen.getByText(/עדכון אחרון/)
    expect(lastUpdate).toHaveTextContent('עדכון אחרון:')
    expect(lastUpdate.textContent).toMatch(/2024/)
  })

  it('omits the last update badge when no date is provided', () => {
    render(<VatIndicator vatRate={0.17} />)

    // Text is split across elements, so use a function matcher
    expect(screen.getByText((content, element) => {
      return element?.textContent?.includes('מע״מ נוכחי') ?? false
    })).toBeInTheDocument()
    
    // Percentage might be split, so check for the number and % separately or together
    expect(screen.getByText((content, element) => {
      return element?.textContent?.includes('17.0') && element?.textContent?.includes('%')
    })).toBeInTheDocument()
    
    expect(screen.queryByText(/עדכון אחרון/)).toBeNull()
  })
})
