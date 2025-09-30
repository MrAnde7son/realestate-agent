import { NextRequest, NextResponse } from 'next/server'

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params
  const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

  const incomingFormData = await request.formData()
  const file = incomingFormData.get('file')

  if (!(file instanceof File)) {
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

  const headers = new Headers()
  const cookie = request.headers.get('cookie')
  const authorization = request.headers.get('authorization')
  if (cookie) {
    headers.set('cookie', cookie)
  }
  if (authorization) {
    headers.set('authorization', authorization)
  }

  try {
    const backendResponse = await fetch(
      `${backendUrl}/api/assets/${id}/documents/upload/`,
      {
        method: 'POST',
        body: backendFormData,
        headers,
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
  }

  const mockDoc = {
    id: Date.now().toString(),
    title,
    name: title,
    type: documentType,
    url: `/uploads/${file.name}`,
    uploaded_at: new Date().toISOString(),
    source: 'mock'
  }

  return NextResponse.json({ doc: mockDoc })
}
