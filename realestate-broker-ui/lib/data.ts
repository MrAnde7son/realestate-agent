export interface Listing {
  id: string
  address: string
  price: number
  bedrooms: number
  bathrooms: number
  area: number
  type: string
  status: "active" | "pending" | "sold"
  images: string[]
  description: string
  features: string[]
  contactInfo: {
    agent: string
    phone: string
    email: string
  }
  // Additional properties for table display
  city?: string
  neighborhood?: string
  netSqm?: number
  pricePerSqm?: number
  deltaVsAreaPct?: number
  domPercentile?: number
  competition1km?: string
  zoning?: string
  riskFlags?: string[]
  priceGapPct?: number
  expectedPriceRange?: string
  remainingRightsSqm?: number
  program?: string
  lastPermitQ?: string
  noiseLevel?: number
  greenWithin300m?: boolean
  schoolsWithin500m?: boolean
  modelPrice?: number
  confidencePct?: number
  capRatePct?: number
  antennaDistanceM?: number
  shelterDistanceM?: number
  rentEstimate?: number
}

export const listings: Listing[] = [
  {
    id: "l1",
    address: "רחוב הרצל 123, תל אביב",
    price: 2850000,
    bedrooms: 3,
    bathrooms: 2,
    area: 85,
    type: "דירה",
    status: "active",
    images: ["/placeholder-home.jpg"],
    description: "דירה מקסימה במרכז תל אביב עם נוף לים",
    features: ["מעלית", "חניה", "מרפסת", "משופצת"],
    contactInfo: {
      agent: "יוסי כהן",
      phone: "050-1234567",
      email: "yossi@example.com"
    },
    city: "תל אביב",
    neighborhood: "מרכז העיר",
    netSqm: 85,
    pricePerSqm: 33529,
    deltaVsAreaPct: 2.5,
    domPercentile: 75,
    competition1km: "בינוני",
    zoning: "מגורים א'",
    riskFlags: [],
    priceGapPct: -5.2,
    expectedPriceRange: "2.7M - 3.0M",
    remainingRightsSqm: 45,
    program: "תמ״א 38",
    lastPermitQ: "Q2/24",
    noiseLevel: 2,
    greenWithin300m: true,
    schoolsWithin500m: true,
    modelPrice: 3000000,
    confidencePct: 85,
    capRatePct: 3.2,
    antennaDistanceM: 150,
    shelterDistanceM: 80,
    rentEstimate: 9500
  },
  {
    id: "l2",
    address: "שדרות רוטשילד 45, תל אביב",
    price: 4200000,
    bedrooms: 4,
    bathrooms: 3,
    area: 120,
    type: "דירה",
    status: "pending",
    images: ["/placeholder-home.jpg"],
    description: "דירת פנטהאוס מפוארת עם מרפסת גדולה",
    features: ["מעלית", "חניה", "מרפסת גדולה", "חדר עבודה"],
    contactInfo: {
      agent: "דנה לוי",
      phone: "052-7654321",
      email: "dana@example.com"
    },
    city: "תל אביב",
    neighborhood: "רוטשילד",
    netSqm: 120,
    pricePerSqm: 35000,
    deltaVsAreaPct: 8.3,
    domPercentile: 90,
    competition1km: "גבוה",
    zoning: "מגורים א' מיוחד",
    riskFlags: ["אנטנה סלולרית"],
    priceGapPct: 12.1,
    expectedPriceRange: "3.8M - 4.3M",
    remainingRightsSqm: 80,
    program: "פינוי בינוי",
    lastPermitQ: "Q1/24",
    noiseLevel: 4,
    greenWithin300m: false,
    schoolsWithin500m: true,
    modelPrice: 3750000,
    confidencePct: 92,
    capRatePct: 2.8,
    antennaDistanceM: 80,
    shelterDistanceM: 120,
    rentEstimate: 12000
  }
]

// Mock data functions for API routes
export function appraisalByListing(id: string) {
  return {
    listingId: id,
    marketValue: 2850000,
    appraisedValue: 2800000,
    date: "2024-01-15",
    appraiser: "שמואל דוד",
    notes: "הערכה בהתבסס על נתוני שוק עדכניים"
  }
}

export function compsByListing(id: string) {
  return [
    {
      address: "רחוב בן יהודה 45, תל אביב",
      price: 2750000,
      area: 80,
      pricePerSqm: 34375,
      date: "2024-01-10"
    },
    {
      address: "רחוב דיזנגוף 67, תל אביב", 
      price: 2900000,
      area: 90,
      pricePerSqm: 32222,
      date: "2024-01-05"
    }
  ]
}

export function rightsByListing(id: string) {
  return {
    listingId: id,
    buildingRights: "זכויות בנייה: 4 קומות + גג",
    landUse: "מגורים א'",
    restrictions: ["איסור שינוי יעוד", "חובת שמירה על חזית היסטורית"],
    permits: ["היתר בנייה בתוקף", "היתר עסק למשרד"],
    lastUpdate: "2024-01-20"
  }
}

// Alerts/Notifications data
export interface Alert {
  id: string
  type: 'price_drop' | 'new_listing' | 'market_change' | 'document_update' | 'permit_status'
  title: string
  message: string
  listingId?: string
  listingAddress?: string
  priority: 'high' | 'medium' | 'low'
  isRead: boolean
  createdAt: string
  actionUrl?: string
}

export const alerts: Alert[] = [
  {
    id: "alert1",
    type: "price_drop",
    title: "ירידת מחיר בנכס",
    message: "הנכס ברחוב הרצל 123 ירד במחיר ב-50,000 ₪",
    listingId: "l1",
    listingAddress: "רחוב הרצל 123, תל אביב",
    priority: "high",
    isRead: false,
    createdAt: "2024-01-15T10:30:00Z",
    actionUrl: "/listings/l1"
  },
  {
    id: "alert2", 
    type: "new_listing",
    title: "נכס חדש התווסף",
    message: "נכס חדש במרכז תל אביב התאים לקריטריונים שלך - 3 חדרים, עד 3M ₪",
    priority: "medium",
    isRead: false,
    createdAt: "2024-01-14T15:45:00Z"
  },
  {
    id: "alert3",
    type: "market_change", 
    title: "שינוי בשוק הנדל״ן",
    message: "עלייה של 2.3% במחירי הנדל״ן באזור מרכז תל אביב החודש",
    priority: "medium",
    isRead: false,
    createdAt: "2024-01-13T09:00:00Z"
  },
  {
    id: "alert4",
    type: "document_update",
    title: "עדכון מסמכים",
    message: "תוכנית בנייה חדשה פורסמה לאזור רוטשילד - עלולה להשפיע על ערך הנכס",
    listingId: "l2",
    listingAddress: "שדרות רוטשילד 45, תל אביב", 
    priority: "high",
    isRead: true,
    createdAt: "2024-01-12T14:20:00Z",
    actionUrl: "/listings/l2"
  },
  {
    id: "alert5",
    type: "permit_status",
    title: "עדכון היתר בנייה",
    message: "היתר הבנייה עבור הנכס ברוטשילד אושר - ניתן להתחיל בעבודות",
    listingId: "l2",
    listingAddress: "שדרות רוטשילד 45, תל אביב",
    priority: "low",
    isRead: true,
    createdAt: "2024-01-10T11:15:00Z",
    actionUrl: "/listings/l2"
  }
]

// Helper functions for alerts
export function getActiveAlerts(): Alert[] {
  return alerts.filter(alert => !alert.isRead)
}

export function getActiveAlertsCount(): number {
  return getActiveAlerts().length
}

export function getActiveListingsCount(): number {
  return listings.filter(listing => listing.status === "active").length
}
