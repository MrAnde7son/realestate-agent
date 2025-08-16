import { NextResponse } from 'next/server'
import { rightsByListing } from '@/lib/data'
export async function GET(_: Request, { params }: { params: { id: string }}){
  const rights = rightsByListing[params.id]
  if(!rights) return NextResponse.json({ rights: null })
  return NextResponse.json({ rights })
}
