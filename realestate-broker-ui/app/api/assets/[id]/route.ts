import { NextRequest, NextResponse } from 'next/server'
import { normalizeFromBackend } from '@/lib/normalizers/asset'
import { getMockAsset } from '@/lib/mock-assets'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params

  try {
    // Try to fetch from backend first
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
    const backendResponse = await fetch(`${backendUrl}/api/assets/${id}`)

    if (backendResponse.ok) {
      const data = await backendResponse.json()
      const backendAsset = Array.isArray((data as any)?.rows)
        ? (data as any).rows.find(
            (l: any) => l.id?.toString() === id || l['external_id']?.toString() === id
          )
        : data

      if (backendAsset) {
        const asset: any = normalizeFromBackend(backendAsset)

        const backendMeta = backendAsset._meta || backendAsset.meta || {}
        const meta: Record<string, any> = {}
        for (const [key, value] of Object.entries(backendMeta)) {
          const camel = key.replace(/_([a-z])/g, (_, c) => c.toUpperCase())
          meta[camel] = value
        }
        asset._meta = meta

        return NextResponse.json({ asset })
      }
    }
  } catch (error) {
    console.error('Error fetching asset from backend:', error)
  }

  const localAsset = getMockAsset(Number(id))
  if (localAsset) {
    return NextResponse.json({ asset: localAsset })
  }

  return new NextResponse('Not found', { status: 404, statusText: 'Not Found' })
}
