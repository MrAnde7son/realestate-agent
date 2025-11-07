import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateToken } from '@/lib/token-utils'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

/**
 * GET /api/agent/recommendations
 * 
 * Fetches recommended questions for the AI chat interface.
 * Can be customized to return dynamic recommendations based on user context,
 * recent activity, or AI-generated suggestions.
 * 
 * Returns: { recommendations: string[] }
 */
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
        return NextResponse.json(data)
      }
    } catch (error) {
      // Backend endpoint doesn't exist yet, fall through to default
      console.log('Backend recommendations endpoint not available, using defaults')
    }
    
    // Option 2: Return default recommendations
    // You can customize this to generate dynamic recommendations based on:
    // - User's recent assets
    // - User's plan/features
    // - Context from current page
    // - AI-generated suggestions
    
    const defaultRecommendations = [
      "מצא לי נכסים בתל אביב מתחת למחיר שוק",
      "מה הפוטנציאל של הנכס הזה?",
      "איזה סיכונים יש בנכס הזה?"
    ]
    
    return NextResponse.json({
      recommendations: defaultRecommendations
    })
    
  } catch (error) {
    console.error('Error in recommendations API:', error)
    return NextResponse.json(
      { error: 'Failed to fetch recommendations' },
      { status: 500 }
    )
  }
}

