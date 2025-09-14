import { NextRequest, NextResponse } from 'next/server'
import { normalizeFromBackend } from '@/lib/normalizers/asset'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params

  try {
    // Try to fetch from backend first
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
    const backendResponse = await fetch(`${backendUrl}/api/assets/${id}/`)

    if (backendResponse.ok) {
      const data = await backendResponse.json()
      const backendAsset = Array.isArray((data as any)?.rows)
        ? (data as any).rows.find(
            (l: any) => l.id?.toString() === id || l['external_id']?.toString() === id
          )
        : data

      if (backendAsset) {
        // Debug: Log what we're getting from backend
        console.log('Backend asset keys:', Object.keys(backendAsset))
        console.log('Snapshot in backend asset:', !!backendAsset.snapshot)
        
        // Extract data from meta field and merge with asset data
        const meta = backendAsset.meta || {}
        const enrichedAsset = {
          ...backendAsset,
          // Override with data from meta field
          address: backendAsset.normalized_address || backendAsset.address,
          type: meta.type || backendAsset.building_type,
          price: meta.price || backendAsset.price,
          area: meta.area || meta.netSqm || backendAsset.area,
          totalArea: meta.totalSqm || backendAsset.total_area,
          rooms: meta.rooms || meta.bedrooms || backendAsset.rooms,
          bedrooms: meta.bedrooms || backendAsset.bedrooms,
          bathrooms: meta.bathrooms || backendAsset.bathrooms,
          pricePerSqm: meta.pricePerSqm || backendAsset.price_per_sqm,
          rentEstimate: meta.rentEstimate || backendAsset.rent_estimate,
          zoning: meta.zoning || backendAsset.zoning,
          buildingRights: meta.building_rights || backendAsset.building_rights,
          permitStatus: meta.permit_status || backendAsset.permit_status,
          remainingRightsSqm: meta.remainingRightsSqm,
          program: meta.program,
          lastPermitQ: meta.lastPermitQ,
          noiseLevel: meta.noiseLevel,
          competition1km: meta.competition1km,
          priceGapPct: meta.priceGapPct,
          expectedPriceRange: meta.expectedPriceRange,
          modelPrice: meta.modelPrice,
          confidencePct: meta.confidencePct,
          capRatePct: meta.capRatePct,
          riskFlags: meta.riskFlags || [],
          documents: meta.documents || [],
          features: meta.features,
          contactInfo: meta.contactInfo,
          deltaVsAreaPct: meta.deltaVsAreaPct,
          domPercentile: meta.domPercentile,
          antennaDistanceM: meta.antennaDistanceM,
          greenWithin300m: meta.greenWithin300m,
          shelterDistanceM: meta.shelterDistanceM,
          assetStatus: backendAsset.status,
          // Pass through attribution data
          attribution: backendAsset.attribution,
          recent_contributions: backendAsset.recent_contributions,
          // Pass through snapshot data
          snapshot: backendAsset.snapshot,
        }

        const asset: any = normalizeFromBackend(enrichedAsset)

        const backendMeta = backendAsset._meta || backendAsset.meta || {}
        const metaData: Record<string, any> = {}
        for (const [key, value] of Object.entries(backendMeta)) {
          const camel = key.replace(/_([a-z])/g, (_, c) => c.toUpperCase())
          metaData[camel] = value
        }
        asset._meta = metaData

        // Debug: Check if snapshot is in the normalized asset
        console.log('Normalized asset has snapshot:', !!asset.snapshot)
        console.log('Snapshot data:', asset.snapshot)

        return NextResponse.json({ asset })
      }
    }
  } catch (error) {
    console.error('Error fetching asset from backend:', error)
  }

  return new NextResponse('Not found', { status: 404, statusText: 'Not Found' })
}
