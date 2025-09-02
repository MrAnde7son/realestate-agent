import { NextResponse } from 'next/server'
import { alerts } from '@/lib/data'

export async function GET() {
  try {
    // Return mock alerts data in the format expected by dashboard
    return NextResponse.json({ alerts })
  } catch (error) {
    console.error('Error fetching alerts:', error)
    return NextResponse.json({ error: 'Failed to fetch alerts' }, { status: 500 })
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json()
    
    // Mock response for creating/updating alerts
    return NextResponse.json({ 
      success: true, 
      message: 'Alert updated successfully' 
    }, { status: 200 })
    
  } catch (error) {
    console.error('Error updating alert:', error)
    return NextResponse.json({ 
      error: 'Failed to update alert' 
    }, { status: 500 })
  }
}
