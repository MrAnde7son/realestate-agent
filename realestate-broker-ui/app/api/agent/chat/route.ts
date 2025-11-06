import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateToken } from '@/lib/token-utils'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

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
      return NextResponse.json(
        { error: errorData.error || 'Failed to get agent response' },
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
      { error: 'Failed to process chat request' },
      { status: 500 }
    )
  }
}

