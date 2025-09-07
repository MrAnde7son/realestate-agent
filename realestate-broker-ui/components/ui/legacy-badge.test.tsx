import React from 'react'
import { render, screen } from '@testing-library/react'
import { Badge } from './legacy-badge'
import { describe, it, expect, vi } from 'vitest'
import Link from 'next/link'

describe('Badge Component', () => {
  it('renders correctly with default props', () => {
    render(<Badge>Test Badge</Badge>)
    const badge = screen.getByText('Test Badge')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('inline-flex', 'items-center', 'justify-center')
  })

  it('applies variant classes correctly', () => {
    const { rerender } = render(<Badge variant="destructive">Destructive</Badge>)
    expect(screen.getByText('Destructive')).toHaveClass('bg-destructive')

    rerender(<Badge variant="secondary">Secondary</Badge>)
    expect(screen.getByText('Secondary')).toHaveClass('bg-secondary')

    rerender(<Badge variant="outline">Outline</Badge>)
    expect(screen.getByText('Outline')).toHaveClass('text-foreground')

    rerender(<Badge variant="good">Good</Badge>)
    expect(screen.getByText('Good')).toHaveClass('border-[#245a3a]', 'bg-[#11261a]', 'text-[#8ce7a8]')

    rerender(<Badge variant="warn">Warn</Badge>)
    expect(screen.getByText('Warn')).toHaveClass('border-[#5a4a24]', 'bg-[#261f11]', 'text-[#ffd07a]')

    rerender(<Badge variant="bad">Bad</Badge>)
    expect(screen.getByText('Bad')).toHaveClass('border-[#5a2424]', 'bg-[#261111]', 'text-[#ff9aa0]')
  })

  it('renders as child component when asChild is true', () => {
    render(
      <Badge asChild variant="outline">
        <Link href="/test">Badge Link</Link>
      </Badge>
    )
    
    const link = screen.getByRole('link')
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', '/test')
    expect(link).toHaveClass('inline-flex', 'items-center', 'justify-center')
    expect(link).toHaveClass('text-foreground') // outline variant class
  })

  it('applies custom className', () => {
    render(<Badge className="custom-badge-class">Custom</Badge>)
    expect(screen.getByText('Custom')).toHaveClass('custom-badge-class')
  })

  it('forwards ref correctly', () => {
    const ref = vi.fn()
    render(<Badge ref={ref}>Ref Badge</Badge>)
    expect(ref).toHaveBeenCalledWith(expect.any(HTMLSpanElement))
  })

  it('supports all HTML span attributes', () => {
    render(
      <Badge 
        title="Badge title"
        aria-label="Status badge"
        data-testid="status-badge"
      >
        Status
      </Badge>
    )
    
    const badge = screen.getByText('Status')
    expect(badge).toHaveAttribute('title', 'Badge title')
    expect(badge).toHaveAttribute('aria-label', 'Status badge')
    expect(badge).toHaveAttribute('data-testid', 'status-badge')
  })

  it('renders with icon content', () => {
    render(
      <Badge>
        <span data-testid="icon">🚀</span>
        With Icon
      </Badge>
    )
    
    expect(screen.getByTestId('icon')).toBeInTheDocument()
    expect(screen.getByText('With Icon')).toBeInTheDocument()
  })

  it('has correct default styling classes', () => {
    render(<Badge>Default Badge</Badge>)
    const badge = screen.getByText('Default Badge')
    
    expect(badge).toHaveClass(
      'rounded-md',
      'border',
      'px-2',
      'py-0.5',
      'text-xs',
      'font-medium',
      'w-fit',
      'whitespace-nowrap'
    )
  })
})
