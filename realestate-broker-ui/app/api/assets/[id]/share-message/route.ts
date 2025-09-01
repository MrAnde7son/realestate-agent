import { NextRequest, NextResponse } from 'next/server'

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params
  try {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    console.log('Share message request for asset:', id, 'Backend URL:', backendUrl)
    
    let language: string | undefined
    try {
      const body = await request.json()
      language = body.language
    } catch {
      // ignore missing body
    }
    
    const response = await fetch(`${backendUrl}/api/assets/${id}/share-message/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ language }),
    })
    
    // Check if response is OK
    if (!response.ok) {
      console.error('Backend error:', response.status, response.statusText)
      const errorText = await response.text()
      console.error('Backend error response:', errorText)
      return NextResponse.json(
        { error: `Backend error: ${response.status} ${response.statusText}` },
        { status: response.status }
      )
    }
    
    // Check content type to ensure we're getting JSON
    const contentType = response.headers.get('content-type')
    if (!contentType || !contentType.includes('application/json')) {
      const responseText = await response.text()
      console.error('Backend returned non-JSON response:', contentType, responseText.substring(0, 200))
      return NextResponse.json(
        { error: 'Backend returned non-JSON response' },
        { status: 500 }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('Error generating share message:', error)
    return NextResponse.json(
      { error: 'Failed to generate message', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}
