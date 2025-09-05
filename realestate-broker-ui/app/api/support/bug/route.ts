import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  const form = await req.formData()
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/api/support/bug`, {
    method: 'POST',
    headers: { cookie: req.headers.get('cookie') || '' },
    credentials: 'include',
    body: form,
  })
  return NextResponse.json(await res.json(), { status: res.status })
}
