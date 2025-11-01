/**
 * @vitest-environment jsdom
 */

import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { beforeEach, vi, describe, expect, it} from 'vitest'

import AssetsTable from '@/components/AssetsTable'
import type { Asset } from '@/lib/normalizers/asset'

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() })
}))

vi.mock('@/hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackFeatureUsage: vi.fn(),
    trackSearch: vi.fn()
  })
}))

const COLUMN_PREFERENCES_KEY = 'assets-table-column-preferences'

const baseAsset: Partial<Asset> = {
  id: 1,
  address: 'רחוב הבדיקה 1',
  city: 'תל אביב',
  type: 'דירה',
  area: 100,
  price: 1_500_000,
  pricePerSqm: 15_000,
  deltaVsAreaPct: 0.12,
  domPercentile: 25,
  competition1km: 'בינוני',
  riskFlags: ['ללא']
}

describe('AssetsTable default columns', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('hides advanced metrics by default', async () => {
    render(<AssetsTable data={[baseAsset as Asset]} />)

    await screen.findByRole('columnheader', { name: /נכס/ })

    expect(screen.getByRole('columnheader', { name: /סוג עסקה/ })).toBeInTheDocument()
    const currencyHeaders = screen.getAllByRole('columnheader', { name: /₪/ })
    expect(currencyHeaders.some(header => header.textContent?.includes('₪'))).toBe(true)

    expect(screen.queryByRole('columnheader', { name: /ייעוד/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('columnheader', { name: /שטחי ציבור ≤300מ"/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('columnheader', { name: /קבצים/ })).not.toBeInTheDocument()
  })

  it('respects stored column visibility preferences', async () => {
    localStorage.setItem(COLUMN_PREFERENCES_KEY, JSON.stringify({ zoning: true }))

    render(<AssetsTable data={[baseAsset as Asset]} />)

    await screen.findByRole('columnheader', { name: /נכס/ })

    expect(screen.getByRole('columnheader', { name: /ייעוד/ })).toBeInTheDocument()
    expect(screen.queryByRole('columnheader', { name: /שטחי ציבור ≤300מ"/ })).not.toBeInTheDocument()
  })

  it('restores default columns from the toolbar action', async () => {
    localStorage.setItem(COLUMN_PREFERENCES_KEY, JSON.stringify({ zoning: true }))

    render(<AssetsTable data={[baseAsset as Asset]} />)

    await screen.findByRole('columnheader', { name: /ייעוד/ })

    const columnsButton = screen.getByRole('button', { name: 'עמודות' })
    fireEvent.pointerDown(columnsButton)
    fireEvent.keyDown(columnsButton, { key: 'Enter', code: 'Enter', charCode: 13 })

    const resetButton = await screen.findByRole('button', { name: 'שחזר' })
    fireEvent.click(resetButton)

    await waitFor(() => {
      expect(screen.queryByRole('columnheader', { name: /ייעוד/ })).not.toBeInTheDocument()
    })

    const storedPreferences = localStorage.getItem(COLUMN_PREFERENCES_KEY)
    expect(storedPreferences).not.toBeNull()
    expect(JSON.parse(storedPreferences!)).toMatchObject({ zoning: false })
  })

  it('renders commercial indicator when asset is marked as commercial', async () => {
    const commercialAsset = { ...baseAsset, isCommercial: true } as Asset
    render(<AssetsTable data={[commercialAsset]} />)

    await waitFor(() => {
      expect(screen.getByText('מסחרי')).toBeInTheDocument()
    })
  })
})
