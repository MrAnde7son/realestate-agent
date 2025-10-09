import { NextRequest, NextResponse } from 'next/server'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params
  const numericId = Number(id)
  const backendUrl = `${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/api/assets/${numericId}/transactions/`

  try {
    // Fetch from backend with cache-busting to ensure fresh data
    const backendResponse = await fetch(backendUrl, {
      cache: 'no-store',
      headers: {
        'Cache-Control': 'no-cache'
      }
    });

    if (backendResponse.ok) {
      const data = await backendResponse.json()
      return NextResponse.json(data);
    }

    // If backend returns an error status, return that error
    return NextResponse.json(
      { error: 'Failed to fetch transaction data' },
      { status: backendResponse.status }
    )
  } catch (error) {
    console.error('Error fetching transactions from backend:', error)
    return NextResponse.json(
      { error: 'Backend service unavailable' },
      { status: 503 }
    )
  }
}
