import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateToken } from '@/lib/token-utils'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const assetId = params.id
    const cookieStore = await cookies()
    let token = cookieStore.get('access_token')?.value

    if (!token) {
      const authHeader = request.headers.get('authorization')
      if (authHeader && authHeader.startsWith('Bearer ')) {
        token = authHeader.substring(7)
      }
    }
    
    console.log('🔍 Listings API - Request received:', {
      assetId,
      hasToken: !!token,
      backendUrl: BACKEND_URL
    })
    
    // Validate token
    const tokenValidation = validateToken(token)
    if (!tokenValidation.isValid) {
      console.log('❌ Listings API - Token validation failed:', tokenValidation.error)
      return NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 })
    }

    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()

    // Make request to Django backend
    const backendUrl = `${BACKEND_URL}/api/assets/${assetId}/listings/${queryString ? `?${queryString}` : ''}`
    
    console.log('🔍 Listings API - Backend request:', {
      backendUrl,
      query: queryString,
      assetId,
      hasToken: !!token
    })
    
    const response = await fetch(backendUrl, {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      cache: 'no-store',
    })
    
    console.log('🔍 Listings API - Backend response:', {
      url: backendUrl,
      status: response.status,
      statusText: response.statusText,
      ok: response.ok
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      console.error('❌ Listings API - Backend error:', errorData)
      return NextResponse.json(
        { error: errorData.error || `Backend error: ${response.status}` },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
    
  } catch (error) {
    console.error('❌ Listings API - Error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
