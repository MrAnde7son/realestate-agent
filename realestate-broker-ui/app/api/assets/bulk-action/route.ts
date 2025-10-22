import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

import { validateToken } from '@/lib/token-utils'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(req: Request) {
  try {
    const token = cookies().get('access_token')?.value
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

    let body: unknown
    try {
      body = await req.json()
    } catch (error) {
      console.error('Invalid JSON for bulk action:', error)
      return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
    }

    const response = await fetch(`${BACKEND_URL}/api/assets/bulk-action/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` })
      },
      body: JSON.stringify(body)
    })

    const text = await response.text()
    let data: unknown = null
    try {
      data = text ? JSON.parse(text) : null
    } catch (error) {
      console.error('Failed to parse bulk action response:', error)
      data = text ? { error: text } : null
    }

    if (!response.ok) {
      return NextResponse.json(
        data ?? { error: 'Failed to perform bulk action' },
        { status: response.status }
      )
    }

    return NextResponse.json(data ?? {})
  } catch (error) {
    console.error('Error performing assets bulk action:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
