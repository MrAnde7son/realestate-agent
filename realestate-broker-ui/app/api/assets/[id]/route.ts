import { NextRequest, NextResponse } from 'next/server'
import { assets } from '@/lib/data'

function determineAssetType(asset: any): string {
  return asset?.propertyType || asset?.property_type || asset?.type || 'לא ידוע'
}

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params

  try {
    // Try to fetch from backend first
    const backendResponse = await fetch(`${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/api/assets/${id}`)
    
    if (backendResponse.ok) {
      const data = await backendResponse.json()
      const backendAsset = data.rows?.find((l: any) =>
        l.id?.toString() === id || l['external_id']?.toString() === id
      )

      if (backendAsset) {
        const asset = {
          id: Number(backendAsset.id ?? backendAsset['external_id']),
          address: backendAsset.address,
          price: backendAsset.price,
          bedrooms: backendAsset.rooms || 3,
          bathrooms: backendAsset.bathrooms || 2,
          area: backendAsset.size || 85,
          type: determineAssetType(backendAsset),
          status: 'active',
          images: backendAsset.images || ['/placeholder-home.jpg'],
          description: backendAsset.description || 'תיאור הנכס',
          features: backendAsset.features || ['מעלית', 'חניה'],
          contactInfo: backendAsset['contact_info'] || {
            name: 'משרד תיווך',
            phone: '03-1234567',
            email: 'info@broker.co.il'
          },
          // Additional fields for detailed view
          city: backendAsset.address?.split(',')[1]?.trim() || 'תל אביב',
          neighborhood: backendAsset.address?.split(',')[2]?.trim() || 'מרכז העיר',
          netSqm: backendAsset.size || 85,
          pricePerSqmDisplay: backendAsset.price && backendAsset.size ?
            Math.round(backendAsset.price / backendAsset.size) : 29412,
          // Financial analysis
          expectedPriceRange: backendAsset.price ?
            `${(backendAsset.price * 0.9 / 1000000).toFixed(1)}M - ${(backendAsset.price * 1.1 / 1000000).toFixed(1)}M` :
            '₪2.7M - ₪3.3M',
          confidencePct: 85,
          capRatePct: 3.2,
          priceGapPct: -5.2,
          competition1km: 12,
          // Rights and permits
          remainingRightsSqm: 45,
          zoning: 'מגורים',
          program: 'תכנית מפורטת 5000',
          lastPermitQ: 'Q4/23',
          // Environmental factors
          noiseLevel: 2,
          greenWithin300m: true,
          antennaDistanceM: 150,
          riskFlags: ['שימור מבנה'],
          // Model and estimates
          modelPrice: backendAsset.price || 3000000,
          rentEstimate: backendAsset.price ? Math.round(backendAsset.price * 0.004) : 9500,
          permitDateDisplay: backendAsset['permit_date'],
          permitStatusDisplay: backendAsset['permit_status'],
          permitDetails: backendAsset['permit_details'],
          permitMainArea: backendAsset['permit_main_area'],
          permitServiceArea: backendAsset['permit_service_area'],
          permitApplicant: backendAsset['permit_applicant'],
          permitDocUrl: backendAsset['permit_doc_url'],
          mainRightsSqm: backendAsset['main_rights_sqm'],
          serviceRightsSqm: backendAsset['service_rights_sqm'],
          additionalPlanRights: backendAsset['additional_plan_rights'],
          planStatus: backendAsset['plan_status'],
          publicObligations: backendAsset['public_obligations'],
          publicTransport: backendAsset['public_transport'],
          openSpacesNearby: backendAsset['open_spaces_nearby'],
          publicBuildings: backendAsset['public_buildings'],
          parking: backendAsset.parking,
          nearbyProjects: backendAsset['nearby_projects'],
          rightsUsagePct: backendAsset['rights_usage_pct'],
          legalRestrictions: backendAsset['legal_restrictions'],
          urbanRenewalPotential: backendAsset['urban_renewal_potential'],
          bettermentLevy: backendAsset['betterment_levy']
        }

        return NextResponse.json({ asset })
      }
    }
  } catch (error) {
    console.error('Error fetching asset from backend:', error)
  }

  // Fallback to mock data
  const asset = assets.find(l => l.id === Number(id))
  if(!asset) return new NextResponse('Not found', { status: 404, statusText: 'Not Found' })
  return NextResponse.json({ asset })
}
