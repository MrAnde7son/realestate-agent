import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { requireAuth } from '@/app/api/_utils/require-auth';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

export async function GET(req: Request) {
  try {
    // Check authentication and redirect if not authenticated
    const authResponse = await requireAuth(req)
    if (authResponse) {
      return authResponse
    }
    
    const cookieStore = await cookies();
    const token = cookieStore.get('access_token')?.value;
    
    const res = await fetch(`${BACKEND_URL}/api/reports`, { 
      cache: 'no-store',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` })
      }
    });
    if (res.ok) {
      const data = await res.json();
      const backendReports = data.reports || [];
      return NextResponse.json({ reports: [...backendReports] });
    }
  } catch (err) {
    console.error('Backend reports fetch failed:', err);
  }
  return NextResponse.json({ reports: [] });
}

export async function DELETE(req: Request) {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get('access_token')?.value;
    
    // Validate token
    const tokenValidation = validateToken(token);
    if (!tokenValidation.isValid) {
      console.log('❌ Reports DELETE API - Token validation failed:', tokenValidation.error);
      const response = NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 });
      response.cookies.delete('access_token');
      response.cookies.delete('refresh_token');
      return response;
    }
    
    // Check if request has a body
    const contentType = req.headers.get('content-type');
    let reportId: number | null = null;
    
    if (contentType && contentType.includes('application/json')) {
      try {
        const body = await req.json();
        reportId = body.reportId;
      } catch (err) {
        console.error('Error parsing JSON body:', err);
        return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
      }
    } else {
      // Try to get reportId from URL params as fallback
      const url = new URL(req.url);
      reportId = url.searchParams.get('reportId') ? parseInt(url.searchParams.get('reportId')!) : null;
    }
    
    if (!reportId) {
      return NextResponse.json({ error: 'reportId required' }, { status: 400 });
    }

    console.log('Attempting to delete report:', reportId);

    // Try to connect to backend first
    try {
      const res = await fetch(`${BACKEND_URL}/api/reports`, {
        method: 'DELETE',
        headers: { 
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` })
        },
        body: JSON.stringify({ reportId }),
      });
      
      console.log('Backend delete response status:', res.status);
      
      if (res.ok) {
        const data = await res.json();
        console.log('Backend delete success:', data);
        return NextResponse.json(data, { status: res.status });
      } else {
        return NextResponse.json({ error: 'Failed to delete report' }, { status: res.status });
      }
    } catch (err) {
      console.error('Error deleting report:', err);
      return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
  } catch (err) {
    console.error('Error deleting report:', err);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
} 

export async function POST(req: Request) {
  let assetId: number;
  let sections: string[] | undefined;
  
  // Parse request first
  try {
    const body = await req.json();
    assetId = Number(body.assetId);
    sections = Array.isArray(body.sections) ? body.sections : undefined;
    
    // Validate assetId
    if (!body.assetId || isNaN(assetId) || assetId <= 0) {
      return NextResponse.json({ error: 'Invalid assetId', details: 'assetId must be a positive number' }, { status: 400 });
    }
    
    console.log('Generating report for assetId:', assetId);
  } catch (err) {
    console.error('Error parsing request:', err);
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    return NextResponse.json({ error: 'Invalid request', details: errorMessage }, { status: 400 });
  }

  // Try to connect to backend first
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get('access_token')?.value;
    console.log('Attempting to connect to backend at:', BACKEND_URL);
    const res = await fetch(`${BACKEND_URL}/api/reports`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` })
      },
      body: JSON.stringify({ assetId, sections }),
    });
    console.log('Backend response status:', res.status);
    if (res.ok) {
      const data = await res.json();
      console.log('Backend response data:', data);
      return NextResponse.json(data, { status: res.status });
    } else {
      console.error('Backend returned error status:', res.status);
      const errorText = await res.text();
      console.error('Backend error response:', errorText);

      // If asset not found in backend, return 404 error
      if (res.status === 404) {
        console.log('Asset not found in backend, falling back to local data');
        return NextResponse.json({
          error: 'Asset not found',
          details: errorText,
          suggestion: 'The asset may not exist in the backend database'
        }, { status: 404 });
      } else {
        // For other backend errors, return the backend error
        return NextResponse.json({
          error: 'Backend report generation failed',
          details: errorText,
          suggestion: 'Please ensure the backend is running for proper Hebrew support'
        }, { status: res.status });
      }
    }
  } catch (err) {
    console.error('Error generating report:', err);
    return NextResponse.json({ error: 'Backend report generation failed', details: err instanceof Error ? err.message : 'Unknown error' }, { status: 500 });
  }
}
