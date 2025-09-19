import { NextRequest, NextResponse } from 'next/server'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params

  try {
    // Fetch from backend
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
    console.log('Fetching plans from:', `${backendUrl}/api/assets/${id}/plans/`)
    const backendResponse = await fetch(`${backendUrl}/api/assets/${id}/plans/`)

    if (backendResponse.ok) {
      const data = await backendResponse.json()
      return NextResponse.json(data)
    } else {
      console.error('Backend error:', backendResponse.status, backendResponse.statusText)
      return new NextResponse('Backend error', { status: backendResponse.status })
    }
  } catch (error) {
    console.error('Error fetching plans from backend:', error)
    return new NextResponse('Internal Server Error', { status: 500 })
  }
}
