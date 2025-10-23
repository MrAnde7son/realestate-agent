import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  const body = await req.json()
  const res = await fetch(`${process.env.BACKEND_URL}/api/support/contact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', cookie: req.headers.get('cookie') || '' },
    credentials: 'include',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await res.json(), { status: res.status })
}
