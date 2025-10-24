import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: { batchId: string } },
) {
  const { batchId } = params
  try {
    const cookieStore = cookies()
    const token = cookieStore.get('access_token')?.value
    const url = new URL(`${BACKEND_URL}/api/imports/${batchId}`)
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      cache: 'no-store',
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
    const message = error instanceof Error ? error.message : 'Failed to fetch import batch'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { batchId: string } },
) {
  const { batchId } = params
  try {
    const cookieStore = cookies()
    const token = cookieStore.get('access_token')?.value
    const body = await request.json().catch(() => ({}))

    const response = await fetch(`${BACKEND_URL}/api/imports/${batchId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
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
    const message = error instanceof Error ? error.message : 'Failed to update import batch'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
