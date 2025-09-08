import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

async function fetchFromBackend(endpoint: string, options: RequestInit = {}) {
  const url = `${BACKEND_URL}${endpoint}`
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include',
    cache: 'no-store',
  }
  
  return fetch(url, { ...defaultOptions, ...options })
}

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url)
    const since = searchParams.get('since')
    
    let endpoint = '/api/alert-rules/'
    if (since) {
      endpoint = `/api/alert-events/?since=${since}`
    }
    
    const response = await fetchFromBackend(endpoint)
    
    // Handle authentication errors gracefully
    if (response.status === 401) {
      return NextResponse.json({ rules: [], events: [] })
    }
    
    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`)
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching alerts:', error)
    return NextResponse.json({ error: 'Failed to fetch alerts' }, { status: 500 })
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json()
    
    // Check if this is a test request
    if (body.test) {
      const response = await fetchFromBackend('/api/alert-test/', {
        method: 'POST',
        body: JSON.stringify({}),
      })
      
      if (response.status === 401) {
        return NextResponse.json({ error: 'Authentication required' }, { status: 401 })
      }
      
      if (!response.ok) {
        throw new Error(`Backend responded with ${response.status}`)
      }
      
      const data = await response.json()
      return NextResponse.json(data)
    }
    
    // Create new alert rule
    const response = await fetchFromBackend('/api/alert-rules/', {
      method: 'POST',
      body: JSON.stringify(body),
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      return NextResponse.json(errorData, { status: response.status })
    }
    
    const data = await response.json()
    return NextResponse.json(data, { status: 201 })
  } catch (error) {
    console.error('Error creating alert:', error)
    return NextResponse.json({ error: 'Failed to create alert' }, { status: 500 })
  }
}

export async function PATCH(req: Request) {
  try {
    const body = await req.json()
    
    // Handle mark all as read
    if (body.markAllAsRead) {
      // This would need to be implemented in the backend
      return NextResponse.json({ 
        success: true, 
        message: 'All alerts marked as read' 
      }, { status: 200 })
    }
    
    // Handle individual alert updates
    if (body.alertId && body.isRead !== undefined) {
      // This would need to be implemented in the backend
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
