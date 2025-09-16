import { NextRequest, NextResponse } from 'next/server'

// Supported tile services configuration
const TILE_SERVICES = {
  'jerusalem-ortho': {
    baseUrl: 'https://gisviewer.jerusalem.muni.il/arcgis/rest/services/Ortho062025/MapServer/tile',
    fallbackUrl: 'https://tile.openstreetmap.org' // Use OSM as fallback
  },
  'telaviv-ortho': {
    baseUrl: 'https://gisn.tel-aviv.gov.il/arcgis/rest/services/WM/IView2Ortho2011WM/MapServer/tile',
    fallbackUrl: 'https://tile.openstreetmap.org' // Use OSM as fallback
  },
  'haifa-ortho': {
    baseUrl: 'https://gisserver.haifa.muni.il/arcgiswebadaptor/rest/services/Basemaps/Basemaps_Orthophoto_July_2023/MapServer/tile',
    fallbackUrl: 'https://tile.openstreetmap.org' // Use OSM as fallback
  }
} as const

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    
    // Extract tile parameters
    const service = searchParams.get('service')
    const z = searchParams.get('z')
    const x = searchParams.get('x')
    const y = searchParams.get('y')
    const fallback = searchParams.get('fallback') === 'true'

    // Validate required parameters
    if (!service || z === null || x === null || y === null) {
      return NextResponse.json(
        { error: 'Missing required tile parameters: service, z, x, y' },
        { status: 400 }
      )
    }

    // Validate service
    if (!(service in TILE_SERVICES)) {
      return NextResponse.json(
        { error: `Unsupported tile service: ${service}` },
        { status: 400 }
      )
    }

    const serviceConfig = TILE_SERVICES[service as keyof typeof TILE_SERVICES]
    const targetUrl = fallback ? serviceConfig.fallbackUrl : serviceConfig.baseUrl
    const fullUrl = `${targetUrl}/${z}/${y}/${x}`

    // Make the request to the tile server
    const response = await fetch(fullUrl, {
      method: 'GET',
      headers: {
        'User-Agent': 'RealEstateAgent/1.0',
        'Accept': 'image/png,image/jpeg,image/webp,*/*',
      },
    })

    if (!response.ok) {
      // If primary service fails and we haven't tried fallback, try fallback
      if (!fallback && response.status >= 400) {
        console.warn(`Primary tile service failed for ${service}, trying fallback...`)
        const fallbackUrl = `${request.url}${request.url.includes('?') ? '&' : '?'}fallback=true`
        return NextResponse.redirect(fallbackUrl)
      }

      console.error(`Tile request failed: ${response.status} ${response.statusText} for ${fullUrl}`)
      return NextResponse.json(
        { error: 'Tile request failed' },
        { status: response.status }
      )
    }

    // Get the image data
    const imageBuffer = await response.arrayBuffer()
    
    // Return the image with appropriate headers
    return new NextResponse(imageBuffer, {
      status: 200,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'image/png',
        'Cache-Control': 'public, max-age=86400', // Cache for 24 hours
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'X-Tile-Source': fallback ? 'fallback' : 'primary',
      },
    })

  } catch (error) {
    console.error('Tile proxy error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

// Handle preflight requests
export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  })
}
