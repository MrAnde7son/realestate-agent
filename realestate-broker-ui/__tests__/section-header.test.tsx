import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { SectionHeader } from '@/components/layout/section-header'

describe('SectionHeader', () => {
  it('renders title, count, description, saved filters, and actions', () => {
    render(
      <SectionHeader
        title='כותרת מדור'
        count={1234}
        countLabel='נכסים'
        description='תיאור המדור'
        savedFilters={<div>סינונים</div>}
        primaryActions={<button type='button'>פעולה</button>}
      />
    )

    expect(screen.getByRole('heading', { name: 'כותרת מדור' })).toBeInTheDocument()
    const summary = screen.getByText(/תיאור המדור/)
    expect(summary).toHaveTextContent('1,234', { normalizeWhitespace: true })
    expect(screen.getByText('סינונים')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'פעולה' })).toBeInTheDocument()
  })
})
