import { NextResponse } from 'next/server'
import { listings, addListing } from '@/lib/data'
export async function GET(req: Request){
  const url = new URL(req.url)
  const page = Number(url.searchParams.get('page') ?? 1)
  const pageSize = Number(url.searchParams.get('pageSize') ?? 50)
  const start = (page - 1) * pageSize
  const rows = listings.slice(start, start + pageSize)
  return NextResponse.json({ rows, total: listings.length, page, pageSize })
}

export async function POST(req: Request){
  const data = await req.json()
  const id = `l${listings.length + 1}`
  const listing = {
    id,
    address: data.address || '',
    price: data.price ?? 0,
    bedrooms: data.bedrooms ?? 0,
    bathrooms: data.bathrooms ?? 0,
    area: data.area ?? 0,
    type: data.type || 'דירה',
    status: 'active',
    images: data.images ?? [],
    description: data.description || '',
    features: data.features ?? [],
    contactInfo: data.contactInfo || { agent: '', phone: '', email: '' },
    city: data.city,
    neighborhood: data.neighborhood,
    netSqm: data.netSqm,
    pricePerSqm: data.pricePerSqm,
    deltaVsAreaPct: data.deltaVsAreaPct,
    domPercentile: data.domPercentile,
    competition1km: data.competition1km,
    zoning: data.zoning,
    riskFlags: data.riskFlags,
    priceGapPct: data.priceGapPct,
    expectedPriceRange: data.expectedPriceRange,
    remainingRightsSqm: data.remainingRightsSqm,
    program: data.program,
    lastPermitQ: data.lastPermitQ,
    noiseLevel: data.noiseLevel,
    greenWithin300m: data.greenWithin300m,
    schoolsWithin500m: data.schoolsWithin500m,
    modelPrice: data.modelPrice,
    confidencePct: data.confidencePct,
    capRatePct: data.capRatePct,
    antennaDistanceM: data.antennaDistanceM,
    shelterDistanceM: data.shelterDistanceM,
    rentEstimate: data.rentEstimate,
  }
  addListing(listing)
  return NextResponse.json({ listing }, { status: 201 })
}
