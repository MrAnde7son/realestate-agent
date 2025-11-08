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

  it('applies the requested elevation variant', () => {
    render(
      <>
        <Card data-testid="default" />
        <Card data-testid="elevated" variant="elevated" />
        <Card data-testid="outlined" variant="outlined" />
      </>,
    )

    expect(screen.getByTestId('default')).toHaveClass('shadow-sm')
    expect(screen.getByTestId('elevated')).toHaveClass('shadow-lg')
    expect(screen.getByTestId('outlined')).toHaveClass('ring-1')
    expect(screen.getByTestId('outlined')).toHaveClass('ring-inset')
    expect(screen.getByTestId('outlined')).toHaveClass('shadow-none')
  })

  it('enables interactive affordances when requested', () => {
    render(<Card data-testid="interactive" interactive />)

    expect(screen.getByTestId('interactive')).toHaveClass('hover:shadow-md')
    expect(screen.getByTestId('interactive')).toHaveClass('focus-visible:ring-2')
  })
})
