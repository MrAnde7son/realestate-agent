'use client'
import React, { useEffect, useRef, useState, useCallback } from 'react'
import { Loader2, MapPin, Search, Layers, Settings, ArrowLeft, List } from 'lucide-react'
import maplibregl, { Marker } from 'maplibre-gl'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { MapLayerService, LayerConfig } from '@/lib/map-layer-service'
import type { Asset } from '@/lib/normalizers/asset'
import { validateCoordinates, areCoordinatesMissing } from '@/lib/coordinate-utils'

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

class GeocodingService {
  private apiKey: string | undefined

  constructor() {
    this.apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
  }

  async searchPlaces(query: string): Promise<GeocodingResult[]> {
    if (!this.apiKey) {
      // Mock service for development
      return this.getMockResults(query)
    }

    try {
      const response = await fetch(
        `https://maps.googleapis.com/maps/api/place/autocomplete/json?input=${encodeURIComponent(query)}&key=${this.apiKey}&language=he&region=il`
      )
      const data = await response.json()
      
      if (data.status === 'OK') {
        return data.predictions.map((prediction: any) => ({
          place_id: prediction.place_id,
          formatted_address: prediction.description,
          geometry: {
            location: {
              lat: 0, // Will be filled by geocodeAddress
              lng: 0
            }
          }
        }))
      }
      
      return []
    } catch (error) {
      console.error('Error searching places:', error)
      return this.getMockResults(query)
    }
  }

  async geocodeAddress(address: string): Promise<GeocodingResult | null> {
    if (!this.apiKey) {
      // Mock service for development
      return this.getMockGeocodeResult(address)
    }

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
          geometry: {
            location: {
              lat: result.geometry.location.lat,
              lng: result.geometry.location.lng
            }
          }
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
    
    return mockResults.filter(result => 
      result.formatted_address.toLowerCase().includes(query.toLowerCase())
    )
  }

  private getMockGeocodeResult(address: string): GeocodingResult | null {
    // Simple mock that returns Tel Aviv for any address
    return {
      place_id: 'mock-1',
      formatted_address: address,
      geometry: {
        location: {
          lat: 32.0853,
          lng: 34.7818
        }
      }
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
  const map = useRef<any>(null)
  const layerService = useRef<MapLayerService | null>(null)
  const geocodingService = useRef<GeocodingService | null>(null)
  const draw = useRef<any>(null)
  const drawInitialized = useRef<boolean>(false)
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchResults, setSearchResults] = useState<GeocodingResult[]>([])
  const [showSearchResults, setShowSearchResults] = useState(false)
  const [layers, setLayers] = useState<LayerConfig[]>([])
  const [showLayerControls, setShowLayerControls] = useState(false)

  // Initialize services
  useEffect(() => {
    geocodingService.current = new GeocodingService()
  }, [])

  // Add asset markers to map
  const addAssetMarkers = useCallback(() => {
    if (!map.current || !assets.length) return

    // Remove existing markers
    const existingMarkers = document.querySelectorAll('.asset-marker')
    existingMarkers.forEach(marker => marker.remove())

    let validMarkersCount = 0

    // Add new markers
    assets.forEach((asset, index) => {
      // Skip assets with no coordinates (null/undefined) - this is normal
      if (areCoordinatesMissing(asset.lat, asset.lon)) {
        return
      }

      // Validate and convert coordinates using the coordinate utility
      const coords = validateCoordinates(asset.lat, asset.lon)
      
      if (!coords) {
        return
      }

      const { lat, lon } = coords

      const markerEl = document.createElement('div')
      markerEl.className = 'asset-marker'
      markerEl.style.cssText = `
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background-color: #10b981;
        border: 3px solid white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 12px;
      `
      markerEl.innerHTML = `<span>${index + 1}</span>`

      markerEl.addEventListener('click', () => {
        onAssetClick(asset)
      })

      markerEl.addEventListener('mouseenter', () => {
        markerEl.style.transform = 'scale(1.1)'
        markerEl.style.transition = 'transform 0.2s'
      })

      markerEl.addEventListener('mouseleave', () => {
        markerEl.style.transform = 'scale(1)'
      })

      new Marker(markerEl)
        .setLngLat([lon, lat])
        .addTo(map.current)
      
      validMarkersCount++
    })
  }, [assets, onAssetClick])

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
              'osm': {
                type: 'raster',
                tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
                tileSize: 256,
                attribution: '© OpenStreetMap contributors'
              }
            },
            layers: [
              {
                id: 'osm',
                type: 'raster',
                source: 'osm'
              }
            ]
          },
          center,
          zoom,
          attributionControl: false
        })

        // Initialize layer service
        layerService.current = new MapLayerService(map.current)
        
        map.current.on('load', async () => {
          setLoading(false)
          
          // Load all layers only after map style is fully loaded
          try {
            if (layerService.current) {
              await layerService.current.loadAllLayers()
              setLayers(layerService.current.getAllLayers())
            }
          } catch (error) {
            console.warn('Error loading layers:', error)
          }

          // Add asset markers
          addAssetMarkers()
          
          // Initialize drawing tools only after map is fully loaded and only once
          // Temporarily disabled due to MapLibre GL compatibility issues
          /*
          if (!drawInitialized.current) {
            const MapboxDraw = (await import('@mapbox/mapbox-gl-draw')).default
            
            // Check if draw control already exists
            const existingDrawControl = map.current.getContainer().querySelector('.mapbox-gl-draw')
            if (!existingDrawControl) {
              draw.current = new MapboxDraw({
                displayControlsDefault: false,
                controls: {
                  polygon: true,
                  line_string: true,
                  point: true,
                  trash: true
                }
              })
              
              try {
                map.current.addControl(draw.current)
                drawInitialized.current = true
              } catch (error) {
                console.warn('Error adding draw control:', error)
              }
            }
          }
          */
        })

        map.current.on('error', (e: any) => {
          // Suppress tile loading errors as they're not critical
          if (e.error && e.error.message && e.error.message.includes('could not be decoded')) {
            console.warn('Tile loading error (non-critical):', e.error.message)
            return
          }
          
          // Suppress Mapbox Draw compatibility errors
          if (e.error && e.error.message && e.error.message.includes('Expression name must be a string')) {
            console.warn('Mapbox Draw compatibility error (non-critical):', e.error.message)
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
      if (map.current) {
        // Clean up drawing tools first
        if (draw.current) {
          try {
            // Check if the draw control is actually added to the map
            const drawControl = map.current.getContainer().querySelector('.mapbox-gl-draw')
            if (drawControl) {
              // Remove draw control sources before removing the control
              const drawSources = ['mapbox-gl-draw-cold', 'mapbox-gl-draw-hot']
              drawSources.forEach(sourceId => {
                if (map.current.getSource(sourceId)) {
                  map.current.removeSource(sourceId)
                }
              })
              
              map.current.removeControl(draw.current)
            }
          } catch (error) {
            console.warn('Error removing draw control:', error)
          }
        }
        
        // Clean up layer service
        if (layerService.current) {
          layerService.current.destroy()
        }
        
        // Remove all layers and sources before removing the map
        try {
          const style = map.current.getStyle()
          if (style && style.layers) {
            // Remove all layers first (in reverse order to avoid dependency issues)
            const layerIds = style.layers.map((layer: any) => layer.id).reverse()
            layerIds.forEach((layerId: string) => {
              if (map.current.getLayer(layerId)) {
                map.current.removeLayer(layerId)
              }
            })
          }
          
          // Then remove all sources
          if (style && style.sources) {
            Object.keys(style.sources).forEach(sourceId => {
              if (map.current.getSource(sourceId)) {
                map.current.removeSource(sourceId)
              }
            })
          }
        } catch (error) {
          console.warn('Error cleaning up layers and sources:', error)
        }
        
        // Remove the map
        try {
          map.current.remove()
        } catch (error) {
          console.warn('Error removing map:', error)
        }
        
        // Reset refs
        map.current = null
        layerService.current = null
        geocodingService.current = null
        draw.current = null
        drawInitialized.current = false
      }
    }
  }, [center, zoom, addAssetMarkers])

  // Update markers when assets change
  useEffect(() => {
    if (map.current) {
      addAssetMarkers()
    }
  }, [addAssetMarkers])

  // Handle search
  const handleSearch = useCallback(async (query: string) => {
    if (!query.trim()) {
      setSearchResults([])
      setShowSearchResults(false)
      return
    }

    if (!geocodingService.current) return

    try {
      const results = await geocodingService.current.searchPlaces(query)
      setSearchResults(results)
      setShowSearchResults(true)
    } catch (error) {
      console.error('Search error:', error)
    }
  }, [])

  // Debounced search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      handleSearch(searchValue)
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [searchValue, handleSearch])

  // Handle search result selection
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

  // Toggle layer visibility
  const toggleLayer = useCallback((layerId: string) => {
    if (!layerService.current) return
    
    layerService.current.toggleLayer(layerId)
    setLayers([...layerService.current.getAllLayers()])
  }, [])

  // Set layer opacity
  const setLayerOpacity = useCallback((layerId: string, opacity: number) => {
    if (!layerService.current) return
    
    layerService.current.setLayerOpacity(layerId, opacity)
    setLayers([...layerService.current.getAllLayers()])
  }, [])

  if (error) {
    return (
      <div 
        className="flex items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground"
        style={{ height }}
      >
        <div className="text-center">
          <MapPin className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative w-full rounded-lg overflow-hidden" style={{ height }}>
      {loading && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-muted">
          <div className="flex flex-col items-center space-y-2">
            <Loader2 className="h-6 w-6 animate-spin text-brand-teal" />
            <span className="text-sm text-muted-foreground">טוען מפה...</span>
          </div>
        </div>
      )}

      {/* Back to Table Button */}
      {onBackToTable && (
        <div className="absolute top-4 left-4 z-20">
          <Button
            variant="outline"
            size="sm"
            onClick={onBackToTable}
            className="bg-white/90 backdrop-blur-sm"
            title="חזרה לטבלה"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            חזרה לטבלה
          </Button>
        </div>
      )}

      {/* Search Bar */}
      <div className={`absolute top-4 z-20 ${onBackToTable ? 'left-48 right-24' : 'left-4 right-24'}`}>
        <div className="relative">
          <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="חפש מיקום..."
            className="pr-10 bg-white/90 backdrop-blur-sm"
            onFocus={() => setShowSearchResults(true)}
          />
          
          {/* Search Results */}
          {showSearchResults && searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-md shadow-lg border z-30 max-h-60 overflow-y-auto">
              {searchResults.map((result) => (
                <button
                  key={result.place_id}
                  onClick={() => handleSearchResultClick(result)}
                  className="w-full px-4 py-2 text-right hover:bg-gray-50 border-b last:border-b-0"
                >
                  {result.formatted_address}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Layer Controls */}
      <div className="absolute top-4 right-4 z-20">
        <Popover open={showLayerControls} onOpenChange={setShowLayerControls}>
          <PopoverTrigger asChild>
            <Button variant="outline" size="sm" className="bg-white/90 backdrop-blur-sm">
              <Layers className="h-4 w-4 mr-2" />
              שכבות
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80 bg-white text-gray-900 border border-gray-200" align="end">
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
      <div className="absolute bottom-4 left-4 z-20">
        <div className="bg-white/90 backdrop-blur-sm rounded-md px-3 py-2 text-sm">
          <span className="font-medium">{assets.length}</span> נכסים
        </div>
      </div>

      {/* Map Container */}
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  )
}
