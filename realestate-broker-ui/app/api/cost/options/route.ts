import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET() {
  try {
    const resp = await fetch(`${BACKEND_URL}/api/cost/options`)

    if (!resp.ok) {
      const text = await resp.text()
      console.error('Backend cost options error:', resp.status, text)
      return NextResponse.json(
        { error: 'Failed to fetch cost options' },
        { status: 502 }
      )
    }

    const data = await resp.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Cost options error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch cost options' },
      { status: 500 }
    )
  }
}
