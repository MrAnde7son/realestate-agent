import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { InlineAlert } from './inline-alert'

describe('InlineAlert', () => {
  it('renders title and description', () => {
    render(<InlineAlert title="כותרת" description="תיאור" />)

    expect(screen.getByText('כותרת')).toBeInTheDocument()
    expect(screen.getByText('תיאור')).toBeInTheDocument()
  })

  it('falls back to children when description is not provided', () => {
    render(
      <InlineAlert title="עדכון">
        <span>תוכן מותאם אישית</span>
      </InlineAlert>
    )

    expect(screen.getByText('תוכן מותאם אישית')).toBeInTheDocument()
  })

  it('applies destructive semantics and styling', () => {
    render(<InlineAlert variant="destructive" title="שגיאה">פרטים</InlineAlert>)

    const alert = screen.getByRole('alert')
    expect(alert).toHaveClass('border-destructive/50')
    expect(alert).toHaveClass('bg-destructive/10')
  })
})
