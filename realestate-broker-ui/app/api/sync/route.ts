import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

// Mock data collection simulation
async function collectDataFromSources(address: string) {
  console.log(`Collecting data for address: ${address}`)
  
  // Simulate API calls to different sources
  const mockData = {
    // Yad2 data
    price: Math.floor(Math.random() * 2000000) + 1000000, // 1M - 3M
    bedrooms: Math.floor(Math.random() * 3) + 2, // 2-4 rooms
    bathrooms: Math.floor(Math.random() * 2) + 1, // 1-2 bathrooms
    area: Math.floor(Math.random() * 50) + 60, // 60-110 sqm
    type: 'לא ידוע',
    
    // GIS data
    zoning: 'מגורים א\'',
    buildingRights: '4 קומות + גג',
    landUse: 'מגורים',
    
    // RAMI data
    appraisalValue: Math.floor(Math.random() * 2000000) + 1000000,
    lastAppraisalDate: new Date().toISOString().split('T')[0],
    
    // Government data
    buildingPermits: ['היתר בנייה בתוקף'],
    lastPermitDate: '2024-01-15',
    
    // Calculated fields
    pricePerSqm: 0,
    rentEstimate: 0,
    
    // Metadata
    collectedAt: new Date().toISOString(),
    sources: ['yad2', 'gis', 'rami', 'gov']
  }
  
  // Calculate derived fields
  mockData.pricePerSqm = Math.round(mockData.price / mockData.area)
  mockData.rentEstimate = Math.round(mockData.price * 0.004) // 0.4% monthly
  
  // Simulate processing time
  await new Promise(resolve => setTimeout(resolve, 2000))
  
  return mockData
}

export async function POST(req: Request){
  try {
    const body = await req.json()
    const { address } = body
    
    if (!address) {
      return NextResponse.json({ error: 'כתובת נדרשת' }, { status: 400 })
    }
    
    // Try backend first
    try {
      console.log('Attempting to sync with backend:', `${BACKEND_URL}/api/sync-address/`)
      
      const resp = await fetch(`${BACKEND_URL}/api/sync-address/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address }),
      })
      
      if (resp.ok) {
        const data = await resp.json()
        console.log('Backend sync successful:', data)
        return NextResponse.json(data)
      } else {
        // Backend returned an error status
        const errorText = await resp.text()
        console.log('Backend sync failed with status:', resp.status, 'Error:', errorText)
        
        // Return empty data instead of mock data
        return NextResponse.json({
          success: false,
          message: 'אין מידע זמין עבור הנכס כרגע',
          data: {
            price: 0,
            bedrooms: 0,
            bathrooms: 0,
            area: 0,
            type: 'לא ידוע',
            zoning: '',
            buildingRights: '',
            landUse: '',
            appraisalValue: 0,
            lastAppraisalDate: '',
            buildingPermits: [],
            lastPermitDate: '',
            pricePerSqm: 0,
            rentEstimate: 0,
            collectedAt: new Date().toISOString(),
            sources: []
          },
          sources: []
        })
      }
    } catch (backendError) {
      console.log('Backend connection failed:', backendError)
      
      // Return empty data instead of mock data
      return NextResponse.json({
        success: false,
        message: 'אין מידע זמין עבור הנכס כרגע',
        data: {
          price: 0,
          bedrooms: 0,
          bathrooms: 0,
          area: 0,
          type: 'לא ידוע',
          zoning: '',
          buildingRights: '',
          landUse: '',
          appraisalValue: 0,
          lastAppraisalDate: '',
          buildingPermits: [],
          lastPermitDate: '',
            pricePerSqm: 0,
            rentEstimate: 0,
          collectedAt: new Date().toISOString(),
          sources: []
        },
        sources: []
      })
    }
    
  } catch (error) {
    console.error('Sync error:', error)
    return NextResponse.json({ 
      error: 'שגיאה באיסוף המידע',
      details: error instanceof Error ? error.message : 'שגיאה לא ידועה'
    }, { status: 500 })
  }
}
