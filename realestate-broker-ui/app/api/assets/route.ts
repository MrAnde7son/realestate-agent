import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function POST(req: Request) {
  try {
    const body = await req.json()
    
    // Validate required fields
    const { scope } = body
    if (!scope || !scope.type) {
      return NextResponse.json({ 
        error: 'Scope type is required' 
      }, { status: 400 })
    }
    
    // Proxy to Django backend
    const response = await fetch(`${BACKEND_URL}/api/assets/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      return NextResponse.json(errorData, { status: response.status })
    }
    
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
    
  } catch (error) {
    console.error('Error creating asset:', error)
    return NextResponse.json({ 
      error: 'Failed to create asset',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}
