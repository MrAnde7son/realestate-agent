import { NextRequest, NextResponse } from 'next/server'

export async function GET(
  _request: NextRequest,
  { params }: { params: { id: string } }
) {
  const id = Number(params.id)
  const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
  const permitsEndpoint = `${backendUrl}/api/assets/${id}/permits/`

  try {
    const resp = await fetch(permitsEndpoint, { cache: 'no-store' })
    if (!resp.ok) {
      return NextResponse.json({ error: 'Failed to fetch permits', status: resp.status, permits: [] }, { status: 200 })
    }
    const data = await resp.json()
    return NextResponse.json(data)
  } catch (e) {
    return NextResponse.json({ error: 'Network error', permits: [] }, { status: 200 })
  }
}
