import { NextResponse } from 'next/server'
import { appraisalByListing } from '@/lib/data'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  
  try {
    // Try to fetch from backend
    const resp = await fetch(`${BACKEND_URL}/api/decisive-appraisals/`, { cache: 'no-store' })
    
    if (resp.ok) {
      const data = await resp.json()
      
      if (data.rows && data.rows.length > 0) {
        // Use the most recent appraisal
        const appraisal = data.rows[0]
        
        return NextResponse.json({
          listingId: id,
          marketValue: 2850000, // Could be derived from appraisal data
          appraisedValue: 2800000,
          date: appraisal.date || "2024-01-15",
          appraiser: appraisal.appraiser || "שמואל דוד",
          notes: appraisal.title || "הערכה בהתבסס על נתוני שוק עדכניים",
          pdf_url: appraisal.pdf_url
        })
      }
    }
  } catch (error) {
    console.error('Error fetching appraisal from backend:', error)
  }
  
  // Fallback to mock data
  return NextResponse.json(appraisalByListing(id))
}