import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET() {
  try {
    const resp = await fetch(`${BACKEND_URL}/api/analytics/property-types/`, { cache: 'no-store' })
    if (!resp.ok) {
      console.error('Backend error:', resp.status, resp.statusText)
      return NextResponse.json({ rows: [] })
    }
    const data = await resp.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching property type distribution:', error)
    return NextResponse.json({ rows: [] })
  }
}
