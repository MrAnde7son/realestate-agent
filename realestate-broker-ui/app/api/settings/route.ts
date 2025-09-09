import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateToken } from '@/lib/token-utils'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET() {
  const token = cookies().get('access_token')?.value
  
  // Validate token
  const tokenValidation = validateToken(token)
  if (!tokenValidation.isValid) {
    console.log('❌ Settings API - Token validation failed:', tokenValidation.error)
    const response = NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 })
    response.cookies.delete('access_token')
    response.cookies.delete('refresh_token')
    return response
  }

  const res = await fetch(`${BACKEND_URL}/api/settings/`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  const data = await res.json().catch(() => ({}))
  return NextResponse.json(data, { status: res.status })
}

export async function PUT(req: Request) {
  const token = cookies().get('access_token')?.value
  
  // Validate token
  const tokenValidation = validateToken(token)
  if (!tokenValidation.isValid) {
    console.log('❌ Settings API PUT - Token validation failed:', tokenValidation.error)
    const response = NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 })
    response.cookies.delete('access_token')
    response.cookies.delete('refresh_token')
    return response
  }
  let body
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  const res = await fetch(`${BACKEND_URL}/api/settings/`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(body)
  })
  const data = await res.json().catch(() => ({}))
  return NextResponse.json(data, { status: res.status })
}
