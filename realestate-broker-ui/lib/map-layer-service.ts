import layersConfig from './map-layers-config.json'

export interface LayerConfig {
  id: string
  label: string
  type: 'wmts' | 'wms' | 'geojson' | 'vector'
  urlTemplate?: string
  getMapUrl?: string
  opacity: number
  minzoom: number
  maxzoom: number
  visible: boolean
  style?: any
  source?: any
}

export interface MapLayer {
  id: string
  source: any
  layer: any
  opacity: number
  visible: boolean
}

export class MapLayerService {
  private map: any
  private layers: Map<string, MapLayer> = new Map()
  private layerVisibility: Record<string, boolean> = {}
  private layerOpacity: Record<string, number> = {}

  constructor(map: any) {
    this.map = map
    this.initializeLayers()
  }

  private initializeLayers() {
    layersConfig.forEach((config: any) => {
      this.layerVisibility[config.id] = config.visible
      this.layerOpacity[config.id] = config.opacity
    })
  }

  async addLayer(config: LayerConfig): Promise<void> {
    if (!this.map) return

    try {
      const sourceId = `${config.id}-source`
      const layerId = `${config.id}-layer`

      // Remove existing layer if it exists
      if (this.map.getLayer(layerId)) {
        this.map.removeLayer(layerId)
      }
      if (this.map.getSource(sourceId)) {
        this.map.removeSource(sourceId)
      }

      let source: any = {}

      switch (config.type) {
        case 'wmts':
          source = {
            type: 'raster',
            tiles: [config.urlTemplate!],
            tileSize: 256,
            attribution: `© ${config.label}`,
            scheme: 'xyz',
            minzoom: config.minzoom,
            maxzoom: config.maxzoom
          }
          break

        case 'wms':
          // For WMS layers, we need to use a different approach
          // MapLibre doesn't directly support WMS, so we'll use a tile service approach
          const wmsUrl = this.buildWMSUrl(config)
          source = {
            type: 'raster',
            tiles: [wmsUrl],
            tileSize: 256,
            attribution: `© ${config.label}`,
            scheme: 'xyz',
            minzoom: config.minzoom,
            maxzoom: config.maxzoom
          }
          break

        case 'geojson':
          // For GeoJSON layers, we'll need to fetch the data
          // Replace bbox placeholder with actual map bounds
          const bounds = this.map.getBounds()
          const bbox4326 = `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`
          const geojsonUrl = config.urlTemplate!.replace('{bbox-epsg-4326}', bbox4326)
          
          const response = await fetch(geojsonUrl)
          if (!response.ok) {
            throw new Error(`Failed to fetch GeoJSON: ${response.status} ${response.statusText}`)
          }
          const geojson = await response.json()
          source = {
            type: 'geojson',
            data: geojson
          }
          break

        case 'vector':
          source = {
            type: 'vector',
            tiles: [config.urlTemplate!],
            minzoom: config.minzoom,
            maxzoom: config.maxzoom
          }
          break
      }

      // Add source with error handling
      try {
        this.map.addSource(sourceId, source)
      } catch (sourceError) {
        console.warn(`Failed to add source ${sourceId}:`, sourceError)
        throw sourceError
      }

      // Add layer
      let layer: any = {}

      if (config.type === 'wmts' || config.type === 'wms') {
        layer = {
          id: layerId,
          type: 'raster',
          source: sourceId,
          paint: {
            'raster-opacity': config.opacity
          },
          layout: {
            visibility: config.visible ? 'visible' : 'none'
          }
        }
      } else if (config.type === 'geojson') {
        layer = {
          id: layerId,
          type: 'fill',
          source: sourceId,
          paint: {
            'fill-color': '#0080ff',
            'fill-opacity': config.opacity
          },
          layout: {
            visibility: config.visible ? 'visible' : 'none'
          }
        }
      } else if (config.type === 'vector') {
        layer = {
          id: layerId,
          type: 'fill',
          source: sourceId,
          'source-layer': config.id,
          paint: {
            'fill-color': '#0080ff',
            'fill-opacity': config.opacity
          },
          layout: {
            visibility: config.visible ? 'visible' : 'none'
          }
        }
      }

      try {
        this.map.addLayer(layer)

        // Store layer reference
        this.layers.set(config.id, {
          id: config.id,
          source: this.map.getSource(sourceId),
          layer: this.map.getLayer(layerId),
          opacity: config.opacity,
          visible: config.visible
        })

        // Add error event listener for tile loading failures
        this.map.on('error', (e: any) => {
          if (e.sourceId === sourceId) {
            console.warn(`Tile loading error for layer ${config.id}:`, e.error)
          }
        })

      } catch (layerError) {
        console.warn(`Failed to add layer ${config.id}:`, layerError)
        // Clean up the source if layer creation fails
        try {
          this.map.removeSource(sourceId)
        } catch (cleanupError) {
          console.warn(`Failed to cleanup source ${sourceId}:`, cleanupError)
        }
        throw layerError // Re-throw to be caught by outer catch
      }

    } catch (error) {
      console.error(`Error adding layer ${config.id}:`, error)
      // Don't throw the error to prevent breaking other layers
    }
  }

  private buildWMSUrl(config: LayerConfig): string {
    if (!config.getMapUrl) return ''
    
    // Replace the external WMS URL with our proxy
    const originalUrl = config.getMapUrl
    const proxyUrl = originalUrl.replace(
      'https://open.govmap.gov.il/geoserver/opendata/wms',
      '/api/wms-proxy'
    )
    
    // Convert WMS GetMap URL to a tile URL template that MapLibre can use
    // MapLibre will replace {bbox-epsg-3857} with actual bbox values
    return proxyUrl
  }

  toggleLayer(layerId: string): void {
    if (!this.map) return

    const layer = this.layers.get(layerId)
    if (!layer) return

    const newVisibility = !this.layerVisibility[layerId]
    this.layerVisibility[layerId] = newVisibility

    if (newVisibility) {
      this.map.setLayoutProperty(`${layerId}-layer`, 'visibility', 'visible')
    } else {
      this.map.setLayoutProperty(`${layerId}-layer`, 'visibility', 'none')
    }

    // Update layer reference
    this.layers.set(layerId, {
      ...layer,
      visible: newVisibility
    })
  }

  setLayerOpacity(layerId: string, opacity: number): void {
    if (!this.map) return

    const layer = this.layers.get(layerId)
    if (!layer) return

    this.layerOpacity[layerId] = opacity

    // Update layer opacity
    const layerType = this.map.getLayer(`${layerId}-layer`)?.type
    if (layerType === 'raster') {
      this.map.setPaintProperty(`${layerId}-layer`, 'raster-opacity', opacity)
    } else if (layerType === 'fill') {
      this.map.setPaintProperty(`${layerId}-layer`, 'fill-opacity', opacity)
    }

    // Update layer reference
    this.layers.set(layerId, {
      ...layer,
      opacity
    })
  }

  getLayerVisibility(layerId: string): boolean {
    return this.layerVisibility[layerId] || false
  }

  getLayerOpacity(layerId: string): number {
    return this.layerOpacity[layerId] || 1
  }

  getAllLayers(): LayerConfig[] {
    return layersConfig as LayerConfig[]
  }

  async loadAllLayers(): Promise<void> {
    const promises = layersConfig.map(async (config: any) => {
      try {
        await this.addLayer(config as LayerConfig)
      } catch (error) {
        console.warn(`Failed to load layer ${config.id}:`, error)
        
        // Try to load fallback layer for orthophoto services
        if (config.id.includes('ortho') && !config.id.includes('openstreetmap')) {
          try {
            const fallbackConfig = {
              ...config,
              id: 'openstreetmap',
              label: 'OpenStreetMap (Fallback)',
              urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
              opacity: 0.6,
              minzoom: 0,
              maxzoom: 19
            }
            console.log(`Loading fallback layer for ${config.id}`)
            await this.addLayer(fallbackConfig as LayerConfig)
          } catch (fallbackError) {
            console.warn(`Failed to load fallback layer for ${config.id}:`, fallbackError)
          }
        }
      }
    })
    await Promise.allSettled(promises)
  }

  destroy(): void {
    if (!this.map) return

    // Remove all layers
    this.layers.forEach((layer, layerId) => {
      if (this.map.getLayer(`${layerId}-layer`)) {
        this.map.removeLayer(`${layerId}-layer`)
      }
      if (this.map.getSource(`${layerId}-source`)) {
        this.map.removeSource(`${layerId}-source`)
      }
    })

    this.layers.clear()
  }
}

// Utility function to get layer configuration
export function getLayerConfig(layerId: string): LayerConfig | undefined {
  return layersConfig.find((config: any) => config.id === layerId) as LayerConfig | undefined
}

// Utility function to get all available layers
export function getAllLayerConfigs(): LayerConfig[] {
  return layersConfig as LayerConfig[]
}
