import { NextResponse } from 'next/server'

// API endpoint to fetch Bank of Israel interest rate
export async function GET() {
  try {
    // In a real implementation, this would scrape or call Bank of Israel API
    // For now, we'll return the current known rate
    const currentRate = 4.75 // As of latest update
    
    return NextResponse.json({
      success: true,
      data: {
        baseRate: currentRate,
        lastUpdated: new Date().toISOString(),
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
