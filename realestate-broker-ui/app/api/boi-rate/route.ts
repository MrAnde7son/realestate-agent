import { NextResponse } from 'next/server'

// API endpoint to fetch Bank of Israel interest rate
export async function GET() {
  try {
    const res = await fetch('https://www.boi.org.il/PublicApi/GetInterest')
    const data = await res.json()

    const currentRate = data?.currentInterest
    const nextDate = data?.nextInterestDate

    if (typeof currentRate !== 'number') {
      throw new Error('Invalid data from Bank of Israel')
    }

    return NextResponse.json({
      success: true,
      data: {
        baseRate: currentRate,
        lastUpdated: nextDate || new Date().toISOString(),
        source: "בנק ישראל",
        scenarios: [
          {
            bank: "בנק לאומי",
            type: "קבוע",
            margin: 1.8,
            totalRate: currentRate + 1.8
          },
          {
            bank: "בנק הפועלים",
            type: "משתנה",
            margin: 1.5,
            totalRate: currentRate + 1.5
          },
          {
            bank: "מזרחי טפחות",
            type: "פריים",
            margin: 1.3,
            totalRate: currentRate + 1.3
          }
        ]
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
