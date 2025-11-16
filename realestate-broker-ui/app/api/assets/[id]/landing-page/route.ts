import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateToken } from '@/lib/token-utils'

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

  console.log('🔄 Landing Page API route called for asset:', id)

  // Get authentication token
  const cookieStore = await cookies()
  let token = cookieStore.get('access_token')?.value
  
  // If no token in cookies, try to get from request headers
  if (!token) {
    const authHeader = request.headers.get('authorization')
    if (authHeader && authHeader.startsWith('Bearer ')) {
      token = authHeader.substring(7)
    }
  }
  
  // Validate token only if it's a JWT (has 3 parts separated by dots)
  // API tokens are not JWTs, so we skip validation and let the backend handle them
  if (token) {
    const isJWT = token.split('.').length === 3
    if (isJWT) {
      const tokenValidation = validateToken(token)
      if (!tokenValidation.isValid) {
        console.log('❌ Landing Page API - Token validation failed:', tokenValidation.error)
        return NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 })
      }
    }
  } else {
    console.log('❌ Landing Page API - No token provided')
    return NextResponse.json({ error: 'Unauthorized - No token provided' }, { status: 401 })
  }

  try {
    console.log('📡 Fetching landing page from backend:', `${backendUrl}/api/assets/${id}/landing-page`)
    const backendResponse = await fetch(
      `${backendUrl}/api/assets/${id}/landing-page`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )

    console.log('📥 Backend response:', {
      ok: backendResponse.ok,
      status: backendResponse.status,
      contentType: backendResponse.headers.get('content-type'),
      contentDisposition: backendResponse.headers.get('content-disposition'),
    })

    if (backendResponse.ok) {
      const buffer = await backendResponse.arrayBuffer()
      const contentType = backendResponse.headers.get('content-type') || 'text/html; charset=utf-8'
      const contentDisposition = backendResponse.headers.get('content-disposition')
      const cacheControl = backendResponse.headers.get('cache-control')
      
      console.log('✅ Returning landing page:', {
        bufferSize: buffer.byteLength,
        contentType,
        contentDisposition,
      })
      
      return new NextResponse(buffer, {
        status: 200,
        headers: {
          'Content-Type': contentType,
          ...(contentDisposition && { 'Content-Disposition': contentDisposition }),
          ...(cacheControl && { 'Cache-Control': cacheControl }),
        },
      })
    }

    const errorText = await backendResponse.text()
    let payload: Record<string, unknown>
    try {
      payload = errorText ? JSON.parse(errorText) : { error: 'Landing page generation failed' }
    } catch (parseErr) {
      payload = { error: errorText || 'Landing page generation failed' }
    }
    console.error(
      'Backend landing page generation failed:',
      backendResponse.status,
      payload
    )
    return NextResponse.json(payload, { status: backendResponse.status })
  } catch (error) {
    console.error('Error in landing page route handler:', error)
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    const errorStack = error instanceof Error ? error.stack : undefined
    console.error('Route handler error details:', { errorMessage, errorStack })
    return NextResponse.json({ 
      error: 'Internal server error',
      details: process.env.NODE_ENV === 'development' ? errorMessage : undefined
    }, { status: 500 })
  }
}

