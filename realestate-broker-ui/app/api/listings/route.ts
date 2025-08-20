import { NextResponse } from 'next/server'
import { listings, addListing } from '@/lib/data'
import type { Listing } from '@/lib/data'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(req: Request){
  try {
    // For now, always use mock data for demo purposes
    // To enable backend integration, uncomment the backend fetch logic below
    
    // Use mock data for immediate testing
    console.log('Using mock data for listings')
    return NextResponse.json({ rows: listings })
    
    /* Backend integration code (commented out for demo):
    const url = new URL(req.url)
    const query = url.search
    const resp = await fetch(`${BACKEND_URL}/api/listings/${query}`, { cache: 'no-store' })
    
    if (!resp.ok) {
      console.error('Backend API error:', resp.status, resp.statusText)
      // Fallback to mock data if backend is unavailable
      return NextResponse.json({ rows: listings })
    }
    
    const data = await resp.json()
    
    // Transform backend data to frontend format
    const transformedRows = data.rows?.map((listing: any) => ({
      id: listing.id?.toString() || listing.external_id,
      address: listing.address,
      price: listing.price,
      bedrooms: listing.rooms || 0,
      bathrooms: 1, // Default since not in backend
      area: listing.size || 0,
      type: listing.property_type || 'דירה',
      status: 'active' as const,
      images: listing.images || [],
      description: listing.description || '',
      features: listing.features || [],
      contactInfo: listing.contact_info || { agent: '', phone: '', email: '' },
      city: listing.address?.split(',')[1]?.trim() || 'תל אביב',
      neighborhood: '',
      netSqm: listing.size || 0,
      pricePerSqm: listing.price && listing.size ? Math.round(listing.price / listing.size) : 0,
      deltaVsAreaPct: 0, // Calculate if needed
      domPercentile: 50, // Default
      competition1km: 'בינוני',
      zoning: 'מגורים א\'',
      riskFlags: [],
      priceGapPct: 0,
      expectedPriceRange: '',
      remainingRightsSqm: 0,
      program: '',
      lastPermitQ: '',
      noiseLevel: 2,
      greenWithin300m: true,
      schoolsWithin500m: true,
      modelPrice: listing.price,
      confidencePct: 75, // Default
      capRatePct: 3.0,
      antennaDistanceM: 150,
      shelterDistanceM: 100,
      rentEstimate: listing.price ? Math.round(listing.price * 0.004) : 0 // 0.4% monthly
    })) || []
    
    return NextResponse.json({ rows: transformedRows })
    */
  } catch (error) {
    console.error('Error fetching listings:', error)
    // Fallback to mock data on error
    return NextResponse.json({ rows: listings })
  }
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
