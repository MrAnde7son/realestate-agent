import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(request: NextRequest) {
  try {
    // Forward the request to Django backend
    const response = await fetch(`${BACKEND_URL}/api/dashboard/market-data/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store', // Disable caching
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch market data' },
        { status: response.status }
      )
    }

    const data = await response.json()
    console.log('Dashboard market data from Django:', JSON.stringify(data, null, 2))
    return NextResponse.json(data)
  } catch (error) {
    console.error('Dashboard market data API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
