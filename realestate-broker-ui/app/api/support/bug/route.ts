import { NextRequest, NextResponse } from 'next/server'

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  'http://127.0.0.1:8000'

export async function POST(req: NextRequest) {
  const form = await req.formData()
  const res = await fetch(`${API_BASE}/api/support/bug`, {
    method: 'POST',
    headers: { cookie: req.headers.get('cookie') || '' },
    credentials: 'include',
    body: form,
  })
  return NextResponse.json(await res.json(), { status: res.status })
}
