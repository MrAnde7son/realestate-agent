import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    
    // Extract the WMS parameters from the query string
    const service = searchParams.get('SERVICE')
    const requestType = searchParams.get('REQUEST')
    const version = searchParams.get('VERSION')
    const layers = searchParams.get('LAYERS')
    const crs = searchParams.get('CRS')
    const bbox = searchParams.get('BBOX')
    const width = searchParams.get('WIDTH')
    const height = searchParams.get('HEIGHT')
    const styles = searchParams.get('STYLES')
    const format = searchParams.get('FORMAT')
    const transparent = searchParams.get('TRANSPARENT')

    // Validate required parameters
    if (!service || !requestType || !version || !layers || !crs || !bbox || !width || !height || !format) {
      return NextResponse.json(
        { error: 'Missing required WMS parameters' },
        { status: 400 }
      )
    }

    // Build the target WMS URL
    const targetUrl = new URL('https://open.govmap.gov.il/geoserver/opendata/wms')
    targetUrl.searchParams.set('SERVICE', service)
    targetUrl.searchParams.set('REQUEST', requestType)
    targetUrl.searchParams.set('VERSION', version)
    targetUrl.searchParams.set('LAYERS', layers)
    targetUrl.searchParams.set('CRS', crs)
    targetUrl.searchParams.set('BBOX', bbox)
    targetUrl.searchParams.set('WIDTH', width)
    targetUrl.searchParams.set('HEIGHT', height)
    if (styles) targetUrl.searchParams.set('STYLES', styles)
    targetUrl.searchParams.set('FORMAT', format)
    if (transparent) targetUrl.searchParams.set('TRANSPARENT', transparent)

    // Make the request to the WMS server
    const response = await fetch(targetUrl.toString(), {
      method: 'GET',
      headers: {
        'User-Agent': 'RealEstateAgent/1.0',
      },
    })

    if (!response.ok) {
      console.error(`WMS request failed: ${response.status} ${response.statusText}`)
      return NextResponse.json(
        { error: 'WMS request failed' },
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
    console.error('WMS proxy error:', error)
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
