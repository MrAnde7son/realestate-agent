import { NextResponse } from 'next/server'
import { rightsByListing } from '@/lib/data'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  
  try {
    // Try to fetch from backend
    const resp = await fetch(`${BACKEND_URL}/api/building-rights/`, { cache: 'no-store' })
    
    if (resp.ok) {
      const data = await resp.json()
      
      if (data.rows && data.rows.length > 0) {
        // Use the most recent building rights record
        const rights = data.rows[0]
        
        return NextResponse.json({
          listingId: id,
          buildingRights: rights.data?.buildingRights || "זכויות בנייה: 4 קומות + גג",
          landUse: "מגורים א'",
          restrictions: rights.data?.restrictions || ["איסור שינוי יעוד", "חובת שמירה על חזית היסטורית"],
          permits: ["היתר בנייה בתוקף", "היתר עסק למשרד"],
          lastUpdate: rights.scraped_at ? new Date(rights.scraped_at).toISOString().split('T')[0] : "2024-01-20",
          gush: rights.gush,
          helka: rights.helka,
          file_path: rights.file_path
        })
      }
    }
  } catch (error) {
    console.error('Error fetching rights from backend:', error)
  }
  
  // Fallback to mock data
  return NextResponse.json(rightsByListing(id))
}