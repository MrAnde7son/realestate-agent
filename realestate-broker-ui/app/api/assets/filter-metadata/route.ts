import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET() {
  const cookieStore = await cookies()
  const token = cookieStore.get('access_token')?.value

  try {
    const res = await fetch(`${BACKEND_URL}/api/assets/filter-metadata`, {
      headers: {
        ...(token && { Authorization: `Bearer ${token}` })
      }
    })
    
    if (!res.ok) {
      return NextResponse.json({ error: 'Failed to fetch filter metadata' }, { status: res.status })
    }
    
    const data = await res.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching filter metadata from backend:', error)
    return NextResponse.json({ error: 'Failed to fetch filter metadata' }, { status: 500 })
  }
}

