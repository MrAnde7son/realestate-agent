import { NextRequest, NextResponse } from 'next/server'
import { getAccessToken } from '../../_utils/get-access-token'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

type RouteContext = { params: Record<string, string | string[]> }

function extractBatchId(context: RouteContext): string {
  const raw = context.params?.batchId

  if (Array.isArray(raw)) {
    return raw[0] ?? ''
  }

  return raw ?? ''
}

export async function GET(request: NextRequest, context: unknown) {
  const batchId = extractBatchId(context as RouteContext)
  if (!batchId) {
    return NextResponse.json({ error: 'Missing batch identifier' }, { status: 400 })
  }
  try {
    const token = await getAccessToken(request)
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

export async function POST(request: NextRequest, context: unknown) {
  const batchId = extractBatchId(context as RouteContext)
  if (!batchId) {
    return NextResponse.json({ error: 'Missing batch identifier' }, { status: 400 })
  }
  try {
    const token = await getAccessToken(request)
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
