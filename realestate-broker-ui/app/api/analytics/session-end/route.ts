import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Forward to Django backend
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/analytics/session-end/`, {
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
    console.error('Analytics session end error:', error);
    return NextResponse.json(
      { error: 'Failed to track session end' },
      { status: 500 }
    );
  }
}
