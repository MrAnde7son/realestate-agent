import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Typography } from './typography'

describe('Typography', () => {
  it('renders a paragraph by default', () => {
    render(<Typography>ברירת מחדל</Typography>)

    const paragraph = screen.getByText('ברירת מחדל')
    expect(paragraph.tagName.toLowerCase()).toBe('p')
    expect(paragraph).toHaveClass('text-base')
  })

  it('renders semantic headings based on variant', () => {
    render(
      <>
        <Typography variant='h1'>כותרת ראשית</Typography>
        <Typography variant='h2'>כותרת משנית</Typography>
        <Typography variant='h3'>כותרת משנה</Typography>
      </>
    )

    expect(screen.getByText('כותרת ראשית').tagName.toLowerCase()).toBe('h1')
    expect(screen.getByText('כותרת משנית').tagName.toLowerCase()).toBe('h2')
    expect(screen.getByText('כותרת משנה').tagName.toLowerCase()).toBe('h3')
  })

  it('allows overriding the rendered element', () => {
    render(
      <Typography variant='h2' as='h3' className='custom-class'>
        כותרת מותאמת
      </Typography>
    )

    const heading = screen.getByText('כותרת מותאמת')
    expect(heading.tagName.toLowerCase()).toBe('h3')
    expect(heading).toHaveClass('custom-class')
  })
})
