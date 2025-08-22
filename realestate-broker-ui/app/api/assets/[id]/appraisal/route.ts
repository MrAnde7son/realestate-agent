import { NextRequest, NextResponse } from 'next/server'
import { appraisalByAsset } from '@/lib/data'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params

  try {
    // Try to fetch from backend first
    const backendResponse = await fetch(`${process.env.BACKEND_URL || 'http://localhost:8000'}/api/assets/${id}/appraisal/`)
    
    if (backendResponse.ok) {
      const data = await backendResponse.json()
      return NextResponse.json(data)
    }
  } catch (error) {
    console.error('Error fetching appraisal from backend:', error)
  }

  // Fallback to mock data
  return NextResponse.json(appraisalByAsset(id))
}
