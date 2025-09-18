import { NextRequest, NextResponse } from 'next/server'
import { normalizeFromBackend } from '@/lib/normalizers/asset'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params

  try {
    // Try to fetch from backend first
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
    console.log('Fetching from:', `${backendUrl}/api/assets/${id}/`)
    const backendResponse = await fetch(`${backendUrl}/api/assets/${id}/`)

    if (backendResponse.ok) {
      const data = await backendResponse.json()
      const backendAsset = Array.isArray((data as any)?.rows)
        ? (data as any).rows.find(
            (l: any) => l.id?.toString() === id || l['external_id']?.toString() === id
          )
        : data

      if (backendAsset) {
        // Debug: Log what we're getting from backend
        console.log('Backend asset keys:', Object.keys(backendAsset))
        console.log('Snapshot in backend asset:', !!backendAsset.snapshot)
        console.log('Documents in backend asset:', backendAsset.documents?.length || 0)
        if (backendAsset.documents) {
          console.log('First document:', backendAsset.documents[0])
        } else {
          console.log('No documents in backend asset')
        }
        
        // The backend now provides unified structure with _meta already populated
        const asset: any = normalizeFromBackend(backendAsset)

        // Debug: Check if snapshot is in the normalized asset
        console.log('Normalized asset has snapshot:', !!asset.snapshot)
        console.log('Snapshot data:', asset.snapshot)
        console.log('Documents in normalized asset:', asset.documents?.length || 0)

        return NextResponse.json({ asset })
      }
    }
  } catch (error) {
    console.error('Error fetching asset from backend:', error)
  }

  return new NextResponse('Not found', { status: 404, statusText: 'Not Found' })
}
