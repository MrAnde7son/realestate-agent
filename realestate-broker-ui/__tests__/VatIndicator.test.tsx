import React from 'react'
import { render, screen } from '@testing-library/react'

import { VatIndicator } from '@/components/vat-indicator'

describe('VatIndicator', () => {
  it('shows the current VAT rate in a compact badge', () => {
    render(<VatIndicator vatRate={0.18} vatUpdated="2024-05-15T12:00:00Z" />)

    expect(screen.getByText('מע״מ נוכחי')).toBeInTheDocument()
    expect(screen.getByText('18.0%')).toBeInTheDocument()

    const lastUpdate = screen.getByText(/עדכון אחרון/)
    expect(lastUpdate).toHaveTextContent('עדכון אחרון:')
    expect(lastUpdate.textContent).toMatch(/2024/)
  })

  it('omits the last update badge when no date is provided', () => {
    render(<VatIndicator vatRate={0.17} />)

    expect(screen.getByText('מע״מ נוכחי')).toBeInTheDocument()
    expect(screen.getByText('17.0%')).toBeInTheDocument()
    expect(screen.queryByText(/עדכון אחרון/)).toBeNull()
  })
})
