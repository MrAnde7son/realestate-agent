import { NextRequest, NextResponse } from 'next/server'
import { rightsByAsset } from '@/lib/data'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params
  const numericId = Number(id)

  try {
    // Try the new permits endpoint first
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
    console.log(`Fetching permits from: ${backendUrl}/api/assets/${numericId}/permits/`)
    const resp = await fetch(`${backendUrl}/api/assets/${numericId}/permits/`)
    console.log(`Response status: ${resp.status}`)
    if (resp.ok) {
      const data = await resp.json()
      console.log(`Response data:`, data)
      const permits = data.permits || []
      console.log(`Permits found: ${permits.length}`)
      if (permits.length > 0) {
        return NextResponse.json({ permits })
      }
    } else {
      console.log(`Backend response not ok: ${resp.status} ${resp.statusText}`)
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
