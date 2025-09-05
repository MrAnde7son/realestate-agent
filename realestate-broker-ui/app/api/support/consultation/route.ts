import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  const body = await req.json()
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/api/support/consultation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', cookie: req.headers.get('cookie') || '' },
    credentials: 'include',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await res.json(), { status: res.status })
}
