import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import UserGuidePage from '../app/user-guide/page'

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

vi.mock('@/components/layout/dashboard-shell', () => ({
  DashboardShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DashboardHeader: ({ heading }: { heading: string }) => <h1>{heading}</h1>,
}))

describe('UserGuidePage', () => {
  it('renders user guide content', () => {
    render(<UserGuidePage />)
    expect(screen.getByText('מדריך משתמש')).toBeInTheDocument()
    expect(screen.getByText('התחלה מהירה')).toBeInTheDocument()
  })
})
