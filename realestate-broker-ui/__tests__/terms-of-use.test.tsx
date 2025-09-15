import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import TermsOfUsePage from '../app/terms-of-use/page'

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

vi.mock('@/components/layout/dashboard-shell', () => ({
  DashboardShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DashboardHeader: ({ heading }: { heading: string }) => <h1>{heading}</h1>,
}))

vi.mock('@/components/ui/Card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: React.ReactNode }) => <h2>{children}</h2>,
  CardContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

describe('TermsOfUsePage', () => {
  it('renders terms of use content', () => {
    render(<TermsOfUsePage />)
    expect(screen.getByText('תנאי שימוש')).toBeInTheDocument()
    expect(screen.getByText('הגדרות')).toBeInTheDocument()
  })
})
