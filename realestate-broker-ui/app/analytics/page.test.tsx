/* eslint-env jest */
import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import AnalyticsPage from './page'
import { vi } from 'vitest'

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

describe('AnalyticsPage', () => {
  it('loads and displays analytics data', async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url === '/api/analytics/property-types') {
        return Promise.resolve({ json: () => Promise.resolve({ rows: [{ property_type: 'Apartment', count: 2 }] }) })
      }
      return Promise.resolve({ json: () => Promise.resolve({ rows: [{ area: 'Tel Aviv', count: 3 }] }) })
    })
    vi.stubGlobal('fetch', fetchMock as any)

    render(<AnalyticsPage />)
    expect(await screen.findByText('Apartment')).toBeInTheDocument()
    expect(await screen.findByText('Tel Aviv')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/analytics/property-types')
    expect(fetchMock).toHaveBeenCalledWith('/api/analytics/market-activity')
  })
})
