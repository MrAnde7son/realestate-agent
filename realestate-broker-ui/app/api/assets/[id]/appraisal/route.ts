import { NextRequest, NextResponse } from 'next/server'
import { appraisalByAsset, compsByAsset } from '@/lib/data'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params
  const numericId = Number(id)

  try {
    // Try to fetch from backend first
    const backendResponse = await fetch(
      `${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/api/assets/${numericId}/appraisal/`
    )

    if (backendResponse.ok) {
      const data = await backendResponse.json()
      return NextResponse.json(data)
    }
  } catch (error) {
    console.error('Error fetching appraisal from backend:', error)
  }

  // Fallback to mock data
  return NextResponse.json({
    appraisal: appraisalByAsset(numericId),
    comps: compsByAsset(numericId)
  })
}
