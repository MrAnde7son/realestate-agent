import React from 'react'
import { describe, expect, it, beforeEach, afterAll, beforeAll, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import AssetCard from './AssetCard'
import type { Asset } from '@/lib/normalizers/asset'

const push = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push,
  }),
}))

const mockAsset: Asset = {
  id: 42,
  address: 'נכס בדיקה',
  assetStatus: 'done',
  rooms: 4,
  bathrooms: 2,
  area: 120,
  price: 2_500_000,
}

const createObjectURLMock = vi.fn(() => 'blob:mock-url')

let originalCreateObjectURL: typeof URL.createObjectURL | undefined
let createObjectURLSpy: ReturnType<typeof vi.spyOn> | null = null

beforeAll(() => {
  originalCreateObjectURL = (URL as any).createObjectURL

  if (originalCreateObjectURL) {
    createObjectURLSpy = vi
      .spyOn(URL, 'createObjectURL')
      .mockImplementation(createObjectURLMock)
  } else {
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      writable: true,
      value: createObjectURLMock,
    })
  }
})

afterAll(() => {
  if (createObjectURLSpy) {
    createObjectURLSpy.mockRestore()
  } else {
    delete (URL as any).createObjectURL
  }
})

beforeEach(() => {
  push.mockClear()
  createObjectURLMock.mockClear()
})

describe('AssetCard', () => {
  it('navigates to the asset details when the card is clicked', () => {
    render(<AssetCard asset={mockAsset} />)

    const card = screen.getByRole('link', { name: /נכס בדיקה/ })
    fireEvent.click(card)

    expect(push).toHaveBeenCalledWith('/assets/42')
  })

  it('navigates with keyboard activation', () => {
    render(<AssetCard asset={mockAsset} />)

    const card = screen.getByRole('link', { name: /נכס בדיקה/ })
    fireEvent.keyDown(card, { key: 'Enter' })

    expect(push).toHaveBeenCalledWith('/assets/42')
  })

  it('shows loader when asset data is still being collected', () => {
    render(<AssetCard asset={{ ...mockAsset, assetStatus: 'enriching' }} />)

    expect(screen.getByText('אוסף נתונים על הנכס')).toBeInTheDocument()
  })

  it('hides loader when asset data is ready', () => {
    render(<AssetCard asset={{ ...mockAsset, assetStatus: 'done' }} />)

    expect(screen.queryByText('אוסף נתונים על הנכס')).not.toBeInTheDocument()
  })

  it('does not trigger navigation when export is clicked', () => {
    render(<AssetCard asset={mockAsset} />)

    const exportButton = screen.getByRole('button', { name: 'ייצוא פרטי נכס' })
    fireEvent.click(exportButton)

    expect(push).not.toHaveBeenCalled()
    expect(createObjectURLMock).toHaveBeenCalled()
  })

  it('renders watch button and triggers handler', () => {
    const onToggleWatch = vi.fn()
    render(<AssetCard asset={mockAsset} onToggleWatch={onToggleWatch} />)

    const watchButton = screen.getByRole('button', { name: 'הוסף לרשימת המעקב' })
    fireEvent.click(watchButton)

    expect(push).not.toHaveBeenCalled()
    expect(onToggleWatch).toHaveBeenCalledWith(mockAsset)
  })

  it('indicates watched state', () => {
    render(<AssetCard asset={{ ...mockAsset, isWatched: true }} onToggleWatch={() => {}} />)

    const watchButton = screen.getByRole('button', { name: 'הסר מרשימת המעקב' })
    expect(watchButton).toHaveAttribute('aria-pressed', 'true')
  })
})
