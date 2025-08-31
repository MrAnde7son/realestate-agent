import { NextRequest, NextResponse } from 'next/server'

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params

  try {
    // Try to upload to backend first
    const formData = await request.formData()
    const backendResponse = await fetch(`${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/api/assets/${id}/documents/`, {
      method: 'POST',
      body: formData,
    })
    
    if (backendResponse.ok) {
      const data = await backendResponse.json()
      return NextResponse.json(data)
    }
  } catch (error) {
    console.error('Error uploading document to backend:', error)
  }

  // Fallback to mock response
  const formData = await request.formData()
  const file = formData.get('file') as File
  const type = formData.get('type') as string
  
  if (!file) {
    return NextResponse.json({ error: 'No file provided' }, { status: 400 })
  }

  const mockDoc = {
    id: Date.now().toString(),
    name: file.name,
    type: type,
    url: `/uploads/${file.name}`,
    uploadedAt: new Date().toISOString()
  }

  return NextResponse.json({ doc: mockDoc })
}
