import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Badge } from './Badge'

describe('Badge component', () => {
  it('renders with default props', () => {
    render(<Badge>Label</Badge>)
    expect(screen.getByText('Label')).toBeInTheDocument()
  })

  it('applies variant styles', () => {
    const { rerender } = render(<Badge variant="success">A</Badge>)
    expect(screen.getByText('A')).toHaveClass('bg-success')
    rerender(<Badge variant="warning">B</Badge>)
    expect(screen.getByText('B')).toHaveClass('bg-warning')
  })
})
