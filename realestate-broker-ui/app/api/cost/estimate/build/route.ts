import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(req: NextRequest) {
  try {
    const payload = await req.json()

    const resp = await fetch(`${BACKEND_URL}/api/cost/estimate/build`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      // If the app passes auth via cookies/headers, forward them here as needed.
    })

    if (!resp.ok) {
      const text = await resp.text()
      console.error('Backend cost estimate error:', resp.status, text)
      return NextResponse.json(
        { error: 'Failed to fetch build cost estimate' },
        { status: 502 }
      )
    }

    const data = await resp.json()
    return NextResponse.json(data)
  } catch (err) {
    console.error('Proxy error (cost estimate):', err)
    return NextResponse.json({ error: 'Proxy error' }, { status: 500 })
  }
}
