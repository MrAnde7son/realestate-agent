import { NextResponse } from 'next/server'
import { fetchVatRate } from '@/lib/vat'

export async function GET() {
  try {
    const data = await fetchVatRate()
    return NextResponse.json({ success: true, data })
  } catch (e) {
    return NextResponse.json({ success: false, error: 'Failed to fetch VAT' }, { status: 500 })
  }
}
