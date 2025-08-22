import React from 'react'
import { render, screen } from '@testing-library/react'
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent, 
  CardFooter, 
  CardAction 
} from './card'
import { describe, it, expect } from 'vitest'

describe('Card Components', () => {
  describe('Card', () => {
    it('renders correctly with default props', () => {
      render(<Card data-testid="card">Card Content</Card>)
      const card = screen.getByTestId('card')
      expect(card).toBeInTheDocument()
      expect(card).toHaveClass('bg-card', 'text-card-foreground', 'flex', 'flex-col', 'rounded-xl', 'border', 'shadow-sm')
      expect(card).toHaveAttribute('data-slot', 'card')
    })

    it('applies custom className', () => {
      render(<Card className="custom-card" data-testid="card">Content</Card>)
      expect(screen.getByTestId('card')).toHaveClass('custom-card')
    })

    it('supports all div attributes', () => {
      render(
        <Card 
          data-testid="card"
          id="test-card"
          role="region"
          aria-label="Card region"
        >
          Content
        </Card>
      )
      
      const card = screen.getByTestId('card')
      expect(card).toHaveAttribute('id', 'test-card')
      expect(card).toHaveAttribute('role', 'region')
      expect(card).toHaveAttribute('aria-label', 'Card region')
    })
  })

  describe('CardHeader', () => {
    it('renders correctly', () => {
      render(<CardHeader data-testid="header">Header Content</CardHeader>)
      const header = screen.getByTestId('header')
      expect(header).toBeInTheDocument()
      expect(header).toHaveClass('grid', 'auto-rows-min', 'items-start')
      expect(header).toHaveAttribute('data-slot', 'card-header')
    })

    it('applies custom className', () => {
      render(<CardHeader className="custom-header" data-testid="header">Content</CardHeader>)
      expect(screen.getByTestId('header')).toHaveClass('custom-header')
    })
  })

  describe('CardTitle', () => {
    it('renders correctly', () => {
      render(<CardTitle data-testid="title">Card Title</CardTitle>)
      const title = screen.getByTestId('title')
      expect(title).toBeInTheDocument()
      expect(title).toHaveClass('leading-none', 'font-semibold')
      expect(title).toHaveAttribute('data-slot', 'card-title')
    })

    it('applies custom className', () => {
      render(<CardTitle className="custom-title" data-testid="title">Title</CardTitle>)
      expect(screen.getByTestId('title')).toHaveClass('custom-title')
    })
  })

  describe('CardDescription', () => {
    it('renders correctly', () => {
      render(<CardDescription data-testid="description">Card Description</CardDescription>)
      const description = screen.getByTestId('description')
      expect(description).toBeInTheDocument()
      expect(description).toHaveClass('text-muted-foreground', 'text-sm')
      expect(description).toHaveAttribute('data-slot', 'card-description')
    })

    it('applies custom className', () => {
      render(<CardDescription className="custom-desc" data-testid="description">Desc</CardDescription>)
      expect(screen.getByTestId('description')).toHaveClass('custom-desc')
    })
  })

  describe('CardContent', () => {
    it('renders correctly', () => {
      render(<CardContent data-testid="content">Card Content</CardContent>)
      const content = screen.getByTestId('content')
      expect(content).toBeInTheDocument()
      expect(content).toHaveClass('px-6')
      expect(content).toHaveAttribute('data-slot', 'card-content')
    })

    it('applies custom className', () => {
      render(<CardContent className="custom-content" data-testid="content">Content</CardContent>)
      expect(screen.getByTestId('content')).toHaveClass('custom-content')
    })
  })

  describe('CardFooter', () => {
    it('renders correctly', () => {
      render(<CardFooter data-testid="footer">Card Footer</CardFooter>)
      const footer = screen.getByTestId('footer')
      expect(footer).toBeInTheDocument()
      expect(footer).toHaveClass('flex', 'items-center', 'px-6')
      expect(footer).toHaveAttribute('data-slot', 'card-footer')
    })

    it('applies custom className', () => {
      render(<CardFooter className="custom-footer" data-testid="footer">Footer</CardFooter>)
      expect(screen.getByTestId('footer')).toHaveClass('custom-footer')
    })
  })

  describe('CardAction', () => {
    it('renders correctly', () => {
      render(<CardAction data-testid="action">Action</CardAction>)
      const action = screen.getByTestId('action')
      expect(action).toBeInTheDocument()
      expect(action).toHaveClass('col-start-2', 'row-span-2', 'row-start-1', 'self-start', 'justify-self-end')
      expect(action).toHaveAttribute('data-slot', 'card-action')
    })

    it('applies custom className', () => {
      render(<CardAction className="custom-action" data-testid="action">Action</CardAction>)
      expect(screen.getByTestId('action')).toHaveClass('custom-action')
    })
  })

  describe('Full Card Integration', () => {
    it('renders complete card structure', () => {
      render(
        <Card data-testid="full-card">
          <CardHeader>
            <CardTitle>Test Title</CardTitle>
            <CardDescription>Test Description</CardDescription>
            <CardAction>Action Button</CardAction>
          </CardHeader>
          <CardContent>
            <p>This is the card content</p>
          </CardContent>
          <CardFooter>
            <button>Footer Button</button>
          </CardFooter>
        </Card>
      )

      expect(screen.getByTestId('full-card')).toBeInTheDocument()
      expect(screen.getByText('Test Title')).toBeInTheDocument()
      expect(screen.getByText('Test Description')).toBeInTheDocument()
      expect(screen.getByText('Action Button')).toBeInTheDocument()
      expect(screen.getByText('This is the card content')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Footer Button' })).toBeInTheDocument()
    })
  })
})
