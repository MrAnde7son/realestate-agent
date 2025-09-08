import { NextResponse } from 'next/server'
import { alerts } from '@/lib/data'

// In-memory storage for read status (in a real app, this would be in a database)
let readAlerts = new Set<number>()

export async function GET() {
  try {
    // Return alerts with updated read status
    const alertsWithReadStatus = alerts.map(alert => ({
      ...alert,
      isRead: readAlerts.has(alert.id)
    }))
    
    return NextResponse.json({ alerts: alertsWithReadStatus })
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

export async function PATCH(req: Request) {
  try {
    const body = await req.json()
    
    // Handle mark all as read
    if (body.markAllAsRead) {
      // Mark all alerts as read
      alerts.forEach(alert => {
        readAlerts.add(alert.id)
      })
      
      return NextResponse.json({ 
        success: true, 
        message: 'All alerts marked as read' 
      }, { status: 200 })
    }
    
    // Handle individual alert updates
    if (body.alertId && body.isRead !== undefined) {
      if (body.isRead) {
        readAlerts.add(body.alertId)
      } else {
        readAlerts.delete(body.alertId)
      }
      
      return NextResponse.json({ 
        success: true, 
        message: 'Alert marked as read' 
      }, { status: 200 })
    }
    
    return NextResponse.json({ 
      success: true, 
      message: 'Alert updated successfully' 
    }, { status: 200 })
    
  } catch (error) {
    console.error('Error updating alerts:', error)
    return NextResponse.json({ 
      error: 'Failed to update alerts' 
    }, { status: 500 })
  }
}
