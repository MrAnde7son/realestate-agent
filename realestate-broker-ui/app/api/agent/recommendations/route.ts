import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateToken } from '@/lib/token-utils'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(req: Request) {  
  try {
    const cookieStore = await cookies()
    const token = cookieStore.get('access_token')?.value
    
    // Validate token
    const tokenValidation = validateToken(token)
    if (!tokenValidation.isValid) {
      return NextResponse.json(
        { error: 'Unauthorized - Token expired or invalid' },
        { status: 401 }
      )
    }
    
    // Option 1: Fetch from backend API if available
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
      } else {
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

