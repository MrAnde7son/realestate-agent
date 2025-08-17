import { NextResponse } from 'next/server'
import { rightsByListing } from '@/lib/data'

export async function GET(_: Request, props: { params: Promise<{ id: string }> }) {
  const params = await props.params
  const rights = rightsByListing(params.id)
  if(!rights) return NextResponse.json({ rights: null })
  return NextResponse.json({ rights })
}
