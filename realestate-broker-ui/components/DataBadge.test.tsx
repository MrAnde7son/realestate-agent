// @vitest-environment jsdom
import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { describe, it, expect } from 'vitest'
import DataBadge from './DataBadge'

describe('DataBadge', () => {
  it('renders tooltip with source and date', async () => {
    render(
      <DataBadge source="מנהל התכנון" fetchedAt="2025-09-01" url="http://example.com" defaultOpen />
    )
    const tooltip = screen.getByTestId('data-badge-tooltip')
    expect(tooltip).toHaveTextContent(
      'מקור: מנהל התכנון • עודכן: 2025-09-01'
    )
    expect(tooltip.querySelector('a')).toHaveAttribute('href', 'http://example.com')
  })

  it('renders nothing when metadata missing', () => {
    const { container } = render(<DataBadge />)
    expect(container.firstChild).toBeNull()
  })
})
