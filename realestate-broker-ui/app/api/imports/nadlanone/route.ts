import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(request: Request) {
  try {
    const cookieStore = await cookies()
    const token = cookieStore.get('access_token')?.value
    const incoming = await request.formData()
    const outgoing = new FormData()

    incoming.forEach((value, key) => {
      if (typeof value === 'string') {
        outgoing.append(key, value)
      } else if (value instanceof File) {
        outgoing.append(key, value, value.name)
      }
    })

    const response = await fetch(`${BACKEND_URL}/api/imports/nadlanone`, {
      method: 'POST',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: outgoing,
    })

    const text = await response.text()
    let data: any
    try {
      data = text ? JSON.parse(text) : {}
    } catch {
      data = { error: text }
    }

    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Import request failed'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
