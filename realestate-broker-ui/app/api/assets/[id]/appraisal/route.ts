import { NextRequest, NextResponse } from 'next/server'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params
  const numericId = Number(id)

  try {
    // Fetch from backend
    const backendResponse = await fetch(
      `${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/api/assets/${numericId}/appraisal/`
    )

    if (backendResponse.ok) {
      const data = await backendResponse.json()
      return NextResponse.json(data)
    }

    // If backend returns an error status, return that error
    return NextResponse.json(
      { error: 'Failed to fetch appraisal data' },
      { status: backendResponse.status }
    )
  } catch (error) {
    console.error('Error fetching appraisal from backend:', error)
    return NextResponse.json(
      { error: 'Backend service unavailable' },
      { status: 503 }
    )
  }
}
