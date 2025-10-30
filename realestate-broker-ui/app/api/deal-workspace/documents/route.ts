import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(request: Request) {
  const cookieStore = await cookies()
  const token = cookieStore.get('access_token')?.value

  let search = ''
  try {
    const url = new URL(request.url)
    search = url.search
  } catch (error) {
    console.warn('Failed to parse documents request URL:', error)
  }

  try {
    const response = await fetch(`${BACKEND_URL}/api/deal-workspace/documents${search}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })

    const text = await response.text()
    let data: unknown = null
    if (text) {
      try {
        data = JSON.parse(text)
      } catch (error) {
        console.warn('Failed to parse backend documents response:', error)
      }
    }

    if (!response.ok) {
      return NextResponse.json(
        { error: (data as any)?.error || `Failed to load documents (status ${response.status})` },
        { status: response.status }
      )
    }

    if (Array.isArray(data)) {
      return NextResponse.json({ documents: data })
    }

    return NextResponse.json({ documents: (data as any)?.results ?? [] })
  } catch (error) {
    console.error('Failed to fetch deal workspace documents:', error)
    return NextResponse.json({ error: 'Unable to fetch documents' }, { status: 500 })
  }
}
