import { NextResponse } from 'next/server'
import { listings } from '@/lib/data'
export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }){
  const { id } = await params
  const listing = listings.find(l => l.id === id)
  if(!listing) return new NextResponse('Not found', { status: 404 })
  return NextResponse.json({ listing })
}
