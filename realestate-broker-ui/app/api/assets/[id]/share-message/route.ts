import { NextRequest, NextResponse } from 'next/server'

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params
  try {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    let language: string | undefined
    try {
      const body = await request.json()
      language = body.language
    } catch {
      // ignore missing body
    }
    const res = await fetch(`${backendUrl}/api/assets/${id}/share-message/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ language }),
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (error) {
    console.error('Error generating share message:', error)
    return NextResponse.json(
      { error: 'Failed to generate message' },
      { status: 500 }
    )
  }
}
