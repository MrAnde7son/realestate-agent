import { NextResponse } from 'next/server'
import { appraisalByListing, compsByListing } from '@/lib/data'
export async function GET(_: Request, { params }: { params: { id: string }}){
  const appraisal = (appraisalByListing as any)[params.id]
  const comps = (compsByListing as any)[params.id] ?? []
  return NextResponse.json({ appraisal, comps })
}
