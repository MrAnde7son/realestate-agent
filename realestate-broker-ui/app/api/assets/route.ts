import { NextResponse } from 'next/server'
import { assets, addAsset } from '@/lib/data'
import type { Asset } from '@/lib/data'
import { z } from 'zod'

const newAssetSchema = z.object({
  scope: z.object({
    type: z.enum(['address', 'neighborhood', 'street', 'city', 'parcel']),
    value: z.string(),
    city: z.string()
  }),
  address: z.string(),
  city: z.string(),
  street: z.string().optional(),
  number: z.number().optional(),
  gush: z.string().optional(),
  helka: z.string().optional(),
  radius: z.number().optional()
})

export async function GET() {
  try {
    // Return mock data for now
    const transformedRows = assets.map((asset: any) => ({
      id: asset.id?.toString(),
      address: asset.address,
      price: asset.price,
      bedrooms: asset.bedrooms || 0,
      bathrooms: asset.bathrooms || 1, // Default since not in backend
      area: asset.area,
      type: asset.type || 'דירה',
      status: asset.status || 'active',
      images: asset.images || [],
      description: asset.description || '',
      features: asset.features || [],
      contactInfo: asset.contactInfo || { agent: '', phone: '', email: '' },
      city: asset.city || 'תל אביב',
      neighborhood: asset.neighborhood || '',
      netSqm: asset.netSqm || 0,
      pricePerSqm: asset.pricePerSqm || 0,
      deltaVsAreaPct: asset.deltaVsAreaPct || 0, // Calculate if needed
      domPercentile: asset.domPercentile || 50, // Default
      competition1km: asset.competition1km || 'בינוני',
      zoning: asset.zoning || 'מגורים א\'',
      riskFlags: asset.riskFlags || [],
      priceGapPct: asset.priceGapPct || 0,
      expectedPriceRange: asset.expectedPriceRange || '',
      remainingRightsSqm: asset.remainingRightsSqm || 0,
      program: asset.program || '',
      lastPermitQ: asset.lastPermitQ || '',
      noiseLevel: asset.noiseLevel || 2,
      greenWithin300m: asset.greenWithin300m || true,
      schoolsWithin500m: asset.schoolsWithin500m || true,
      modelPrice: asset.modelPrice || 0,
      confidencePct: asset.confidencePct || 75, // Default
      capRatePct: asset.capRatePct || 3.0,
      antennaDistanceM: asset.antennaDistanceM || 150,
      shelterDistanceM: asset.shelterDistanceM || 100,
      rentEstimate: asset.rentEstimate || 0,
      asset_id: asset.asset_id || asset.id,
      asset_status: asset.asset_status || 'active',
      sources: asset.sources || [],
      primary_source: asset.primary_source || 'manual'
    })) || []

    return NextResponse.json({ rows: transformedRows })
  } catch (error) {
    console.error('Error fetching assets:', error)
    return NextResponse.json({ error: 'Failed to fetch assets' }, { status: 500 })
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json()
    
    // Validate input
    const validatedData = newAssetSchema.parse(body)
    
    // Create asset with available data, using defaults for missing fields
    const asset: Asset = {
      id: `asset_${Date.now()}`, // Generate unique ID
      address: validatedData.address,
      price: 0, // Will be populated by enrichment pipeline
      bedrooms: 0,
      bathrooms: 1,
      area: 0,
      type: 'דירה',
      status: 'pending',
      images: [],
      description: `נכס ${validatedData.scope.type} - ${validatedData.city}`,
      features: [],
      contactInfo: {
        agent: '',
        phone: '',
        email: ''
      },
      city: validatedData.city,
      neighborhood: '',
      netSqm: 0,
      pricePerSqm: 0,
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
      modelPrice: 0,
      confidencePct: 75,
      capRatePct: 3.0,
      antennaDistanceM: 150,
      shelterDistanceM: 100,
      rentEstimate: 0,
      asset_id: Date.now(),
      asset_status: 'pending',
      sources: [],
      primary_source: 'manual'
    }
    
    // Add to in-memory store
    addAsset(asset)
    return NextResponse.json({ asset }, { status: 201 })
    
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ 
        error: 'Validation failed', 
        details: error.errors 
      }, { status: 400 })
    }
    
    console.error('Error creating asset:', error)
    return NextResponse.json({ 
      error: 'Failed to create asset' 
    }, { status: 500 })
  }
}
