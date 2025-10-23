import { NextResponse } from 'next/server'

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: rawId } = await params
  const id = Number(rawId)
  const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
  const baseUrl = `${backendUrl}/api/assets/${id}/permits`
  const searchParams = new URL(request.url).searchParams.toString()
  const permitsEndpoint = searchParams ? `${baseUrl}?${searchParams}` : baseUrl

  try {
    const headers: HeadersInit = {
      'Cache-Control': 'no-cache',
    }
    const authHeader = request.headers.get('authorization')
    if (authHeader) {
      headers['Authorization'] = authHeader
    }

    const resp = await fetch(permitsEndpoint, {
      cache: 'no-store',
      headers,
    })
    if (!resp.ok) {
      return NextResponse.json({ error: 'Failed to fetch permits', status: resp.status, permits: [] }, { status: 200 })
    }
    const data = await resp.json()
    return NextResponse.json(data)
  } catch (e) {
    return NextResponse.json({ error: 'Network error', permits: [] }, { status: 200 })
  }
}
