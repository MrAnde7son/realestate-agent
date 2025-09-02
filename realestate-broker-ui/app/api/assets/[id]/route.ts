import { NextRequest, NextResponse } from 'next/server'
import { assets } from '@/lib/data'

function determineAssetType(asset: any): string {
  return asset?.type || asset?.property_type || asset?.propertyType || 'לא ידוע'
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
        l.id?.toString() === id || l.external_id?.toString() === id
      )

      if (backendAsset) {
        const asset = {
          id: Number(backendAsset.id ?? backendAsset.external_id),
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
          contact_info: backendAsset.contact_info || {
            name: 'משרד תיווך',
            phone: '03-1234567',
            email: 'info@broker.co.il'
          },
          // Additional fields for detailed view
          city: backendAsset.address?.split(',')[1]?.trim() || 'תל אביב',
          neighborhood: backendAsset.address?.split(',')[2]?.trim() || 'מרכז העיר',
          net_sqm: backendAsset.size || 85,
          price_per_sqm_display: backendAsset.price && backendAsset.size ?
            Math.round(backendAsset.price / backendAsset.size) : 29412,
          // Financial analysis
          expected_price_range: backendAsset.price ?
            `${(backendAsset.price * 0.9 / 1000000).toFixed(1)}M - ${(backendAsset.price * 1.1 / 1000000).toFixed(1)}M` :
            '₪2.7M - ₪3.3M',
          confidence_pct: 85,
          cap_rate_pct: 3.2,
          price_gap_pct: -5.2,
          competition_1km: 12,
          // Rights and permits
          remaining_rights_sqm: 45,
          zoning: 'מגורים',
          program: 'תכנית מפורטת 5000',
          last_permit_q: 'Q4/23',
          // Environmental factors
          noise_level: 2,
          green_within_300m: true,
          antenna_distance_m: 150,
          risk_flags: ['שימור מבנה'],
          // Model and estimates
          model_price: backendAsset.price || 3000000,
          rent_estimate: backendAsset.price ? Math.round(backendAsset.price * 0.004) : 9500,
          permit_date_display: backendAsset.permit_date,
          permit_status_display: backendAsset.permit_status,
          permit_details: backendAsset.permit_details,
          permit_main_area: backendAsset.permit_main_area,
          permit_service_area: backendAsset.permit_service_area,
          permit_applicant: backendAsset.permit_applicant,
          permit_doc_url: backendAsset.permit_doc_url,
          main_rights_sqm: backendAsset.main_rights_sqm,
          service_rights_sqm: backendAsset.service_rights_sqm,
          additional_plan_rights: backendAsset.additional_plan_rights,
          plan_status: backendAsset.plan_status,
          public_obligations: backendAsset.public_obligations,
          public_transport: backendAsset.public_transport,
          open_spaces_nearby: backendAsset.open_spaces_nearby,
          public_buildings: backendAsset.public_buildings,
          parking: backendAsset.parking,
          nearby_projects: backendAsset.nearby_projects,
          rights_usage_pct: backendAsset.rights_usage_pct,
          legal_restrictions: backendAsset.legal_restrictions,
          urban_renewal_potential: backendAsset.urban_renewal_potential,
          betterment_levy: backendAsset.betterment_levy
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
