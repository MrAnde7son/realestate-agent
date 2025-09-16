import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    
    // Extract tile parameters
    const z = searchParams.get('z')
    const x = searchParams.get('x')
    const y = searchParams.get('y')
    const layer = searchParams.get('layer')

    // Validate required parameters
    if (!z || !x || !y || !layer) {
      return NextResponse.json(
        { error: 'Missing required tile parameters: z, x, y, layer' },
        { status: 400 }
      )
    }

    // Convert tile coordinates to bbox (Web Mercator)
    const tileSize = 256
    const zoom = parseInt(z)
    const tileX = parseInt(x)
    const tileY = parseInt(y)

    // Calculate bbox for the tile
    const n = Math.pow(2, zoom)
    const lonMin = (tileX / n) * 360 - 180
    const lonMax = ((tileX + 1) / n) * 360 - 180
    const latMin = Math.atan(Math.sinh(Math.PI * (1 - 2 * (tileY + 1) / n))) * 180 / Math.PI
    const latMax = Math.atan(Math.sinh(Math.PI * (1 - 2 * tileY / n))) * 180 / Math.PI

    // Convert to Web Mercator (EPSG:3857)
    const bbox3857 = `${lonMin * 20037508.34 / 180},${latMin * 20037508.34 / 180},${lonMax * 20037508.34 / 180},${latMax * 20037508.34 / 180}`

    // Build WMS request URL
    const wmsUrl = new URL('https://open.govmap.gov.il/geoserver/opendata/wms')
    wmsUrl.searchParams.set('SERVICE', 'WMS')
    wmsUrl.searchParams.set('REQUEST', 'GetMap')
    wmsUrl.searchParams.set('VERSION', '1.3.0')
    wmsUrl.searchParams.set('LAYERS', layer)
    wmsUrl.searchParams.set('CRS', 'EPSG:3857')
    wmsUrl.searchParams.set('BBOX', bbox3857)
    wmsUrl.searchParams.set('WIDTH', tileSize.toString())
    wmsUrl.searchParams.set('HEIGHT', tileSize.toString())
    wmsUrl.searchParams.set('STYLES', '')
    wmsUrl.searchParams.set('FORMAT', 'image/png')
    wmsUrl.searchParams.set('TRANSPARENT', 'true')

    // Make the request to the WMS server
    const response = await fetch(wmsUrl.toString(), {
      method: 'GET',
      headers: {
        'User-Agent': 'RealEstateAgent/1.0',
      },
    })

    if (!response.ok) {
      console.error(`WMS tile request failed: ${response.status} ${response.statusText}`)
      return NextResponse.json(
        { error: 'WMS tile request failed' },
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
        'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    })

  } catch (error) {
    console.error('WMS tile proxy error:', error)
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
