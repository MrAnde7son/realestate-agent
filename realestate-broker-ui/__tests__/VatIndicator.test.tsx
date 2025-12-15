import React from 'react'
import { render, screen } from '@testing-library/react'

import { VatIndicator } from '@/components/vat-indicator'

describe('VatIndicator', () => {
  it('shows the current VAT rate in a compact badge', () => {
    const { container } = render(<VatIndicator vatRate={0.18} vatUpdated="2024-05-15T12:00:00Z" />)

    // Check that the VAT rate text is present
    expect(container.textContent).toContain('מע״מ נוכחי')
    expect(container.textContent).toContain('18.0%')

    // Check that the last update text is present
    expect(container.textContent).toContain('עדכון אחרון')
    expect(container.textContent).toContain('2024')
  })

  it('omits the last update badge when no date is provided', () => {
    const { container } = render(<VatIndicator vatRate={0.17} />)

    // Check that the VAT rate text is present
    expect(container.textContent).toContain('מע״מ נוכחי')
    expect(container.textContent).toContain('17.0%')
    
    // Check that the last update text is NOT present
    expect(container.textContent).not.toContain('עדכון אחרון')
  })
})
