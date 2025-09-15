# Map View Documentation

## Overview

The Map View provides an interactive map interface for viewing and analyzing real estate assets with integrated government and municipal data layers.

## Features

### Base Map
- **MapLibre GL**: Open-source vector map rendering
- **OpenStreetMap**: Free base map tiles
- **Responsive Design**: Adapts to different screen sizes

### Layer Management
- **Dynamic Layers**: Toggle visibility and opacity of different data layers
- **Government Data**: Integration with govmap.gov.il and municipal data
- **Layer Types**: Support for WMTS, WMS, GeoJSON, and Vector tiles

### Search & Geocoding
- **Google Places API**: Location search with autocomplete
- **Mock Service**: Fallback for development without API key
- **Address Geocoding**: Convert addresses to coordinates
- **Reverse Geocoding**: Get address from coordinates

### Drawing & Measurement Tools
- **Polygon Drawing**: Draw areas of interest
- **Line Drawing**: Measure distances
- **Point Marking**: Mark specific locations
- **Area Calculation**: Automatic area measurement
- **Distance Measurement**: Line length calculation

### Asset Visualization
- **Asset Markers**: Visual representation of properties
- **Interactive Markers**: Click to view asset details
- **Hover Effects**: Enhanced user experience
- **Asset Count**: Display total number of assets

## Architecture

### Components

#### MapView.tsx
Main map component that orchestrates all map functionality.

#### MapLayerService
Service class for managing map layers:
- Layer configuration management
- Dynamic layer loading
- Visibility and opacity controls
- Layer cleanup

#### GeocodingService
Service for location search and geocoding:
- Google Places API integration
- Mock service for development
- Address geocoding
- Reverse geocoding

### Configuration

#### Layer Configuration (map-layers-config.json)
```json
[
  {
    "id": "parcels",
    "label": "חלקות",
    "type": "wmts",
    "urlTemplate": "https://govmap.gov.il/...",
    "opacity": 0.7,
    "minzoom": 12,
    "maxzoom": 22,
    "visible": false
  }
]
```

#### Environment Variables
- `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`: Google Maps API key for geocoding

## Usage

### Basic Implementation
```tsx
import MapView from '@/components/MapView'

<MapView
  assets={filteredAssets}
  center={[34.7818, 32.0853]}
  zoom={12}
  onAssetClick={(asset) => router.push(`/assets/${asset.id}`)}
  searchValue={search}
  onSearchChange={setSearch}
  height="600px"
/>
```

### Layer Management
```tsx
// Toggle layer visibility
layerService.current?.toggleLayer('parcels')

// Set layer opacity
layerService.current?.setLayerOpacity('parcels', 0.5)
```

### Geocoding
```tsx
// Search for places
const results = await geocodingService.current.searchPlaces('תל אביב')

// Geocode address
const result = await geocodingService.current.geocodeAddress('רחוב הרצל 1, תל אביב')
```

## Dependencies

### Core Dependencies
- `maplibre-gl`: Map rendering engine
- `@mapbox/mapbox-gl-draw`: Drawing tools
- `@radix-ui/react-slider`: Opacity controls
- `@radix-ui/react-popover`: Layer controls

### Development Dependencies
- `@radix-ui/react-slider`: Slider component
- `@radix-ui/react-popover`: Popover component

## Performance Considerations

### Layer Loading
- Layers are loaded asynchronously
- Only visible layers are rendered
- Opacity changes are optimized

### Search Performance
- Debounced search input
- Mock service for development
- Caching of search results

### Memory Management
- Proper cleanup of map instances
- Layer service destruction
- Event listener cleanup

## Future Enhancements

### Planned Features
- **Clustering**: Group nearby assets
- **Heatmaps**: Density visualization
- **3D Buildings**: Enhanced visualization
- **Custom Styles**: Themed map styles
- **Export Functionality**: Save map images
- **Print Support**: Print-friendly layouts

### Integration Opportunities
- **Real-time Data**: Live updates
- **Analytics**: Usage tracking
- **Collaboration**: Shared map sessions
- **Mobile Optimization**: Touch gestures

## Troubleshooting

### Common Issues

#### Map Not Loading
- Check MapLibre GL dependencies
- Verify container dimensions
- Check console for errors

#### Search Not Working
- Verify Google Maps API key
- Check network connectivity
- Review API quotas

#### Layers Not Displaying
- Check layer configuration
- Verify data sources
- Review zoom levels

### Debug Mode
Enable debug logging by setting:
```javascript
localStorage.setItem('map-debug', 'true')
```

## Contributing

### Adding New Layers
1. Update `map-layers-config.json`
2. Add layer type support in `MapLayerService`
3. Test layer loading and visibility

### Adding New Search Providers
1. Extend `GeocodingService` interface
2. Implement provider-specific methods
3. Add configuration options

### Custom Drawing Tools
1. Extend Mapbox Draw configuration
2. Add custom event handlers
3. Implement measurement calculations
