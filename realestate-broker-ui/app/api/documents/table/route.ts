import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateToken } from '@/lib/token-utils'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(request: Request) {
  try {
    const cookieStore = await cookies()
    let token = cookieStore.get('access_token')?.value

    if (!token) {
      const authHeader = request.headers.get('authorization')
      if (authHeader && authHeader.startsWith('Bearer ')) {
        token = authHeader.substring(7)
      }
    }

    const tokenValidation = validateToken(token)
    if (!tokenValidation.isValid) {
      return NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 })
    }

    const { searchParams } = new URL(request.url)
    const backendUrl = `${BACKEND_URL}/api/documents/table/?${searchParams.toString()}`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch documents' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Documents table API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
