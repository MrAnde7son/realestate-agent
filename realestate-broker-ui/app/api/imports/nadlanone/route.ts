import { NextResponse } from 'next/server'
import { getAccessToken } from '../../_utils/get-access-token'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(request: Request) {
  try {
    const token = await getAccessToken(request)
    const incoming = await request.formData()
    const outgoing = new FormData()

    incoming.forEach((value, key) => {
      if (typeof value === 'string') {
        outgoing.append(key, value)
        return
      }

      if (typeof value === 'object' && value !== null) {
        const blob = value as Blob & { name?: string }
        const filename = typeof blob.name === 'string' && blob.name ? blob.name : undefined
        outgoing.append(key, blob, filename)
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
