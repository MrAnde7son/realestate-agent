import { NextResponse } from 'next/server'

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params

  try {
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
    const baseUrl = `${backendUrl}/api/assets/${id}/plans`
    const searchParams = new URL(request.url).searchParams.toString()
    const url = searchParams ? `${baseUrl}?${searchParams}` : baseUrl

    const headers: HeadersInit = {
      'Cache-Control': 'no-cache',
    }
    const authHeader = request.headers.get('authorization')
    if (authHeader) {
      headers['Authorization'] = authHeader
    }

    const backendResponse = await fetch(url, {
      cache: 'no-store',
      headers,
    })

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
