import { NextResponse } from 'next/server'

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const numericId = Number(id)

  try {
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
    console.log(`Fetching rights from: ${backendUrl}/api/assets/${numericId}/rights/`)
    const backendResponse = await fetch(`${backendUrl}/api/assets/${numericId}/rights/`, {
      cache: 'no-store',
      headers: {
        'Cache-Control': 'no-cache'
      }
    })
    console.log(`Rights backend status: ${backendResponse.status}`)
    if (backendResponse.ok) {
      const data = await backendResponse.json()
      return NextResponse.json(data)
    } else {
      console.warn(`Backend rights fetch failed: ${backendResponse.status} ${backendResponse.statusText}`)
    }
  } catch (error) {
    console.error('Error fetching rights from backend:', error)
  }

  // No fallback: return empty object
  return NextResponse.json({})
}
