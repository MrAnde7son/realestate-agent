import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function POST(req: Request){
  const body = await req.json()
  const resp = await fetch(`${BACKEND_URL}/api/sync-address/`,{
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await resp.json()
  return NextResponse.json(data, { status: resp.status })
}
