// @vitest-environment jsdom
import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { describe, it, expect } from 'vitest'
import PageHeader from './PageHeader'

describe('PageHeader', () => {
  it('renders layout primitives with metadata and actions', () => {
    render(
      <PageHeader
        title="לוח מחוונים"
        description="מבט מהיר על פעילות המשרד"
        breadcrumbs={<nav>בית / לוח מחוונים</nav>}
        meta={<span>עודכן לפני דקה</span>}
        actions={<button type="button">רענן</button>}
      >
        <div data-testid="page-header-children">תוכן נוסף</div>
      </PageHeader>
    )

    expect(screen.getByRole('heading', { level: 1, name: 'לוח מחוונים' })).toBeInTheDocument()
    expect(screen.getByText('מבט מהיר על פעילות המשרד')).toBeInTheDocument()
    expect(screen.getByTestId('page-header-breadcrumbs')).toHaveTextContent('בית / לוח מחוונים')
    expect(screen.getByTestId('page-header-meta')).toHaveTextContent('עודכן לפני דקה')
    expect(screen.getByTestId('page-header-actions')).toBeInTheDocument()
    expect(screen.getByTestId('page-header-children')).toBeInTheDocument()

    const header = document.querySelector('header')
    expect(header).toHaveClass('w-full')
    const container = header?.querySelector('div')
    expect(container).toHaveClass('max-w-[var(--container-max)]')
  })

  it('supports custom title nodes', () => {
    render(
      <PageHeader
        title={<span data-testid="custom-title">Custom Title</span>}
        description={null}
      />
    )

    expect(screen.getByTestId('custom-title')).toBeInTheDocument()
  })
})
