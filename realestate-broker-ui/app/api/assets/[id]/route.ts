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
    const backendResponse = await fetch(`${backendUrl}/api/assets/${id}/`)

    if (backendResponse.ok) {
      const data = await backendResponse.json()
      console.log('Backend response block/parcel:', { block: data.block, parcel: data.parcel, subparcel: data.subparcel })
      
      const backendAsset = Array.isArray((data as any)?.rows)
        ? (data as any).rows.find(
            (l: any) => l.id?.toString() === id || l['external_id']?.toString() === id
          )
        : data

      if (backendAsset) {
        console.log('Backend asset block/parcel:', { block: backendAsset.block, parcel: backendAsset.parcel, subparcel: backendAsset.subparcel })
        
        // The backend now provides unified structure with _meta already populated
        const asset: any = normalizeFromBackend(backendAsset)
        
        console.log('Normalized asset block/parcel:', { block: asset.block, parcel: asset.parcel, subparcel: asset.subparcel })

        return NextResponse.json({ asset })
      }
    }
  } catch (error) {
    console.error('Error fetching asset from backend:', error)
  }

  return new NextResponse('Not found', { status: 404, statusText: 'Not Found' })
}
