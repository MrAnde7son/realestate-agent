/**
 * @vitest-environment jsdom
 */

import React from 'react'
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import '@testing-library/jest-dom'
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'

import { ListingsPanel } from '../listings-panel'

const { mockApiGet } = vi.hoisted(() => ({
  mockApiGet: vi.fn()
}))

vi.mock('@/lib/api-client', () => ({
  api: {
    get: mockApiGet
  }
}))

vi.mock('@/hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackFeatureUsage: vi.fn()
  })
}))

describe('ListingsPanel', () => {
  beforeAll(() => {
    vi.stubGlobal('ResizeObserver', class {
      observe() {}
      unobserve() {}
      disconnect() {}
    })
    vi.spyOn(window, 'open').mockImplementation(() => null)
    Object.defineProperty(window.HTMLElement.prototype, 'scrollIntoView', {
      value: vi.fn(),
      configurable: true,
    })
    Object.defineProperty(window.HTMLElement.prototype, 'hasPointerCapture', {
      value: () => false,
      configurable: true,
    })
    Object.defineProperty(window.HTMLElement.prototype, 'setPointerCapture', {
      value: () => {},
      configurable: true,
    })
    Object.defineProperty(window.HTMLElement.prototype, 'releasePointerCapture', {
      value: () => {},
      configurable: true,
    })
  })

  beforeEach(() => {
    mockApiGet.mockClear()
    mockApiGet.mockImplementation(async (url: string) => {
      const params = new URL(url, 'http://example.com').searchParams
      const listingType = params.get('listing_type') ?? 'rent'

      return {
        ok: true,
        data: {
          results: [
            {
              id: `${listingType}:1`,
              title: listingType === 'sale' ? 'בית למכירה' : 'דירה להשכרה',
              address: 'רחוב הבדיקה 1',
              listing_type: listingType,
              listingType,
              ad_type: listingType === 'sale' ? 'broker' : 'private',
              adType: listingType === 'sale' ? 'broker' : 'private',
              contact_name: 'Dana',
              contact_phone: '050-1234567',
              recent_deal: listingType === 'rent',
              photos: ['http://example.com/photo.jpg'],
              video_url: 'http://example.com/video.mp4',
              price: 1_500_000,
              rooms: 3,
              size: 100,
              source: 'yad2',
              date_posted: '2024-01-01T00:00:00Z'
            }
          ],
          count: 1,
          total_all: 1,
          limit: 10,
          offset: 0,
          ordering: '-date_posted',
          filters: {
            source: ['yad2'],
            property_type: ['דירה'],
            listing_type: ['rent', 'sale'],
            ad_type: ['private', 'broker'],
            rooms: [],
            price: { min: null, max: null }
          }
        }
      }
    })
  })

  it('renders listing metadata and supports filtering by listing type', async () => {
    render(<ListingsPanel assetId={123} assetAddress="רחוב הבדיקה 1" />)

    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledTimes(1)
    })

    expect(await screen.findByText('השכרה')).toBeInTheDocument()
    expect(screen.getByText('Dana')).toBeInTheDocument()
    expect(screen.getByText('050-1234567')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'פתח וידאו' })).toBeInTheDocument()
    expect(screen.getByText('כן')).toBeInTheDocument()

    const filterButton = screen.getByRole('button', { name: /סינון/ })
    fireEvent.click(filterButton)

    const filterSheet = await screen.findByRole('dialog')
    const listingTypeLabel = within(filterSheet).getByText('סוג עסקה')
    const listingTypeContainer = listingTypeLabel.parentElement as HTMLElement
    const listingTypeTrigger = listingTypeContainer.querySelector('[role="combobox"]') as HTMLElement | null

    expect(listingTypeTrigger).not.toBeNull()
    fireEvent.pointerDown(listingTypeTrigger!)
    fireEvent.click(listingTypeTrigger!)

    const saleOption = await screen.findByRole('option', { name: 'מכירה' })
    fireEvent.click(saleOption)

    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledTimes(2)
    })

    const secondCallUrl = mockApiGet.mock.calls[1][0]
    expect(secondCallUrl).toContain('listing_type=sale')
  })
})
