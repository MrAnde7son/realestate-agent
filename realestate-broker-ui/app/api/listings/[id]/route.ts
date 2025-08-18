import { NextResponse } from 'next/server'
import { listings } from '@/lib/data'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }){
  const { id } = await params
  
  try {
    // Try to fetch from backend first
    const resp = await fetch(`${BACKEND_URL}/api/listings/`, { cache: 'no-store' })
    
    if (resp.ok) {
      const data = await resp.json()
      const backendListing = data.rows?.find((l: any) => 
        l.id?.toString() === id || l.external_id === id
      )
      
      if (backendListing) {
        // Transform backend data to frontend format
        const listing = {
          id: backendListing.id?.toString() || backendListing.external_id,
          address: backendListing.address,
          price: backendListing.price,
          bedrooms: backendListing.rooms || 3,
          bathrooms: 2, // Default
          area: backendListing.size || 85,
          type: backendListing.property_type || 'דירה',
          status: 'active' as const,
          images: backendListing.images || ['/placeholder-home.jpg'],
          description: backendListing.description || 'תיאור הנכס',
          features: backendListing.features || ['מעלית', 'חניה'],
          contactInfo: backendListing.contact_info || { 
            agent: 'נציג מכירות', 
            phone: '050-1234567', 
            email: 'agent@example.com' 
          },
          city: backendListing.address?.split(',')[1]?.trim() || 'תל אביב',
          neighborhood: 'מרכז העיר',
          netSqm: backendListing.size || 85,
          pricePerSqm: backendListing.price && backendListing.size ? 
            Math.round(backendListing.price / backendListing.size) : 29412,
          deltaVsAreaPct: 2.5,
          domPercentile: 75,
          competition1km: 'בינוני',
          zoning: 'מגורים א\'',
          riskFlags: [],
          priceGapPct: -5.2,
          expectedPriceRange: backendListing.price ? 
            `${(backendListing.price * 0.9 / 1000000).toFixed(1)}M - ${(backendListing.price * 1.1 / 1000000).toFixed(1)}M` : 
            '2.7M - 3.0M',
          remainingRightsSqm: 45,
          program: 'תמ״א 38',
          lastPermitQ: 'Q2/24',
          noiseLevel: 2,
          greenWithin300m: true,
          schoolsWithin500m: true,
          modelPrice: backendListing.price || 3000000,
          confidencePct: 85,
          capRatePct: 3.2,
          antennaDistanceM: 150,
          shelterDistanceM: 80,
          rentEstimate: backendListing.price ? Math.round(backendListing.price * 0.004) : 9500
        }
        
        return NextResponse.json({ listing })
      }
    }
  } catch (error) {
    console.error('Error fetching listing from backend:', error)
  }
  
  // Fallback to mock data
  const listing = listings.find(l => l.id === id)
  if(!listing) return new NextResponse('Not found', { status: 404 })
  return NextResponse.json({ listing })
}
