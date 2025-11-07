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
      return new NextResponse(
        'data: ' + JSON.stringify({ type: 'error', error: 'Unauthorized - Token expired or invalid' }) + '\n\n',
        {
          status: 401,
          headers: {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
          }
        }
      )
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
    
    // Forward request to backend streaming endpoint
    const backendResponse = await fetch(`${BACKEND_URL}/api/agent/chat/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify(validatedData)
    })
    
    if (!backendResponse.ok) {
      const errorText = await backendResponse.text().catch(() => 'Failed to get agent response')
      return new NextResponse(
        'data: ' + JSON.stringify({ type: 'error', error: errorText }) + '\n\n',
        {
          status: backendResponse.status,
          headers: {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
          }
        }
      )
    }
    
    // Create a readable stream that forwards the backend SSE stream
    const stream = new ReadableStream({
      async start(controller) {
        const reader = backendResponse.body?.getReader()
        const decoder = new TextDecoder()
        
        if (!reader) {
          controller.close()
          return
        }
        
        try {
          while (true) {
            const { done, value } = await reader.read()
            
            if (done) {
              controller.close()
              break
            }
            
            // Forward chunks to client
            const chunk = decoder.decode(value, { stream: true })
            controller.enqueue(new TextEncoder().encode(chunk))
          }
        } catch (error) {
          controller.error(error)
        }
      }
    })
    
    return new NextResponse(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
      }
    })
    
  } catch (error) {
    if (error instanceof z.ZodError) {
      return new NextResponse(
        'data: ' + JSON.stringify({ type: 'error', error: 'Validation failed', details: error.errors }) + '\n\n',
        {
          status: 400,
          headers: {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
          }
        }
      )
    }
    
    console.error('Error in agent chat stream API:', error)
    return new NextResponse(
      'data: ' + JSON.stringify({ type: 'error', error: 'Failed to process chat request' }) + '\n\n',
      {
        status: 500,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        }
      }
    )
  }
}

