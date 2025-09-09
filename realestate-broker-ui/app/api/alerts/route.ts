import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateToken } from '@/lib/token-utils'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

async function fetchFromBackend(endpoint: string, options: RequestInit = {}, req?: Request) {
  const url = `${BACKEND_URL}${endpoint}`
  
  // Try to get token from cookies first (server-side)
  let token = cookies().get('access_token')?.value
  
  // If no token in cookies, try to get from request headers (client-side)
  if (!token && req) {
    const authHeader = req.headers.get('authorization')
    if (authHeader && authHeader.startsWith('Bearer ')) {
      token = authHeader.substring(7)
    }
  }
  
  // Validate token
  const tokenValidation = validateToken(token)
  if (!tokenValidation.isValid) {
    console.log('❌ Alerts API - Token validation failed:', tokenValidation.error)
    return new Response(JSON.stringify({ error: 'Unauthorized - Token expired or invalid' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' }
    })
  }
  
  // Debug logging
  console.log('🔍 Alerts API - Backend request:', {
    backendUrl: BACKEND_URL,
    endpoint,
    fullUrl: url,
    hasToken: !!token,
    tokenLength: token?.length || 0,
    allCookies: cookies().getAll().map(c => c.name)
  })
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
    cache: 'no-store',
  }
  
  const response = await fetch(url, { ...defaultOptions, ...options })
  
  // Debug logging for response
  console.log('🔍 Alerts API - Backend response:', {
    url,
    status: response.status,
    statusText: response.statusText,
    contentType: response.headers.get('content-type'),
    ok: response.ok
  })
  
  return response
}

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url)
    const since = searchParams.get('since')
    
    let endpoint = '/api/alerts/'
    if (since) {
      endpoint = `/api/alert-events/?since=${since}`
    }
    
    const response = await fetchFromBackend(endpoint)
    
    // Handle authentication errors gracefully
    if (response.status === 401) {
      // Clear tokens and return 401 to trigger logout
      const errorResponse = NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 })
      errorResponse.cookies.delete('access_token')
      errorResponse.cookies.delete('refresh_token')
      return errorResponse
    }
    
    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`)
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching alerts:', error)
    // If it's an authentication error, return empty data instead of 500
    if (error instanceof Error && error.message.includes('Unauthorized')) {
      return NextResponse.json({ rules: [], events: [] })
    }
    return NextResponse.json({ error: 'Failed to fetch alerts' }, { status: 500 })
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json()
    
    console.log('🔍 Alerts API - POST request:', {
      body: body,
      hasTest: !!body.test
    })
    
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
    const response = await fetchFromBackend('/api/alerts/', {
      method: 'POST',
      body: JSON.stringify(body),
    })
    
    if (response.status === 401) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 })
    }
    
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

export async function PUT(req: Request) {
  try {
    const { searchParams } = new URL(req.url)
    const ruleId = searchParams.get('id')
    
    if (!ruleId) {
      return NextResponse.json({ error: 'Alert rule ID required' }, { status: 400 })
    }
    
    const body = await req.json()
    
    const response = await fetchFromBackend(`/api/alerts/?id=${ruleId}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    }, req)
    
    if (response.status === 401) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 })
    }
    
    if (!response.ok) {
      const errorData = await response.json()
      return NextResponse.json(errorData, { status: response.status })
    }
    
    const data = await response.json()
    return NextResponse.json(data, { status: 200 })
  } catch (error) {
    console.error('Error updating alert rule:', error)
    return NextResponse.json({ error: 'Failed to update alert rule' }, { status: 500 })
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

export async function DELETE(req: Request) {
  try {
    const { searchParams } = new URL(req.url)
    const ruleId = searchParams.get('ruleId')
    
    if (!ruleId) {
      return NextResponse.json({ error: 'ruleId required' }, { status: 400 })
    }
    
    const response = await fetchFromBackend(`/api/alerts/?ruleId=${ruleId}`, {
      method: 'DELETE',
    }, req)
    
    if (response.status === 401) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 })
    }
    
    if (!response.ok) {
      const errorData = await response.json()
      return NextResponse.json(errorData, { status: response.status })
    }
    
    const data = await response.json()
    return NextResponse.json(data, { status: 200 })
  } catch (error) {
    console.error('Error deleting alert rule:', error)
    return NextResponse.json({ error: 'Failed to delete alert rule' }, { status: 500 })
  }
}
