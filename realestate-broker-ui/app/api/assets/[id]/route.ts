import { NextRequest, NextResponse } from 'next/server'
import { assets } from '@/lib/data'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params

  try {
    // Try to fetch from backend first
    const backendResponse = await fetch(`${process.env.BACKEND_URL || 'http://localhost:8000'}/api/assets/${id}`)
    
    if (backendResponse.ok) {
      const data = await backendResponse.json()
      const backendAsset = data.rows?.find((l: any) =>
        l.id?.toString() === id || l.external_id === id
      )

      if (backendAsset) {
        const asset = {
          id: backendAsset.id?.toString() || backendAsset.external_id,
          address: backendAsset.address,
          price: backendAsset.price,
          bedrooms: backendAsset.rooms || 3,
          bathrooms: backendAsset.bathrooms || 2,
          area: backendAsset.size || 85,
          type: backendAsset.property_type || 'דירה',
          status: 'active',
          images: backendAsset.images || ['/placeholder-home.jpg'],
          description: backendAsset.description || 'תיאור הנכס',
          features: backendAsset.features || ['מעלית', 'חניה'],
          contactInfo: backendAsset.contact_info || {
            name: 'משרד תיווך',
            phone: '03-1234567',
            email: 'info@broker.co.il'
          },
          // Additional fields for detailed view
          city: backendAsset.address?.split(',')[1]?.trim() || 'תל אביב',
          neighborhood: backendAsset.address?.split(',')[2]?.trim() || 'מרכז העיר',
          netSqm: backendAsset.size || 85,
          pricePerSqm: backendAsset.price && backendAsset.size ?
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
          rentEstimate: backendAsset.price ? Math.round(backendAsset.price * 0.004) : 9500
        }

        return NextResponse.json({ asset })
      }
    }
  } catch (error) {
    console.error('Error fetching asset from backend:', error)
  }

  // Fallback to mock data
  const asset = assets.find(l => l.id === id)
  if(!asset) return new NextResponse('Not found', { status: 404 })
  return NextResponse.json({ asset })
}
