import { NextResponse } from 'next/server'
import type { Asset } from '@/lib/normalizers/asset'
import { z } from 'zod'
import { cookies } from 'next/headers'
import { normalizeFromBackend, determineAssetType } from '@/lib/normalizers/asset'
import { validateToken } from '@/lib/token-utils'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

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
  subhelka: z.string().optional(),
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

export async function GET() {
  const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
  const token = cookies().get('access_token')?.value
  
  // Validate token
  const tokenValidation = validateToken(token)
  if (!tokenValidation.isValid) {
    console.log('❌ Assets API - Token validation failed:', tokenValidation.error)
    const response = NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 })
    response.cookies.delete('access_token')
    response.cookies.delete('refresh_token')
    return response
  }
  
  try {
    const res = await fetch(`${backendUrl}/api/assets/`, {
      headers: {
        ...(token && { Authorization: `Bearer ${token}` })
      }
    })
    if (!res.ok) {
      return NextResponse.json({ error: 'Failed to fetch assets' }, { status: res.status })
    }
    const data = await res.json()
    const assets = (data.rows || data || []).map((asset: any) => normalizeFromBackend(asset))
    return NextResponse.json({ rows: assets })
  } catch (error) {
    console.error('Error fetching assets from backend:', error)
    return NextResponse.json({ error: 'Failed to fetch assets' }, { status: 500 })
  }
}

export async function DELETE(req: Request) {
  try {
    // Get authentication token
    const token = cookies().get('access_token')?.value
    
    // Validate token
    const tokenValidation = validateToken(token)
    if (!tokenValidation.isValid) {
      console.log('❌ Asset deletion - Token validation failed:', tokenValidation.error)
      const response = NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 })
      response.cookies.delete('access_token')
      response.cookies.delete('refresh_token')
      return response
    }
    
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
        const errorText = await res.text()
        return NextResponse.json({ error: errorText || 'Failed to delete asset' }, { status: res.status })
      }
    } catch (err) {
      console.error('Error connecting to backend for delete:', err)
      return NextResponse.json({ error: 'Failed to connect to backend for delete' }, { status: 500 })
    }
  } catch (err) {
    console.error('Error in DELETE handler:', err)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json()
    
    // Get authentication token
    const token = cookies().get('access_token')?.value
    console.log('🔐 Asset creation - Token found:', !!token, token ? 'Yes' : 'No')
    
    // Validate token
    const tokenValidation = validateToken(token)
    if (!tokenValidation.isValid) {
      console.log('❌ Asset creation - Token validation failed:', tokenValidation.error)
      const response = NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 })
      response.cookies.delete('access_token')
      response.cookies.delete('refresh_token')
      return response
    }

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
      city: derivedCity,
      street: validatedData.street,
      number: validatedData.number,
      gush: validatedData.gush,
      helka: validatedData.helka,
      subhelka: validatedData.subhelka,
      type: determineAssetType(body),
      assetStatus: 'pending',
      ...extraFields
    }

    // Prepare payload for backend API including scope information
    const backendPayload = {
      scope: validatedData.scope,
      city: derivedCity,
      street: validatedData.street,
      number: validatedData.number,
      gush: validatedData.gush,
      helka: validatedData.helka,
      subhelka: validatedData.subhelka,
      radius: validatedData.radius
    }

    console.log('Attempting to create asset with backend payload:', backendPayload)

    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
    try {
      const backendResponse = await fetch(`${backendUrl}/api/assets/`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` })
        },
        body: JSON.stringify(backendPayload)
      })

      if (!backendResponse.ok) {
        const errorText = await backendResponse.text()
        console.error('Backend asset creation failed:', backendResponse.status, errorText)
        return NextResponse.json(
          { error: 'Failed to create asset in backend', details: errorText },
          { status: backendResponse.status }
        )
      }

      const backendData = await backendResponse.json()
      console.log('Backend asset creation succeeded:', backendData)

      const id = backendData.id

      const asset: Asset = {
        id,
        ...assetPayload,
        assetStatus: backendData.status || assetPayload.assetStatus
      }

      return NextResponse.json({ asset }, { status: 201 })
    } catch (err) {
      console.error('Error connecting to backend for asset creation:', err)
      return NextResponse.json(
        { error: 'Failed to connect to backend for asset creation' },
        { status: 500 }
      )
    }
    
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
