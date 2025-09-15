import { NextResponse } from 'next/server'
import { fetchVATRate } from '@/lib/purchase-tax'

export async function GET() {
  try {
    const data = await fetchVATRate()
    return NextResponse.json({ success: true, data })
  } catch (error) {
    console.error('Error fetching VAT rate:', error)
    return NextResponse.json({ success: false, error: 'Failed to fetch VAT rate' }, { status: 500 })
  }
}
