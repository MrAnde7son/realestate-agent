import { NextResponse } from 'next/server'
import { assets, addAsset, deleteAsset } from '@/lib/data'
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
  radius: z.number().default(100)
})

function determineAssetType(asset: any): string {
  return asset?.type || asset?.property_type || asset?.propertyType || 'לא ידוע'
}

export async function GET() {
  try {
    // Return mock data for now
    const transformedRows = assets.map((asset: any) => ({
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
      contact_info: asset.contact_info || { agent: '', phone: '', email: '' },
      city: asset.city || 'תל אביב',
      neighborhood: asset.neighborhood || '',
      net_sqm: asset.net_sqm || 0,
      price_per_sqm_display: asset.price_per_sqm_display || 0,
      delta_vs_area_pct: asset.delta_vs_area_pct || 0, // Calculate if needed
      dom_percentile: asset.dom_percentile || 50, // Default
      competition_1km: asset.competition_1km || 'בינוני',
      zoning: asset.zoning || 'מגורים א\'',
      risk_flags: asset.risk_flags || [],
      price_gap_pct: asset.price_gap_pct || 0,
      expected_price_range: asset.expected_price_range || '',
      remaining_rights_sqm: asset.remaining_rights_sqm || 0,
      program: asset.program || '',
      last_permit_q: asset.last_permit_q || '',
      noise_level: asset.noise_level || 2,
      green_within_300m: asset.green_within_300m || true,
      schools_within_500m: asset.schools_within_500m || true,
      model_price: asset.model_price || 0,
      confidence_pct: asset.confidence_pct || 75, // Default
      cap_rate_pct: asset.cap_rate_pct || 3.0,
      antenna_distance_m: asset.antenna_distance_m || 150,
      shelter_distance_m: asset.shelter_distance_m || 100,
      rent_estimate: asset.rent_estimate || 0,
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

    const id = Date.now() // Generate unique numeric ID once

    // Create asset with available data, using defaults for missing fields
    const asset: Asset = {
      id,
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
      contact_info: {
        agent: '',
        phone: '',
        email: ''
      },
      city: derivedCity,
      neighborhood: '',
      net_sqm: 0,
      price_per_sqm_display: 0,
      delta_vs_area_pct: 0,
      dom_percentile: 50,
      competition_1km: 'בינוני',
      zoning: 'מגורים א\'',
      risk_flags: [],
      price_gap_pct: 0,
      expected_price_range: '',
      remaining_rights_sqm: 0,
      program: '',
      last_permit_q: '',
      noise_level: 2,
      green_within_300m: true,
      schools_within_500m: true,
      model_price: 0,
      confidence_pct: 75,
      cap_rate_pct: 3.0,
      antenna_distance_m: 150,
      shelter_distance_m: 100,
      rent_estimate: 0,
      asset_id: id,
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
