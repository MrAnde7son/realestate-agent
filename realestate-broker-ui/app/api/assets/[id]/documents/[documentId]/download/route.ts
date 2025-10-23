import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateToken } from '@/lib/token-utils'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string; documentId: string } }
) {
  const { id, documentId } = params
  const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

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
  
  // Validate token
  const tokenValidation = validateToken(token)
  if (!tokenValidation.isValid) {
    console.log('❌ Document Download API - Token validation failed:', tokenValidation.error)
    return NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 })
  }

  try {
    const backendResponse = await fetch(
      `${backendUrl}/api/assets/${id}/documents/${documentId}/download/`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )

    if (backendResponse.ok) {
      const buffer = await backendResponse.arrayBuffer()
      const contentType = backendResponse.headers.get('content-type') || 'application/octet-stream'
      const contentDisposition = backendResponse.headers.get('content-disposition')
      
      return new NextResponse(buffer, {
        status: 200,
        headers: {
          'Content-Type': contentType,
          ...(contentDisposition && { 'Content-Disposition': contentDisposition }),
        },
      })
    }

    const errorText = await backendResponse.text()
    let payload: Record<string, unknown>
    try {
      payload = errorText ? JSON.parse(errorText) : { error: 'Download failed' }
    } catch (parseErr) {
      payload = { error: errorText || 'Download failed' }
    }
    console.error(
      'Backend document download failed:',
      backendResponse.status,
      payload
    )
    return NextResponse.json(payload, { status: backendResponse.status })
  } catch (error) {
    console.error('Error downloading document from backend:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
