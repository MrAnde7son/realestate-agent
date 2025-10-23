import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(req: Request){
  try {
    const body = await req.json()
    const { address } = body
    
    if (!address) {
      return NextResponse.json({ error: 'כתובת נדרשת' }, { status: 400 })
    }
    
    try {
      const resp = await fetch(`${BACKEND_URL}/api/sync-address`, {
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
