import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateToken } from '@/lib/token-utils'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

/**
 * Sanitize error messages to prevent exposing backend details to users
 */
function sanitizeErrorMessage(error: string): string {
  const errorLower = error.toLowerCase()
  
  // Rate limit errors
  if (errorLower.includes('rate limit') || errorLower.includes('429') || errorLower.includes('tokens per day')) {
    return 'השירות עמוס כרגע. אנא נסה שוב בעוד כמה דקות.'
  }
  
  // Quota errors
  if (errorLower.includes('quota') || errorLower.includes('limit reached')) {
    return 'המגבלה היומית הושגה. אנא נסה שוב מחר.'
  }
  
  // Timeout errors
  if (errorLower.includes('timeout')) {
    return 'הבקשה ארכה יותר מדי זמן. אנא נסה שוב.'
  }
  
  // Connection errors
  if (errorLower.includes('connection') || errorLower.includes('network')) {
    return 'בעיית חיבור. אנא בדוק את החיבור לאינטרנט ונסה שוב.'
  }
  
  // If error already looks user-friendly (contains Hebrew), return as-is
  if (/[\u0590-\u05FF]/.test(error)) {
    return error
  }
  
  // Generic fallback
  return 'אירעה שגיאה בעת קבלת התשובה. אנא נסה שוב מאוחר יותר.'
}

const chatRequestSchema = z.object({
  message: z.string().min(1, 'Message is required'),
  chat_history: z.array(z.object({
    role: z.string(),
    content: z.string()
  })).optional()
})

export async function POST(req: Request) {
  try {
    const cookieStore = await cookies()
    let token = cookieStore.get('access_token')?.value
    
    // Also check Authorization header for API tokens
    if (!token) {
      const authHeader = req.headers.get('authorization')
      if (authHeader && authHeader.startsWith('Bearer ')) {
        token = authHeader.substring(7)
      }
    }
    
    // Validate token only if it's a JWT (has 3 parts separated by dots)
    // API tokens are not JWTs, so we skip validation and let the backend handle them
    const isJWT = token && token.split('.').length === 3
    if (isJWT) {
      const tokenValidation = validateToken(token)
      if (!tokenValidation.isValid) {
        const response = NextResponse.json(
          { error: 'Unauthorized - Token expired or invalid' },
          { status: 401 }
        )
        response.cookies.delete('access_token')
        response.cookies.delete('refresh_token')
        return response
      }
    } else if (!token) {
      // No token at all
      return NextResponse.json(
        { error: 'Unauthorized - No token provided' },
        { status: 401 }
      )
    }
    // If token exists but is not a JWT, assume it's an API token and let backend validate it
    
    const body = await req.json()
    
    // Validate input
    const validatedData = chatRequestSchema.parse(body)
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    }
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
    
    const res = await fetch(`${BACKEND_URL}/api/agent/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(validatedData)
    })
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ error: 'Failed to get agent response' }))
      const sanitizedError = sanitizeErrorMessage(errorData.error || 'Failed to get agent response')
      return NextResponse.json(
        { error: sanitizedError },
        { status: res.status }
      )
    }
    
    const data = await res.json()
    return NextResponse.json(data)
    
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Validation failed', details: error.errors },
        { status: 400 }
      )
    }
    
    console.error('Error in agent chat API:', error)
    return NextResponse.json(
      { error: sanitizeErrorMessage('Failed to process chat request') },
      { status: 500 }
    )
  }
}

