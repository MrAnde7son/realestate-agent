import { NextResponse } from 'next/server'
import { assets, deleteAsset } from '@/lib/data'
import type { Asset } from '@/lib/data'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

// Schema for new asset creation. The backend accepts various combinations of
// fields depending on the scope type, so most fields are optional here. Basic
// validation is still applied where possible.
const newAssetSchema = z.object({
  scope: z.object({
    type: z.enum(['address', 'neighborhood', 'street', 'city', 'parcel']),
    value: z.string(),
    // City is only required for some scope types (e.g. address) so mark it optional
    city: z.string().optional()
  }),
  // Address information might be derived from street/number or from the scope
  // value, so keep it optional
  address: z.string().optional(),
  city: z.string().optional(),
  street: z.string().optional(),
  number: z.number().optional(),
  gush: z.string().optional(),
  helka: z.string().optional(),
  radius: z.number().default(100),
  deltaVsAreaPct: z.number().optional(),
  domPercentile: z.number().optional(),
  competition1km: z.string().optional(),
  zoning: z.string().optional(),
  riskFlags: z.array(z.string()).optional(),
  priceGapPct: z.number().optional(),
  expectedPriceRange: z.string().optional(),
  remainingRightsSqm: z.number().optional(),
  program: z.string().optional(),
  lastPermitQ: z.string().optional(),
  noiseLevel: z.number().optional(),
  greenWithin300m: z.boolean().optional(),
  schoolsWithin500m: z.boolean().optional(),
  modelPrice: z.number().optional(),
  confidencePct: z.number().optional(),
  capRatePct: z.number().optional(),
  antennaDistanceM: z.number().optional(),
  shelterDistanceM: z.number().optional(),
  rentEstimate: z.number().optional()
})

function determineAssetType(asset: any): string {
  return asset?.propertyType || asset?.property_type || asset?.type || 'לא ידוע'
}

export async function GET() {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
  try {
    const res = await fetch(`${backendUrl}/api/assets/`)
    if (res.ok) {
      const data = await res.json()
      return NextResponse.json(data)
    }
  } catch (error) {
    console.error('Error fetching assets from backend:', error)
  }

  // Fallback to mock data
  const transformedRows =
    assets.map((asset: any) => ({
      id: asset.id,
      address: asset.address,
      price: asset.price,
      bedrooms: asset.bedrooms || 0,
      bathrooms: asset.bathrooms || 1, // Default since not in backend
      area: asset.area,
      type: determineAssetType(asset),
      status: asset.status || 'active',
      images: asset.images || [],
      description: asset.description || '',
      features: asset.features || [],
      contactInfo: asset.contactInfo || { agent: '', phone: '', email: '' },
      city: asset.city || 'תל אביב',
      neighborhood: asset.neighborhood || '',
      netSqm: asset.netSqm || 0,
      pricePerSqmDisplay: asset.pricePerSqmDisplay || 0,
      deltaVsAreaPct: asset.deltaVsAreaPct,
      domPercentile: asset.domPercentile,
      competition1km: asset.competition1km,
      zoning: asset.zoning,
      riskFlags: asset.riskFlags,
      priceGapPct: asset.priceGapPct,
      expectedPriceRange: asset.expectedPriceRange,
      remainingRightsSqm: asset.remainingRightsSqm,
      program: asset.program,
      lastPermitQ: asset.lastPermitQ,
      noiseLevel: asset.noiseLevel,
      greenWithin300m: asset.greenWithin300m,
      schoolsWithin500m: asset.schoolsWithin500m,
      modelPrice: asset.modelPrice,
      confidencePct: asset.confidencePct,
      capRatePct: asset.capRatePct,
      antennaDistanceM: asset.antennaDistanceM,
      shelterDistanceM: asset.shelterDistanceM,
      rentEstimate: asset.rentEstimate,
      assetId: asset.assetId || asset.id,
      assetStatus: asset.assetStatus || 'active',
      sources: asset.sources || [],
      primarySource: asset.primarySource || 'manual'
    })) || []

  return NextResponse.json({ rows: transformedRows })
}

export async function DELETE(req: Request) {
  try {
    const contentType = req.headers.get('content-type')
    let assetId: number | null = null

    if (contentType && contentType.includes('application/json')) {
      try {
        const body = await req.json()
        assetId = body.assetId
      } catch (err) {
        console.error('Error parsing JSON body:', err)
        return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
      }
    } else {
      const url = new URL(req.url)
      assetId = url.searchParams.get('assetId') ? parseInt(url.searchParams.get('assetId')!) : null
    }

    if (!assetId) {
      return NextResponse.json({ error: 'assetId required' }, { status: 400 })
    }

    try {
      const res = await fetch(`${BACKEND_URL}/api/assets/`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assetId }),
      })

      if (res.ok) {
        const data = await res.json()
        return NextResponse.json(data, { status: res.status })
      } else {
        const deleted = deleteAsset(assetId)
        if (deleted) {
          return NextResponse.json({
            message: `Asset ${assetId} deleted successfully from local storage`,
            deletedAsset: deleted,
          }, { status: 200 })
        } else {
          return NextResponse.json({ error: 'Asset not found' }, { status: 404 })
        }
      }
    } catch (err) {
      console.error('Error connecting to backend for delete:', err)
      const deleted = deleteAsset(assetId)
      if (deleted) {
        return NextResponse.json({
          message: `Asset ${assetId} deleted successfully from local storage`,
          deletedAsset: deleted,
        }, { status: 200 })
      } else {
        return NextResponse.json({ error: 'Asset not found' }, { status: 404 })
      }
    }
  } catch (err) {
    console.error('Error in DELETE handler:', err)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json()

    // Validate input
    const validatedData = newAssetSchema.parse(body)
    // Derive address/city if missing. This mirrors the backend's flexibility
    // and allows submissions that only provide street/number or parcel info.
    const derivedAddress =
      validatedData.address ||
      (validatedData.street
        ? `${validatedData.street} ${validatedData.number ?? ''}`.trim()
        : validatedData.scope.value)

    const derivedCity = validatedData.city || validatedData.scope.city || ''

    // Pull through optional metrics if provided
    const metricKeys = [
      'deltaVsAreaPct',
      'domPercentile',
      'competition1km',
      'zoning',
      'riskFlags',
      'priceGapPct',
      'expectedPriceRange',
      'remainingRightsSqm',
      'program',
      'lastPermitQ',
      'noiseLevel',
      'greenWithin300m',
      'schoolsWithin500m',
      'modelPrice',
      'confidencePct',
      'capRatePct',
      'antennaDistanceM',
      'shelterDistanceM',
      'rentEstimate'
    ] as const

    const extraFields: Partial<Asset> = {}
    for (const key of metricKeys) {
      if ((validatedData as any)[key] !== undefined) {
        ;(extraFields as any)[key] = (validatedData as any)[key]
      }
    }

    // Prepare asset data matching frontend contract (without id yet)
    const assetPayload: Omit<Asset, 'id'> = {
      address: derivedAddress,
      price: 0, // Will be populated by enrichment pipeline
      bedrooms: 0,
      bathrooms: 1,
      area: 0,
      type: determineAssetType(body),
      status: 'pending',
      images: [],
      description: `נכס ${validatedData.scope.type} - ${derivedCity}`,
      features: [],
      contactInfo: {
        agent: '',
        phone: '',
        email: ''
      },
      city: derivedCity,
      neighborhood: '',
      netSqm: 0,
      pricePerSqmDisplay: 0,
      assetStatus: 'pending',
      sources: [],
      primarySource: 'manual',
      ...extraFields
    }

    // Send full asset to backend to ensure contract parity
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    const backendResponse = await fetch(`${backendUrl}/api/assets/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(assetPayload)
    })

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text()
      console.error('Backend asset creation failed:', backendResponse.status, errorText)
      return NextResponse.json(
        { error: 'Failed to create asset in backend' },
        { status: backendResponse.status }
      )
    }

    const backendData = await backendResponse.json()
    const id = backendData.id

    // Final asset with backend-generated id
    const asset: Asset = {
      id,
      ...assetPayload,
      assetId: id,
      assetStatus: backendData.status || assetPayload.assetStatus
    }

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
