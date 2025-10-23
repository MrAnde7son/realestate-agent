import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateToken } from '@/lib/token-utils'

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

  // Get authentication token
  let token = cookies().get('access_token')?.value
  
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
    console.log('❌ Documents API - Token validation failed:', tokenValidation.error)
    return NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 })
  }

  const incomingFormData = await request.formData()
  const file = incomingFormData.get('file')

  if (!file || typeof file === 'string') {
    return NextResponse.json({ error: 'No file provided' }, { status: 400 })
  }

  const documentType =
    (incomingFormData.get('document_type') as string) ||
    (incomingFormData.get('type') as string) ||
    'other'
  const title = (incomingFormData.get('title') as string) || file.name || 'מסמך'
  const description = incomingFormData.get('description')
  const documentDate = incomingFormData.get('document_date') as string | null
  const externalId = incomingFormData.get('external_id') as string | null
  const externalUrl = incomingFormData.get('external_url') as string | null

  const backendFormData = new FormData()
  backendFormData.append('file', file)
  backendFormData.append('document_type', documentType)
  backendFormData.append('title', title)
  if (description) {
    backendFormData.append('description', description.toString())
  }
  if (documentDate) {
    backendFormData.append('document_date', documentDate)
  }
  if (externalId) {
    backendFormData.append('external_id', externalId)
  }
  if (externalUrl) {
    backendFormData.append('external_url', externalUrl)
  }

  try {
    const backendResponse = await fetch(
      `${backendUrl}/api/assets/${id}/documents/upload/`,
      {
        method: 'POST',
        body: backendFormData,
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )

    if (backendResponse.ok) {
      const data = await backendResponse.json()
      return NextResponse.json(data)
    }

    const errorText = await backendResponse.text()
    let payload: Record<string, unknown>
    try {
      payload = errorText ? JSON.parse(errorText) : { error: 'Upload failed' }
    } catch (parseErr) {
      payload = { error: errorText || 'Upload failed' }
    }
    console.error(
      'Backend document upload failed:',
      backendResponse.status,
      payload
    )
    return NextResponse.json(payload, { status: backendResponse.status })
  } catch (error) {
    console.error('Error uploading document to backend:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
