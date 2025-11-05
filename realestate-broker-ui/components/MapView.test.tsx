import React from 'react'
import { render, screen, act } from '@testing-library/react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import type { Asset } from '@/lib/normalizers/asset'
import type { LayerConfig } from '@/lib/map-layer-service'

const mockUseMediaQuery = vi.fn((_args: { query: string; options?: any }) => ({
  matches: false,
  isReady: true,
}))

vi.mock('@/hooks/use-media-query', () => ({
  useMediaQuery: (query: string, options?: any) => mockUseMediaQuery({ query, options }) ?? { matches: false, isReady: true },
  default: (query: string, options?: any) => mockUseMediaQuery({ query, options }) ?? { matches: false, isReady: true },
}))

vi.mock('maplibre-gl', () => {
  class MockMap {
    private options: any
    constructor(options: any) {
      this.options = options
    }
    on(event: string, callback: (...args: any[]) => void) {
      if (event === 'load') {
        callback()
      }
      return this
    }
    off() {
      return this
    }
    remove() {}
    getStyle() {
      return { layers: [], sources: {} }
    }
    getLayer() {
      return null
    }
    removeLayer() {}
    getSource() {
      return null
    }
    removeSource() {}
    fitBounds() {}
    getZoom() {
      return this.options?.zoom ?? 10
    }
    getCenter() {
      const [lng = 0, lat = 0] = this.options?.center ?? []
      return { lng, lat }
    }
    setLayoutProperty() {}
    setPaintProperty() {}
    getBounds() {
      return {
        getWest: () => 0,
        getSouth: () => 0,
        getEast: () => 1,
        getNorth: () => 1,
      }
    }
  }

  class MockMarker {
    private element: HTMLElement
    constructor({ element }: { element: HTMLElement }) {
      this.element = element
    }
    setLngLat() {
      return this
    }
    addTo() {
      return this
    }
    getElement() {
      return this.element
    }
    remove() {}
  }

  return {
    default: {
      Map: MockMap,
      Marker: MockMarker,
    },
  }
})

vi.mock('@/lib/map-layer-service', async () => {
  const actual = await vi.importActual<typeof import('@/lib/map-layer-service')>('@/lib/map-layer-service')
  class MockMapLayerService {
    private layers: LayerConfig[]
    constructor() {
      this.layers = [
        {
          id: 'mock-layer',
          label: 'Mock Layer',
          type: 'wmts',
          opacity: 1,
          minzoom: 0,
          maxzoom: 22,
          visible: true,
        } as LayerConfig,
      ]
    }
    async loadAllLayers() {
      return
    }
    getAllLayers() {
      return this.layers
    }
    toggleLayer(id: string) {
      this.layers = this.layers.map((layer) =>
        layer.id === id ? { ...layer, visible: !layer.visible } : layer
      )
    }
    setLayerOpacity(id: string, opacity: number) {
      this.layers = this.layers.map((layer) =>
        layer.id === id ? { ...layer, opacity } : layer
      )
    }
    setLayerVisibility(id: string, visible: boolean) {
      this.layers = this.layers.map((layer) =>
        layer.id === id ? { ...layer, visible } : layer
      )
    }
    destroy() {}
  }

  return {
    ...actual,
    MapLayerService: MockMapLayerService,
  }
})

import MapView from './MapView'

const mockAssets: Asset[] = [
  {
    id: 1,
    lat: 31.5,
    lon: 34.8,
    address: 'Test Street 1',
    city: 'Tel Aviv',
  } as Asset,
]

describe('MapView responsive layout', () => {
  beforeEach(() => {
    mockUseMediaQuery.mockReset()
    mockUseMediaQuery.mockImplementation(() => ({ matches: false, isReady: true }))
  })

  afterEach(() => {
    mockUseMediaQuery.mockReset()
  })

  it('renders full-screen layout with icon-only controls on mobile', async () => {
    mockUseMediaQuery.mockImplementation(({ query }) =>
      query === '(max-width: 768px)'
        ? { matches: true, isReady: true }
        : { matches: false, isReady: true }
    )

    await act(async () => {
      render(
        <MapView
          assets={mockAssets}
          center={[34.8, 31.5]}
          zoom={14}
          onAssetClick={() => {}}
          searchValue=""
          onSearchChange={() => {}}
          onBackToTable={() => {}}
          height="100dvh"
        />
      )
    })

    const container = screen.getByTestId('map-view-container')
    expect(container).toHaveClass('fixed')
    expect(container).toHaveClass('rounded-none')

    const backButton = screen.getByRole('button', { name: 'חזרה לטבלה' })
    expect(backButton).toHaveAttribute('aria-label', 'חזרה לטבלה')
    expect(backButton).not.toHaveTextContent('חזרה לטבלה')

    const layerButton = screen.getByRole('button', { name: 'ניהול שכבות' })
    expect(layerButton).not.toHaveTextContent('שכבות')
  })

  it('shows desktop layout with labeled controls when not mobile', async () => {
    mockUseMediaQuery.mockImplementation(() => ({ matches: false, isReady: true }))

    await act(async () => {
      render(
        <MapView
          assets={mockAssets}
          center={[34.8, 31.5]}
          zoom={14}
          onAssetClick={() => {}}
          searchValue=""
          onSearchChange={() => {}}
          onBackToTable={() => {}}
          height="600px"
        />
      )
    })

    const container = screen.getByTestId('map-view-container')
    expect(container).not.toHaveClass('fixed')
    expect(container).toHaveClass('rounded-lg')

    const backButton = screen.getByRole('button', { name: 'חזרה לטבלה' })
    expect(backButton).toHaveTextContent('חזרה לטבלה')

    const layerButton = screen.getByRole('button', { name: 'ניהול שכבות' })
    expect(layerButton).toHaveTextContent('שכבות')
  })
})
