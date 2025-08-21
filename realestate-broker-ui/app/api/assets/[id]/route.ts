import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: assetId } = await params
    
    if (!assetId) {
      return NextResponse.json({ 
        error: 'Asset ID is required' 
      }, { status: 400 })
    }
    
    // Proxy to Django backend
    const response = await fetch(`${BACKEND_URL}/api/assets/${assetId}/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      return NextResponse.json(errorData, { status: response.status })
    }
    
    const data = await response.json()
    return NextResponse.json(data)
    
  } catch (error) {
    console.error('Error fetching asset:', error)
    return NextResponse.json({ 
      error: 'Failed to fetch asset',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}
