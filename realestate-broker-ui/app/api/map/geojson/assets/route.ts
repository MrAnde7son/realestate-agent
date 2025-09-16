import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const bbox = searchParams.get('bbox')
    
    if (!bbox) {
      return NextResponse.json(
        { error: 'bbox parameter is required' },
        { status: 400 }
      )
    }

    // Parse bbox (format: minLon,minLat,maxLon,maxLat)
    const [minLon, minLat, maxLon, maxLat] = bbox.split(',').map(Number)
    
    if (isNaN(minLon) || isNaN(minLat) || isNaN(maxLon) || isNaN(maxLat)) {
      return NextResponse.json(
        { error: 'Invalid bbox format. Expected: minLon,minLat,maxLon,maxLat' },
        { status: 400 }
      )
    }

    // For now, return an empty GeoJSON feature collection
    // In a real implementation, you would query your database for assets within the bbox
    const geojson = {
      type: 'FeatureCollection',
      features: []
    }

    return NextResponse.json(geojson, {
      headers: {
        'Cache-Control': 'public, max-age=300', // Cache for 5 minutes
        'Access-Control-Allow-Origin': '*',
      },
    })

  } catch (error) {
    console.error('GeoJSON API error:', error)
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
