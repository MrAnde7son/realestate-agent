import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateToken } from '@/lib/token-utils'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

const feedbackRequestSchema = z.object({
  message_id: z.string().min(1, 'Message ID is required'),
  feedback: z.enum(['positive', 'negative'], {
    errorMap: () => ({ message: 'Feedback must be either "positive" or "negative"' })
  }),
  message_content: z.string().optional(),
  user_message: z.string().nullable().optional()
})

export async function POST(req: Request) {
  try {
    const cookieStore = await cookies()
    const token = cookieStore.get('access_token')?.value
    
    // Validate token
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
    
    const body = await req.json()
    
    // Validate input
    const validatedData = feedbackRequestSchema.parse(body)
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    }
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
    
    const res = await fetch(`${BACKEND_URL}/api/agent/feedback`, {
      method: 'POST',
      headers,
      body: JSON.stringify(validatedData)
    })
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ error: 'Failed to submit feedback' }))
      return NextResponse.json(
        { error: errorData.error || 'Failed to submit feedback' },
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
    
    console.error('Error in agent feedback API:', error)
    return NextResponse.json(
      { error: 'Failed to process feedback request' },
      { status: 500 }
    )
  }
}

