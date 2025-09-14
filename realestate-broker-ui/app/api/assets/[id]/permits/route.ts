import { NextRequest, NextResponse } from 'next/server'
import { rightsByAsset } from '@/lib/data'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params
  const numericId = Number(id)

  try {
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
    const resp = await fetch(`${backendUrl}/api/permits/?asset=${numericId}`)
    if (resp.ok) {
      const data = await resp.json()
      const permits = Array.isArray(data) ? data : data.results || data.rows || []
      return NextResponse.json({ permits })
    }
  } catch (err) {
    console.error('Error fetching permits from backend:', err)
  }

  const fallback = rightsByAsset(numericId).permits.map((desc, idx) => ({
    id: idx + 1,
    description: desc,
  }))
  return NextResponse.json({ permits: fallback })
}
