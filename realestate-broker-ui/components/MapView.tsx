'use client'
import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import { Loader2, MapPin, Search, Layers, ArrowLeft } from 'lucide-react'
import maplibregl from 'maplibre-gl'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { MapLayerService, LayerConfig } from '@/lib/map-layer-service'
import type { Asset } from '@/lib/normalizers/asset'
import { buildMarkerDisplayData, shouldDisplayMarkerLabel, type MarkerDisplayData } from '@/components/map-marker-utils'
import { normalizeToLonLat } from '@/lib/geo/transform'
import { useMediaQuery } from '@/hooks/use-media-query'
import { cn } from '@/lib/utils'
import 'maplibre-gl/dist/maplibre-gl.css'

type MarkerElement = HTMLDivElement & { __cleanupTooltip?: () => void }

const isCoarsePointerEnvironment = (): boolean => {
  if (typeof window === 'undefined') return false
  const { matchMedia, navigator } = window

  const queries = ['(pointer: coarse)', '(hover: none)']
  for (const query of queries) {
    try {
      if (matchMedia?.(query)?.matches) {
        return true
      }
    } catch (error) {
      console.warn('MapView: matchMedia check failed', error)
    }
  }

  if (navigator) {
    const nav = navigator as Navigator & { msMaxTouchPoints?: number }
    if (typeof nav.maxTouchPoints === 'number' && nav.maxTouchPoints > 0) return true
    if (typeof nav.msMaxTouchPoints === 'number' && nav.msMaxTouchPoints > 0) return true
  }

  return false
}

interface MapViewProps {
  assets: Asset[]
  center: [number, number]
  zoom: number
  onAssetClick: (asset: Asset) => void
  searchValue: string
  onSearchChange: (value: string) => void
  height?: string
  onBackToTable?: () => void
}

interface GeocodingResult {
  place_id: string
  formatted_address: string
  geometry: {
    location: {
      lat: number
      lng: number
    }
  }
}

const createTooltipElement = (display: MarkerDisplayData) => {
  const tooltip = document.createElement('div')
  tooltip.className = 'asset-marker-tooltip'
  tooltip.dataset.visible = 'false'
  tooltip.setAttribute('role', 'tooltip')

  const card = document.createElement('div')
  card.className = 'asset-marker-tooltip-card'
  tooltip.appendChild(card)

  if (display.photoUrl) {
    const photoWrapper = document.createElement('div')
    photoWrapper.className = 'asset-marker-tooltip-photo'
    const img = document.createElement('img')
    img.src = display.photoUrl
    img.alt = display.shortAddress
    img.loading = 'lazy'
    photoWrapper.appendChild(img)
    card.appendChild(photoWrapper)
  }

  const details = document.createElement('div')
  details.className = 'asset-marker-tooltip-details'
  card.appendChild(details)

  const addressEl = document.createElement('div')
  addressEl.className = 'asset-marker-tooltip-address'
  addressEl.textContent = display.fullAddress
  details.appendChild(addressEl)

  if (display.priceLabel) {
    const priceEl = document.createElement('div')
    priceEl.className = 'asset-marker-tooltip-price'
    priceEl.textContent = display.priceLabel
    details.appendChild(priceEl)
  }

  if (display.cityLine) {
    const cityEl = document.createElement('div')
    cityEl.className = 'asset-marker-tooltip-city'
    cityEl.textContent = display.cityLine
    details.appendChild(cityEl)
  }

  const metaItems = [
    display.areaLabel,
    display.roomsLabel,
    display.propertyType,
    display.pricePerSqmLabel,
  ].filter((value): value is string => Boolean(value))

  if (metaItems.length) {
    const metaEl = document.createElement('div')
    metaEl.className = 'asset-marker-tooltip-meta'
    metaItems.forEach(text => {
      const itemEl = document.createElement('span')
      itemEl.textContent = text
      metaEl.appendChild(itemEl)
    })
    details.appendChild(metaEl)
  }

  if (display.features.length) {
    const featuresEl = document.createElement('div')
    featuresEl.className = 'asset-marker-tooltip-features'
    featuresEl.textContent = display.features.join(' • ')
    details.appendChild(featuresEl)
  }

  if (display.sourceLabel) {
    const sourceEl = document.createElement('div')
    sourceEl.className = 'asset-marker-tooltip-source'
    sourceEl.textContent = `מקור: ${display.sourceLabel}`
    details.appendChild(sourceEl)
  }

  return tooltip
}


class GeocodingService {
  private apiKey: string | undefined
  constructor() { this.apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY }

  async searchPlaces(query: string): Promise<GeocodingResult[]> {
    if (!this.apiKey) return this.getMockResults(query)
    try {
      const response = await fetch(
        `https://maps.googleapis.com/maps/api/place/autocomplete/json?input=${encodeURIComponent(query)}&key=${this.apiKey}&language=he&region=il`
      )
      const data = await response.json()
      if (data.status === 'OK') {
        return data.predictions.map((prediction: any) => ({
          place_id: prediction.place_id,
          formatted_address: prediction.description,
          geometry: { location: { lat: 0, lng: 0 } }
        }))
      }
      return []
    } catch (error) {
      console.error('Error searching places:', error)
      return this.getMockResults(query)
    }
  }

  async geocodeAddress(address: string): Promise<GeocodingResult | null> {
    if (!this.apiKey) return this.getMockGeocodeResult(address)
    try {
      const response = await fetch(
        `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&key=${this.apiKey}&language=he&region=il`
      )
      const data = await response.json()
      if (data.status === 'OK' && data.results.length > 0) {
        const result = data.results[0]
        return {
          place_id: result.place_id,
          formatted_address: result.formatted_address,
          geometry: { location: { lat: result.geometry.location.lat, lng: result.geometry.location.lng } }
        }
      }
      return null
    } catch (error) {
      console.error('Error geocoding address:', error)
      return this.getMockGeocodeResult(address)
    }
  }

  private getMockResults(query: string): GeocodingResult[] {
    const mockResults = [
      { place_id: '1', formatted_address: 'תל אביב-יפו, ישראל', geometry: { location: { lat: 32.0853, lng: 34.7818 } } },
      { place_id: '2', formatted_address: 'ירושלים, ישראל', geometry: { location: { lat: 31.7683, lng: 35.2137 } } },
      { place_id: '3', formatted_address: 'חיפה, ישראל', geometry: { location: { lat: 32.7940, lng: 34.9896 } } },
      { place_id: '4', formatted_address: 'באר שבע, ישראל', geometry: { location: { lat: 31.2518, lng: 34.7915 } } },
      { place_id: '5', formatted_address: 'נתניה, ישראל', geometry: { location: { lat: 32.3215, lng: 34.8532 } } }
    ]
    return mockResults.filter(r => r.formatted_address.toLowerCase().includes(query.toLowerCase()))
  }

  private getMockGeocodeResult(address: string): GeocodingResult | null {
    return {
      place_id: 'mock-1',
      formatted_address: address,
      geometry: { location: { lat: 32.0853, lng: 34.7818 } }
    }
  }
}

export default function MapView({
  assets,
  center,
  zoom,
  onAssetClick,
  searchValue,
  onSearchChange,
  height = '600px',
  onBackToTable
}: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  function getMapOrThrow(): maplibregl.Map {
    const m = map.current
    if (!m) throw new Error('Map not initialized')
    return m
  }
  const layerService = useRef<MapLayerService | null>(null)
  const geocodingService = useRef<GeocodingService | null>(null)
  const markersRef = useRef<Record<string | number, maplibregl.Marker>>({})
  const coarsePointerRef = useRef(false)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [localSearchValue, setLocalSearchValue] = useState(searchValue)
  const [searchResults, setSearchResults] = useState<GeocodingResult[]>([])
  const [showSearchResults, setShowSearchResults] = useState(false)
  const [layers, setLayers] = useState<LayerConfig[]>([])
  const [showLayerControls, setShowLayerControls] = useState(false)

  const { matches: isMobile } = useMediaQuery('(max-width: 768px)', {
    defaultValue: false,
    initializeWithValue: true,
  })

  const containerClasses = cn(
    'relative w-full overflow-hidden',
    isMobile ? 'fixed inset-0 z-50 rounded-none bg-background' : 'rounded-lg'
  )

  const computedHeight = isMobile ? height ?? '100dvh' : height

  useEffect(() => { geocodingService.current = new GeocodingService() }, [])
  
  // Sync local search value with prop
  useEffect(() => {
    setLocalSearchValue(searchValue)
  }, [searchValue])

  // Filter assets based on search query
  const filteredAssets = useMemo(() => {
    if (!localSearchValue?.trim()) return assets
    
    const query = localSearchValue.trim().toLowerCase()
    return assets.filter(asset => {
      const address = asset.address?.toLowerCase() || ''
      const city = asset.city?.toLowerCase() || ''
      const neighborhood = asset.neighborhood?.toLowerCase() || ''
      const street = asset.street?.toLowerCase() || ''
      const normalizedAddress = asset.normalizedAddress?.toLowerCase() || ''
      
      return address.includes(query) ||
             city.includes(query) ||
             neighborhood.includes(query) ||
             street.includes(query) ||
             normalizedAddress.includes(query)
    })
  }, [assets, localSearchValue])

  const syncMarkerLabelVisibility = useCallback(() => {
    if (!map.current) return

    const totalMarkers = Object.keys(markersRef.current).length
    const shouldPersist = shouldDisplayMarkerLabel({
      totalAssets: totalMarkers,
      zoom: map.current.getZoom(),
      preferTouchDevice: coarsePointerRef.current,
    })

    Object.values(markersRef.current).forEach(marker => {
      const element = marker.getElement() as HTMLElement | null
      if (!element) return
      const label = element.querySelector<HTMLDivElement>('.asset-marker-label')
      const tooltip = element.querySelector<HTMLDivElement>('.asset-marker-tooltip')
      if (!label) return

      label.dataset.persist = shouldPersist ? 'true' : 'false'

      if (shouldPersist) {
        label.dataset.visible = 'true'
        label.setAttribute('aria-hidden', 'false')
      } else if (!tooltip || tooltip.dataset.visible !== 'true') {
        label.classList.remove('asset-marker-label--hover')
        label.dataset.visible = 'false'
        label.setAttribute('aria-hidden', 'true')
      }
    })
  }, [])

  useEffect(() => {
    if (!map.current) return
    const handleZoom = () => syncMarkerLabelVisibility()
    const instance = map.current
    instance.on('zoomend', handleZoom)
    return () => {
      instance.off('zoomend', handleZoom)
    }
  }, [syncMarkerLabelVisibility])

  const addAssetMarkers = useCallback(() => {
    if (!map.current) return

    const m = getMapOrThrow()
    console.log('MapView: Adding markers for', filteredAssets.length, 'assets (filtered from', assets.length, ')')
    console.log('MapView: Map center:', map.current.getCenter())
    console.log('MapView: Map zoom:', map.current.getZoom())

    // Remove existing markers properly
    Object.values(markersRef.current).forEach(markerInstance => {
      const element = markerInstance.getElement() as MarkerElement | null
      element?.__cleanupTooltip?.()
      markerInstance.remove()
    })
    markersRef.current = {}

    if (!filteredAssets.length) {
      syncMarkerLabelVisibility()
      return
    }

    const normalizedPoints: Array<{ lon: number; lat: number; asset: Asset; src: string }> = [];
    const preferTouchDevice = isCoarsePointerEnvironment()
    const supportsPointerEvents = typeof window !== 'undefined' && 'PointerEvent' in window
    const outsideEventName: 'pointerdown' | 'touchstart' = supportsPointerEvents ? 'pointerdown' : 'touchstart'
    coarsePointerRef.current = preferTouchDevice

    const labelsVisibleByDefault = shouldDisplayMarkerLabel({
      totalAssets: filteredAssets.length,
      zoom: map.current?.getZoom(),
      preferTouchDevice,
    })

    filteredAssets.forEach((asset: Asset) => {
      const pt = normalizeToLonLat({
        lon: asset.lon,
        lat: asset.lat,
        // ITM from your GIS
        x: (asset as any)?.gisCoordinates?.x,
        y: (asset as any)?.gisCoordinates?.y,
        // govmap: try both 3857 & explicit lon/lat if present
        x_itm: (asset as any)?.govmap_data?.coordinates?.x_itm ?? (asset as any)?.govmap_data?.coordinates?.x,
        y_itm: (asset as any)?.govmap_data?.coordinates?.y_itm ?? (asset as any)?.govmap_data?.coordinates?.y,
        // also pass through the whole govmap blob for lon_wgs84/lat_wgs84 autodetect
        govmap_data: (asset as any)?.govmap_data,
      });
    
      if (!pt) {
        console.warn(`Skip asset ${asset.id}: cannot normalize coords`, asset);
        return;
      }
    
      const { lat, lon, source } = pt as any;
      normalizedPoints.push({ lon, lat, asset, src: source });
    
      const displayData = buildMarkerDisplayData(asset)

      const markerContainer = document.createElement('div') as MarkerElement
      markerContainer.className = 'asset-marker'
      markerContainer.style.zIndex = '1000'
      markerContainer.style.touchAction = 'manipulation'
      markerContainer.setAttribute('role', 'button')
      markerContainer.tabIndex = 0
      markerContainer.setAttribute('aria-label', displayData.fullAddress)

      const pinEl = document.createElement('div')
      pinEl.className = 'asset-marker-pin'
      markerContainer.appendChild(pinEl)

      const tooltipEl = createTooltipElement(displayData)
      const tooltipId = `asset-tooltip-${asset.id}`
      tooltipEl.id = tooltipId
      markerContainer.setAttribute('aria-describedby', tooltipId)
      markerContainer.appendChild(tooltipEl)

      let skipNextClick = false
      let detachOutsideListener: (() => void) | null = null

      const clearOutsideListener = () => {
        if (detachOutsideListener) {
          detachOutsideListener()
          detachOutsideListener = null
        }
      }

      const showTooltip = () => {
        tooltipEl.dataset.visible = 'true'
      }

      const hideTooltip = () => {
        clearOutsideListener()
        tooltipEl.dataset.visible = 'false'
        skipNextClick = false
      }

      const registerOutsideListener = () => {
        clearOutsideListener()
        const handleOutside = (event: Event) => {
          if (!markerContainer.contains(event.target as Node)) {
            hideTooltip()
          }
        }
        document.addEventListener(outsideEventName, handleOutside, true)
        detachOutsideListener = () => {
          document.removeEventListener(outsideEventName, handleOutside, true)
        }
      }

      markerContainer.addEventListener('mouseenter', showTooltip)
      markerContainer.addEventListener('mouseleave', hideTooltip)
      markerContainer.addEventListener('focus', showTooltip)
      markerContainer.addEventListener('blur', hideTooltip)

      const handleCoarsePointerDown = (event: PointerEvent | TouchEvent) => {
        if (!preferTouchDevice) return
        const pointerType = 'pointerType' in event ? (event as PointerEvent).pointerType : 'touch'
        if (pointerType && pointerType !== 'touch' && pointerType !== 'pen') return

        const tooltipVisible = tooltipEl.dataset.visible === 'true'
        if (!tooltipVisible) {
          skipNextClick = true
          showTooltip()
          registerOutsideListener()
        } else {
          skipNextClick = false
        }
      }

      if (supportsPointerEvents) {
        markerContainer.addEventListener('pointerdown', handleCoarsePointerDown as (event: PointerEvent) => void)
      } else {
        markerContainer.addEventListener('touchstart', handleCoarsePointerDown as (event: TouchEvent) => void, {
          passive: true,
        })
      }

      markerContainer.addEventListener('click', event => {
        if (skipNextClick) {
          skipNextClick = false
          event.preventDefault()
          event.stopPropagation()
          return
        }

        hideTooltip()
        onAssetClick(asset)
      })
      markerContainer.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          hideTooltip()
          onAssetClick(asset)
        }
      })

      markerContainer.__cleanupTooltip = () => {
        hideTooltip()
      }

      const marker = new maplibregl.Marker({ element: markerContainer, anchor: 'bottom' })
      .setLngLat([lon, lat])
      .addTo(m)
      markersRef.current[asset.id] = marker
      console.log(`Marker added for asset ${asset.id} at [${lon}, ${lat}] (src=${source})`);
    });
    
    console.log(`MapView: Marker summary - Total: ${assets.length}, Valid: ${normalizedPoints.length}`);
    
    // Fit bounds using the normalized points
    if (normalizedPoints.length > 0) {
      const lons = normalizedPoints.map(p => p.lon);
      const lats = normalizedPoints.map(p => p.lat);
      const bounds: [[number, number], [number, number]] = [
        [Math.min(...lons), Math.min(...lats)],
        [Math.max(...lons), Math.max(...lats)],
      ];
      console.log(
        `Bounds (lon): ${bounds[0][0]} ${bounds[1][0]}  (lat): ${bounds[0][1]} ${bounds[1][1]}`
      );
      map.current.fitBounds(bounds, { padding: 50 });
    }

    syncMarkerLabelVisibility()
  }, [filteredAssets, onAssetClick, syncMarkerLabelVisibility, assets.length])

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return

    const initializeMap = async () => {
      try {
        map.current = new maplibregl.Map({
          container: mapContainer.current!,
          style: {
            version: 8,
            sources: {
              osm: {
                type: 'raster',
                tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
                tileSize: 256,
                attribution: '© OpenStreetMap contributors',
              },
            },
            layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
          },
          center,
          zoom,
          attributionControl: false,
          // Keep the viewport in/near Israel to avoid fly-outs
          maxBounds: [
            [33.0, 28.5], // SW
            [36.5, 34.5], // NE
          ],
        })

        // Initialize layer service
        layerService.current = new MapLayerService(map.current)

        map.current.on('load', async () => {
          setLoading(false)

          try {
            if (layerService.current) {
              await layerService.current.loadAllLayers()
              setLayers(layerService.current.getAllLayers())
            }
          } catch (err) {
            console.warn('Error loading layers:', err)
          }

          addAssetMarkers()
        })

        map.current.on('error', (e: any) => {
          if (e.error?.message?.includes('could not be decoded')) {
            console.warn('Tile loading error (non-critical):', e.error.message)
            return
          }
          console.error('Map error:', e)
          setError('שגיאה בטעינת המפה')
          setLoading(false)
        })
      } catch (err) {
        console.error('Error initializing map:', err)
        setError('שגיאה בטעינת המפה')
        setLoading(false)
      }
    }

    initializeMap()

    return () => {
      if (!map.current) return

      // Remove markers
      Object.values(markersRef.current).forEach(m => m.remove())
      markersRef.current = {}

      // Destroy layer service
      layerService.current?.destroy()

      try {
        const style = map.current.getStyle()
        if (style?.layers) {
          const layerIds = style.layers.map((l: any) => l.id).reverse()
          layerIds.forEach((id: string) => {
            if (map.current!.getLayer(id)) map.current!.removeLayer(id)
          })
        }
        if (style?.sources) {
          Object.keys(style.sources).forEach(srcId => {
            if (map.current!.getSource(srcId)) map.current!.removeSource(srcId)
          })
        }
      } catch (err) {
        console.warn('Error cleaning up layers/sources:', err)
      }

      try {
        map.current.remove()
      } catch (err) {
        console.warn('Error removing map:', err)
      }

      map.current = null
      layerService.current = null
      geocodingService.current = null
    }
  }, [center, zoom, addAssetMarkers])

  // Update markers when filtered assets change
  useEffect(() => {
    if (map.current) addAssetMarkers()
  }, [addAssetMarkers, filteredAssets])

  // Search handlers - search assets first, then geographic places as fallback
  const handleSearch = useCallback(async (query: string) => {
    if (!query.trim()) { 
      setSearchResults([])
      setShowSearchResults(false)
      return
    }
    
    // First, show asset results (filteredAssets already handles this)
    // For geographic search, show places as additional option
    if (geocodingService.current) {
      try {
        const results = await geocodingService.current.searchPlaces(query)
        setSearchResults(results)
        setShowSearchResults(true)
      } catch (error) {
        console.error('Search error:', error)
      }
    }
  }, [])

  useEffect(() => {
    const timeoutId = setTimeout(() => { handleSearch(localSearchValue) }, 300)
    return () => clearTimeout(timeoutId)
  }, [localSearchValue, handleSearch])

  const handleSearchResultClick = useCallback(async (result: GeocodingResult) => {
    if (!map.current || !geocodingService.current) return
    try {
      const geocoded = await geocodingService.current.geocodeAddress(result.formatted_address)
      if (geocoded) {
        map.current.flyTo({
          center: [geocoded.geometry.location.lng, geocoded.geometry.location.lat],
          zoom: 16
        })
        onSearchChange(geocoded.formatted_address)
      }
    } catch (error) {
      console.error('Error geocoding result:', error)
    }
    setShowSearchResults(false)
  }, [onSearchChange])

  // Layer controls
  const toggleLayer = useCallback((layerId: string) => {
    if (!layerService.current) return
    layerService.current.toggleLayer(layerId)
    setLayers([...layerService.current.getAllLayers()])
  }, [])

  const setLayerOpacity = useCallback((layerId: string, opacity: number) => {
    if (!layerService.current) return
    layerService.current.setLayerOpacity(layerId, opacity)
    setLayers([...layerService.current.getAllLayers()])
  }, [])

  // Export map snapshot (unchanged)
  const exportMapSnapshot = useCallback(async (options: { layers?: string[], withOrthophoto?: boolean } = {}) => {
    if (!map.current) throw new Error('Map not initialized')
    try {
      if (options.layers) options.layers.forEach(id => layerService.current?.setLayerVisibility(id, true))
      if (options.withOrthophoto) {
        layerService.current?.setLayerVisibility('jerusalem-ortho-2025', true)
        layerService.current?.setLayerVisibility('telaviv-ortho', true)
        layerService.current?.setLayerVisibility('haifa-ortho-2023', true)
      }
      await new Promise(res => setTimeout(res, 1000))
      const canvas = map.current.getCanvas()
      return canvas.toDataURL('image/png')
    } catch (error) {
      console.error('Error exporting map snapshot:', error)
      throw error
    }
  }, [])

  if (error) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground" style={{ height }}>
        <div className="text-center">
          <MapPin className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div
      data-testid="map-view-container"
      className={containerClasses}
      style={{ height: computedHeight }}
    >
      {loading && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-muted">
          <div className="flex flex-col items-center space-y-2">
            <Loader2 className="h-6 w-6 animate-spin text-brand-teal" />
            <span className="text-sm text-muted-foreground">טוען מפה...</span>
          </div>
        </div>
      )}

      {/* Back to Table */}
      {onBackToTable && (
        <div className="absolute top-4 start-4 z-20">
          <Button
            variant="outline"
            size="sm"
            onClick={onBackToTable}
            className={cn(
              'bg-white/90 backdrop-blur-sm transition-shadow',
              isMobile ? 'h-10 w-10 rounded-full p-0 shadow-md' : 'h-8 px-3'
            )}
            title="חזרה לטבלה"
            aria-label="חזרה לטבלה"
          >
            <ArrowLeft
              className={cn(
                'rtl:rotate-180',
                isMobile ? 'h-5 w-5' : 'h-4 w-4 me-2'
              )}
            />
            {!isMobile && <span>חזרה לטבלה</span>}
          </Button>
        </div>
      )}

      {/* Search Bar */}
      <div
        className={cn(
          'absolute top-4 z-20',
          isMobile
            ? onBackToTable
              ? 'start-16 end-4'
              : 'start-4 end-4'
            : onBackToTable
              ? 'start-48 end-24'
              : 'start-4 end-24'
        )}
      >
        <div className={cn('relative', isMobile ? 'w-full max-w-full' : 'max-w-xs')}>
          <Search
            className={cn(
              'absolute end-2 top-1/2 -translate-y-1/2 transform text-muted-foreground',
              isMobile ? 'h-4 w-4' : 'h-3.5 w-3.5'
            )}
          />
          <Input
            value={localSearchValue}
            onChange={(e) => {
              const value = e.target.value
              setLocalSearchValue(value)
              // Don't immediately update parent to prevent reload
              // Parent will be updated on Enter key or when search is cleared
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                setShowSearchResults(false)
                // Update parent on enter
                onSearchChange(localSearchValue)
              }
              if (e.key === 'Escape') {
                setShowSearchResults(false)
              }
            }}
            placeholder="חפש נכסים לפי כתובת, עיר או שכונה..."
            className={cn(
              'pe-8 text-sm bg-white/90 backdrop-blur-sm',
              isMobile ? 'h-10 shadow-md' : 'h-8'
            )}
            dir="rtl"
            onFocus={() => {
              if (localSearchValue) {
                setShowSearchResults(true)
              }
            }}
          />
          {/* Asset search results count */}
          {localSearchValue && (
            <div className="absolute top-full start-0 end-0 mt-1 bg-white rounded-md shadow-lg border z-30">
              <div className="px-4 py-2 text-sm text-muted-foreground border-b">
                נמצאו {filteredAssets.length} נכסים מתוך {assets.length}
              </div>
              {/* Geographic search results as additional options */}
              {showSearchResults && searchResults.length > 0 && (
                <div className="max-h-48 overflow-y-auto">
                  <div className="px-4 py-2 text-xs font-semibold text-muted-foreground border-b bg-gray-50">
                    מיקומים גיאוגרפיים:
                  </div>
                  {searchResults.map((result) => (
                    <button
                      key={result.place_id}
                      onClick={() => handleSearchResultClick(result)}
                      className="w-full px-4 py-2 text-start hover:bg-gray-50 border-b last:border-b-0 text-sm"
                    >
                      📍 {result.formatted_address}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Layer Controls */}
      <div className="absolute top-4 end-4 z-20">
        <Popover open={showLayerControls} onOpenChange={setShowLayerControls}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className={cn(
                'bg-white/90 backdrop-blur-sm transition-shadow',
                isMobile ? 'h-10 w-10 rounded-full p-0 shadow-md' : 'h-8 px-2'
              )}
              aria-label="ניהול שכבות"
              title="ניהול שכבות"
            >
              <Layers
                className={cn(
                  'text-muted-foreground',
                  isMobile ? 'h-4 w-4' : 'h-3.5 w-3.5 me-1.5'
                )}
              />
              {!isMobile && <span className="text-xs">שכבות</span>}
            </Button>
          </PopoverTrigger>
          <PopoverContent
            className={cn(
              'bg-white text-gray-900 border border-gray-200',
              isMobile ? 'w-64 max-w-[90vw]' : 'w-80'
            )}
            align="end"
          >
            <div className="space-y-4">
              <h4 className="font-medium">ניהול שכבות</h4>
              {layers.map((layer) => (
                <div key={layer.id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor={`layer-${layer.id}`} className="text-sm">
                      {layer.label}
                    </Label>
                    <Switch
                      id={`layer-${layer.id}`}
                      checked={layer.visible}
                      onCheckedChange={() => toggleLayer(layer.id)}
                    />
                  </div>
                  {layer.visible && (
                    <div className="space-y-1">
                      <Label className="text-xs text-muted-foreground">
                        שקיפות: {Math.round(layer.opacity * 100)}%
                      </Label>
                      <Slider
                        value={[layer.opacity]}
                        onValueChange={([value]) => setLayerOpacity(layer.id, value)}
                        max={1}
                        min={0}
                        step={0.1}
                        className="w-full"
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </PopoverContent>
        </Popover>
      </div>

      {/* Asset Count */}
      <div className="absolute bottom-4 start-4 z-20">
        <div
          className={cn(
            'bg-white/90 backdrop-blur-sm rounded-md px-3 py-2 text-sm',
            isMobile && 'text-xs shadow-md'
          )}
        >
          <span className="font-medium">{assets.length}</span> נכסים
        </div>
      </div>

      {/* Map Container */}
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  )
}
