import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateToken } from '@/lib/token-utils'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(request: NextRequest) {
  try {
    // Get authentication token
    let token = cookies().get('access_token')?.value
    
    // If no token in cookies, try to get from request headers
    if (!token) {
      const authHeader = request.headers.get('authorization')
      if (authHeader && authHeader.startsWith('Bearer ')) {
        token = authHeader.substring(7)
      }
    }
    
    // Validate token
    const tokenValidation = validateToken(token)
    if (!tokenValidation.isValid) {
      console.log('❌ Documents by category API - Token validation failed:', tokenValidation.error)
      return NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 })
    }

    const { searchParams } = new URL(request.url)
    
    // Forward the request to Django backend
    const backendUrl = `${BACKEND_URL}/api/documents/by_category/?${searchParams.toString()}`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch documents' },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
    
  } catch (error) {
    console.error('Documents by category API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
