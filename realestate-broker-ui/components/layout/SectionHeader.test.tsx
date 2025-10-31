// @vitest-environment jsdom
import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { describe, it, expect } from 'vitest'
import SectionHeader from './SectionHeader'

describe('SectionHeader', () => {
  it('renders title, description and actions', () => {
    render(
      <SectionHeader
        title="סטטיסטיקות"
        description="תמונת מצב יומית"
        actions={<button type="button">ייצוא</button>}
      >
        <span data-testid="section-header-children">תוכן נוסף</span>
      </SectionHeader>
    )

    expect(screen.getByRole('heading', { level: 2, name: 'סטטיסטיקות' })).toBeInTheDocument()
    expect(screen.getByText('תמונת מצב יומית')).toBeInTheDocument()
    expect(screen.getByTestId('section-header-actions')).toBeInTheDocument()
    expect(screen.getByTestId('section-header-children')).toBeInTheDocument()

    const header = document.querySelector('header')
    expect(header).toHaveClass('border-b')
  })

  it('accepts custom node titles', () => {
    render(
      <SectionHeader
        title={<span data-testid="custom-node">כותרת מותאמת</span>}
      />
    )

    expect(screen.getByTestId('custom-node')).toBeInTheDocument()
  })
})
