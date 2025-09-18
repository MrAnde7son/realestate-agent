import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params
    const body = await request.json()
    
    if (!id) {
      return NextResponse.json({ error: 'מזהה נכס נדרש' }, { status: 400 })
    }
    
    // Call the backend sync endpoint
    try {
      console.log(`Syncing asset ${id} with backend: ${BACKEND_URL}/api/assets/${id}/sync/`)
      
      // Get authentication token from cookies
      const token = cookies().get('access_token')?.value
      
      const resp = await fetch(`${BACKEND_URL}/api/assets/${id}/sync/`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` })
        },
        body: JSON.stringify(body),
      })
      
      if (resp.ok) {
        const data = await resp.json()
        console.log('Backend asset sync successful:', data)
        return NextResponse.json(data)
      } else {
        // Backend returned an error status
        const errorText = await resp.text()
        console.log('Backend asset sync failed with status:', resp.status, 'Error:', errorText)
        
        let errorData
        try {
          errorData = JSON.parse(errorText)
        } catch {
          errorData = { error: errorText }
        }
        
        return NextResponse.json({
          error: errorData.error || 'שגיאה בסנכרון נתוני הנכס',
          details: errorData.details || errorData.message
        }, { status: resp.status })
      }
    } catch (backendError) {
      console.log('Backend connection failed:', backendError)
      
      return NextResponse.json({
        error: 'שגיאה בחיבור לשירות השרת',
        details: backendError instanceof Error ? backendError.message : 'שגיאה לא ידועה'
      }, { status: 503 })
    }
    
  } catch (error) {
    console.error('Asset sync error:', error)
    return NextResponse.json({ 
      error: 'שגיאת שרת פנימית',
      details: error instanceof Error ? error.message : 'שגיאה לא ידועה'
    }, { status: 500 })
  }
}
