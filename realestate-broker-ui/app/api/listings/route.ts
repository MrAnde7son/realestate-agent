import { NextResponse } from 'next/server'
import { listings, addListing } from '@/lib/data'
import type { Listing } from '@/lib/data'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(req: Request){
  try {
    const url = new URL(req.url)
    const query = url.search
    const resp = await fetch(`${BACKEND_URL}/api/assets/${query}`, { cache: 'no-store' })
    
    if (!resp.ok) {
      console.error('Backend API error:', resp.status, resp.statusText)
      // Fallback to mock data if backend is unavailable
      console.log('Falling back to mock data for listings')
      return NextResponse.json({ rows: listings })
    }
    
    const data = await resp.json()
    
    // Transform backend data to frontend format
    const transformedRows = data.rows?.map((listing: any) => ({
      id: listing.id?.toString() || listing.external_id,
      address: listing.address,
      price: listing.price,
      bedrooms: listing.bedrooms || 0,
      bathrooms: listing.bathrooms || 1, // Default since not in backend
      area: listing.area,
      type: listing.type || 'דירה',
      status: listing.status || 'active',
      images: listing.images || [],
      description: listing.description || '',
      features: listing.features || [],
      contactInfo: listing.contactInfo || { agent: '', phone: '', email: '' },
      city: listing.city || 'תל אביב',
      neighborhood: listing.neighborhood || '',
      netSqm: listing.netSqm || 0,
      pricePerSqm: listing.pricePerSqm || 0,
      deltaVsAreaPct: listing.deltaVsAreaPct || 0, // Calculate if needed
      domPercentile: listing.domPercentile || 50, // Default
      competition1km: listing.competition1km || 'בינוני',
      zoning: listing.zoning || 'מגורים א\'',
      riskFlags: listing.riskFlags || [],
      priceGapPct: listing.priceGapPct || 0,
      expectedPriceRange: listing.expectedPriceRange || '',
      remainingRightsSqm: listing.remainingRightsSqm || 0,
      program: listing.program || '',
      lastPermitQ: listing.lastPermitQ || '',
      noiseLevel: listing.noiseLevel || 2,
      greenWithin300m: listing.greenWithin300m || true,
      schoolsWithin500m: listing.schoolsWithin500m || true,
      modelPrice: listing.modelPrice || listing.price || 0,
      confidencePct: listing.confidencePct || 75, // Default
      capRatePct: listing.capRatePct || 3.0,
      antennaDistanceM: listing.antennaDistanceM || 150,
      shelterDistanceM: listing.shelterDistanceM || 100,
      rentEstimate: listing.rentEstimate || (listing.price ? Math.round(listing.price * 0.004) : 0), // 0.4% monthly
      asset_id: listing.asset_id,
      asset_status: listing.asset_status,
      sources: listing.sources,
      primary_source: listing.primary_source
    })) || []
    
    return NextResponse.json({ rows: transformedRows })
  } catch (error) {
    console.error('Error fetching listings:', error)
    // Fallback to mock data on error
    return NextResponse.json({ rows: listings })
  }
}

const newListingSchema = z.object({
  address: z.string().min(1, 'address required'),
  // Optional fields that will be populated from external sources
  price: z.number().optional(),
  bedrooms: z.number().int().gte(0).optional(),
  bathrooms: z.number().int().gte(0).optional(),
  area: z.number().gt(0).optional(),
  // Additional fields from sync
  city: z.string().optional(),
  neighborhood: z.string().optional(),
  type: z.string().optional(),
  description: z.string().optional(),
  features: z.array(z.string()).optional(),
  images: z.array(z.string()).optional(),
})

export async function POST(req: Request) {
  const json = await req.json()
  const parsed = newListingSchema.safeParse(json)
  if (!parsed.success) {
    return NextResponse.json({ errors: parsed.error.flatten() }, { status: 400 })
  }
  
  const id = `l${listings.length + 1}`
  const data = parsed.data
  
  // Create listing with available data, using defaults for missing fields
  const listing: Listing = {
    id,
    address: data.address,
    price: data.price || 0, // Will be populated from sync
    bedrooms: data.bedrooms || 0, // Will be populated from sync
    bathrooms: data.bathrooms || 0, // Will be populated from sync
    area: data.area || 0, // Will be populated from sync
    type: data.type || 'דירה',
    status: 'active',
    images: data.images || [],
    description: data.description || '',
    features: data.features || [],
    contactInfo: { agent: '', phone: '', email: '' },
    city: data.city || data.address?.split(',')[1]?.trim() || 'תל אביב',
    neighborhood: data.neighborhood || '',
    netSqm: data.area || 0,
    pricePerSqm: data.price && data.area ? Math.round(data.price / data.area) : 0,
    deltaVsAreaPct: 0,
    domPercentile: 50,
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
    modelPrice: data.price || 0,
    confidencePct: 75,
    capRatePct: 3.0,
    antennaDistanceM: 150,
    shelterDistanceM: 100,
    rentEstimate: data.price ? Math.round(data.price * 0.004) : 0
  }
  
  addListing(listing)
  return NextResponse.json({ listing }, { status: 201 })
}
