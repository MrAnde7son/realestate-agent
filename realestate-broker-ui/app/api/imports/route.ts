import { NextResponse } from 'next/server'
import { getAccessToken } from '../_utils/get-access-token'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(request: Request) {
  try {
    const token = await getAccessToken(request)
    const url = new URL(request.url)
    const backendUrl = new URL(`${BACKEND_URL}/api/imports/`)
    if (url.search) {
      backendUrl.search = url.search
    }

    const response = await fetch(backendUrl, {
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
    const message = error instanceof Error ? error.message : 'Failed to fetch imports'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
