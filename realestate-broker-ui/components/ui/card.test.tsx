import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
  CardTitle,
  CardDescription,
} from './Card'

describe('Card component', () => {
  it('renders full structure', () => {
    render(
      <Card data-testid="card">
        <CardHeader>
          <CardTitle>Title</CardTitle>
          <CardDescription>Description</CardDescription>
        </CardHeader>
        <CardContent>Body</CardContent>
        <CardFooter>Footer</CardFooter>
      </Card>
    )

    expect(screen.getByTestId('card')).toBeInTheDocument()
    expect(screen.getByText('Title')).toBeInTheDocument()
    expect(screen.getByText('Description')).toBeInTheDocument()
    expect(screen.getByText('Body')).toBeInTheDocument()
    expect(screen.getByText('Footer')).toBeInTheDocument()
  })

  it('applies visual variants', () => {
    const { rerender } = render(<Card data-testid="card" variant="outline" />)

    expect(screen.getByTestId('card')).toHaveClass('border', 'shadow-none')

    rerender(<Card data-testid="card" variant="ghost" />)
    expect(screen.getByTestId('card')).toHaveClass('bg-transparent')
  })

  it('supports contextual sizing for nested sections', () => {
    render(
      <Card size="sm">
        <CardHeader data-testid="header">Header</CardHeader>
        <CardContent data-testid="content">Content</CardContent>
        <CardFooter data-testid="footer">Footer</CardFooter>
      </Card>
    )

    expect(screen.getByTestId('header')).toHaveClass('px-4', 'py-3')
    expect(screen.getByTestId('content')).toHaveClass('px-4', 'pb-4', 'pt-0')
    expect(screen.getByTestId('footer')).toHaveClass('px-4', 'pb-4', 'pt-0')
  })
})
