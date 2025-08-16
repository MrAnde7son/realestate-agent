import { NextResponse } from 'next/server'
import { appraisalByListing, compsByListing } from '@/lib/data'

export async function GET(_: Request, props: { params: Promise<{ id: string }> }) {
  const params = await props.params
  const appraisal = appraisalByListing(params.id)
  const comps = compsByListing(params.id)
  return NextResponse.json({ appraisal, comps })
}
