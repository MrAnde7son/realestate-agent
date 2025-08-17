import { NextResponse } from 'next/server'
import { listings } from '@/lib/data'
export async function GET(req: Request){
  const url = new URL(req.url)
  const page = Number(url.searchParams.get('page') ?? 1)
  const pageSize = Number(url.searchParams.get('pageSize') ?? 50)
  const start = (page - 1) * pageSize
  const rows = listings.slice(start, start + pageSize)
  return NextResponse.json({ rows, total: listings.length, page, pageSize })
}
