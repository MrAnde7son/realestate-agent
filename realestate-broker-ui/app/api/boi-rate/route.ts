import { NextResponse } from 'next/server'
import { fetchBOIRate, getMortgageScenarios } from '@/lib/mortgage'

// API endpoint to fetch Bank of Israel interest rate
export async function GET() {
  try {
    const { baseRate, lastUpdated } = await fetchBOIRate()

    return NextResponse.json({
      success: true,
      data: {
        baseRate,
        lastUpdated,
        source: 'בנק ישראל',
        scenarios: getMortgageScenarios(baseRate)
      }
    })
  } catch (error) {
    console.error('Error fetching BOI rate:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to fetch interest rate' },
      { status: 500 }
    )
  }
}
