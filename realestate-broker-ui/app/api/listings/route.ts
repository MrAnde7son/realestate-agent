import { NextResponse } from 'next/server'
import { listings, addListing } from '@/lib/data'
import type { Listing } from '@/lib/data'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(req: Request){
  const url = new URL(req.url)
  const query = url.search
  const resp = await fetch(`${BACKEND_URL}/api/listings/${query}`, { cache: 'no-store' })
  const data = await resp.json()
  return NextResponse.json(data)
}

const newListingSchema = z.object({
  address: z.string().min(1, 'address required'),
  price: z.number().gt(0, 'price required'),
  bedrooms: z.number().int().gte(0, 'bedrooms required'),
  bathrooms: z.number().int().gte(0, 'bathrooms required'),
  area: z.number().gt(0, 'area required'),
})

export async function POST(req: Request) {
  const json = await req.json()
  const parsed = newListingSchema.safeParse(json)
  if (!parsed.success) {
    return NextResponse.json({ errors: parsed.error.flatten() }, { status: 400 })
  }
  const id = `l${listings.length + 1}`
  const data = parsed.data
  const listing: Listing = {
    id,
    address: data.address,
    price: data.price,
    bedrooms: data.bedrooms,
    bathrooms: data.bathrooms,
    area: data.area,
    type: 'דירה',
    status: 'active',
    images: [],
    description: '',
    features: [],
    contactInfo: { agent: '', phone: '', email: '' },
    city: json.city,
    neighborhood: json.neighborhood,
    netSqm: json.netSqm,
    pricePerSqm: json.pricePerSqm,
    deltaVsAreaPct: json.deltaVsAreaPct,
    domPercentile: json.domPercentile,
    competition1km: json.competition1km,
    zoning: json.zoning,
    riskFlags: json.riskFlags,
    priceGapPct: json.priceGapPct,
    expectedPriceRange: json.expectedPriceRange,
    remainingRightsSqm: json.remainingRightsSqm,
    program: json.program,
    lastPermitQ: json.lastPermitQ,
    noiseLevel: json.noiseLevel,
    greenWithin300m: json.greenWithin300m,
    schoolsWithin500m: json.schoolsWithin500m,
    modelPrice: json.modelPrice,
    confidencePct: json.confidencePct,
    capRatePct: json.capRatePct,
    antennaDistanceM: json.antennaDistanceM,
    shelterDistanceM: json.shelterDistanceM,
    rentEstimate: json.rentEstimate,
  }
  addListing(listing)
  return NextResponse.json({ listing }, { status: 201 })
}
