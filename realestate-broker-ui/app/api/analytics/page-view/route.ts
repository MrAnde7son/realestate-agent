import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // Check if request has a body
    const contentLength = request.headers.get('content-length');
    if (!contentLength || contentLength === '0') {
      console.warn('Analytics page view: Empty request body');
      return NextResponse.json({ success: true });
    }

    // Try to parse JSON with error handling
    let body;
    try {
      const text = await request.text();
      if (!text.trim()) {
        console.warn('Analytics page view: Empty request body text');
        return NextResponse.json({ success: true });
      }
      body = JSON.parse(text);
    } catch (jsonError) {
      console.error('Analytics page view: Invalid JSON:', jsonError);
      return NextResponse.json({ success: true }); // Return success instead of error to avoid breaking the app
    }

    // Validate that body is not empty
    if (!body || Object.keys(body).length === 0) {
      console.warn('Analytics page view: Empty JSON body');
      return NextResponse.json({ success: true });
    }
    
    // Forward to Django backend (only if backend is available)
    try {
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
        console.warn(`Backend analytics responded with ${response.status}`);
        return NextResponse.json({ success: true }); // Don't fail the request
      }

      const data = await response.json();
      return NextResponse.json(data);
    } catch (backendError) {
      console.warn('Backend analytics not available:', backendError);
      return NextResponse.json({ success: true }); // Don't fail the request
    }
  } catch (error) {
    console.error('Analytics page view error:', error);
    return NextResponse.json({ success: true }); // Don't fail the request
  }
}
