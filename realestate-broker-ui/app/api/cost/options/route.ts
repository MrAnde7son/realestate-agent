import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const options = {
      regions: [
        { code: 'CENTER', name: 'מרכז' },
        { code: 'NORTH', name: 'צפון' },
        { code: 'SOUTH', name: 'דרום' },
        { code: 'JERUSALEM', name: 'ירושלים' },
        { code: 'HAIFA', name: 'חיפה' },
        { code: 'BEER_SHEVA', name: 'באר שבע' }
      ],
      qualities: [
        { code: 'basic', name: 'בסיסי' },
        { code: 'standard', name: 'סטנדרטי' },
        { code: 'premium', name: 'פרימיום' },
        { code: 'luxury', name: 'יוקרה' }
      ],
      scopes: [
        { code: 'foundation', name: 'יסודות' },
        { code: 'structure', name: 'מבנה' },
        { code: 'finishing', name: 'גימור' },
        { code: 'electrical', name: 'חשמל' },
        { code: 'plumbing', name: 'אינסטלציה' },
        { code: 'hvac', name: 'מיזוג אוויר' },
        { code: 'kitchen', name: 'מטבח' },
        { code: 'bathroom', name: 'שירותים' },
        { code: 'flooring', name: 'רצפות' },
        { code: 'painting', name: 'צביעה' },
        { code: 'windows', name: 'חלונות' },
        { code: 'doors', name: 'דלתות' },
        { code: 'roofing', name: 'גג' },
        { code: 'insulation', name: 'בידוד' }
      ]
    }
    
    return NextResponse.json(options)
    
  } catch (error) {
    console.error('Cost options error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch cost options' },
      { status: 500 }
    )
  }
}
