import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // Check if request has a body
    const contentLength = request.headers.get('content-length');
    if (!contentLength || contentLength === '0') {
      console.warn('Analytics page view: Empty request body');
      return NextResponse.json(
        { error: 'Empty request body' },
        { status: 400 }
      );
    }

    // Try to parse JSON with error handling
    let body;
    try {
      body = await request.json();
    } catch (jsonError) {
      console.error('Analytics page view: Invalid JSON:', jsonError);
      return NextResponse.json(
        { error: 'Invalid JSON in request body' },
        { status: 400 }
      );
    }

    // Validate that body is not empty
    if (!body || Object.keys(body).length === 0) {
      console.warn('Analytics page view: Empty JSON body');
      return NextResponse.json(
        { error: 'Empty JSON body' },
        { status: 400 }
      );
    }
    
    // Forward to Django backend
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
    const response = await fetch(`${backendUrl}/api/analytics/page-view`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': request.headers.get('authorization') || '',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Analytics page view error:', error);
    return NextResponse.json(
      { error: 'Failed to track page view' },
      { status: 500 }
    );
  }
}
