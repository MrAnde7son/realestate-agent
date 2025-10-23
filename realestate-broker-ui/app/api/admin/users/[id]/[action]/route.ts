// app/api/admin/users/[id]/[action]/route.ts
import { NextResponse } from 'next/server'

const API_BASE_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(
  request: Request,
  context: { params: Promise<{ id: string; action: string }> }
) {
  try {
    const { id, action } = await context.params
    const authHeader = request.headers.get('authorization') ?? undefined

    const response = await fetch(`${API_BASE_URL}/api/admin/users/${id}/${action}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader ? { Authorization: authHeader } : {}),
      },
      // If your backend sets auth cookies and you need them:
      // credentials: 'include',
    })

    if (!response.ok) {
      const errorData = await response.text()
      return NextResponse.json(
        { error: `Failed to ${action} user`, details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Admin user action error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
