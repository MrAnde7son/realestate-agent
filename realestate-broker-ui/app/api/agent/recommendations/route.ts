import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(req: Request) {  
  try {
    // Get tokens from cookies or Authorization header
    const cookieStore = await cookies()
    let token = cookieStore.get('access_token')?.value
    const refreshToken = cookieStore.get('refresh_token')?.value
    
    // Also check Authorization header for API tokens
    if (!token) {
      const authHeader = req.headers.get('authorization')
      if (authHeader && authHeader.startsWith('Bearer ')) {
        token = authHeader.substring(7)
      }
    }
    
    // If no tokens at all, return JSON error (let backend handle auth if tokens exist)
    if (!token && !refreshToken) {
      return NextResponse.json(
        { error: 'Unauthorized', recommendations: [] },
        { status: 401 }
      )
    }
    
    // For proxy routes, we forward requests with tokens to the backend
    // The backend will handle token validation and refresh if needed
    
    // Fetch from backend API if available
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers.Authorization = `Bearer ${token}`
      }
      
      const res = await fetch(`${BACKEND_URL}/api/agent/recommendations`, {
        method: 'GET',
        headers
      })
      
      
      if (res.ok) {
        const data = await res.json()
        console.log('Backend recommendations received:', data)
        return NextResponse.json(data)
      } else if (res.status === 401) {
        // Backend authentication failed - return 401 so frontend can handle token refresh
        const errorData = await res.json().catch(() => ({}))
        return NextResponse.json(
          { error: 'Unauthorized', recommendations: [] },
          { status: 401 }
        )
      } else {
        // Other backend errors - log and fall back to defaults
        const errorText = await res.text()
        console.log(`Backend returned ${res.status}, falling back to defaults:`, errorText)
      }
    } catch (error) {
      console.log('Backend recommendations endpoint not available, using defaults:', error)
    }
  
    
    return NextResponse.json({
      recommendations: []
    })
  }
  catch (error) {
    console.error('Error in recommendations API:', error)
    return NextResponse.json({
      recommendations: []
    })
  }
}

