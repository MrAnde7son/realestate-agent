import type { Asset } from './normalizers/asset'

export const assets = [
  {
    id: 1,
    address: "הרצל 123 דירה 3 דירה 6 תל אביב",
    price: 2850000,
    bedrooms: 3,
    bathrooms: 2,
    area: 85,
    type: "דירה",
    images: ["/placeholder-home.jpg"],
    description: "דירה מקסימה במרכז תל אביב עם נוף לים",
    features: ["מעלית", "חניה", "מרפסת", "משופצת"],
    contactInfo: {
      agent: "יוסי כהן",
      phone: "050-1234567",
      email: "yossi@example.com"
    },
    
    // Basic address fields
    city: "תל אביב",
    neighborhood: "מרכז העיר",
    street: "הרצל",
    number: 123,
    gush: "1234",
    helka: "56",
    subhelka: "1",
    lat: 32.0853,
    lon: 34.7818,
    normalizedAddress: "רחוב הרצל 123, תל אביב",
    
    // Building details
    buildingType: "דירה",
    floor: 3,
    apartmentNumber: "6",
    totalFloors: 6,
    rooms: 4,
    totalArea: 95,
    balconyArea: 10,
    parkingSpaces: 1,
    storageRoom: true,
    elevator: true,
    airConditioning: true,
    furnished: false,
    renovated: true,
    yearBuilt: 2015,
    lastRenovation: 2022,
    
    // Financial fields
    pricePerSqm: 33529,
    rentEstimate: 9500,
    
    // Legal/Planning fields
    zoning: "מגורים א'",
    buildingRights: "4 קומות + גג",
    permitStatus: "מאושר",
    permitDate: "2024-01-15",
    documents: [
      { name: "נסח טאבו", url: "/docs/1/tabu.pdf", type: "tabu" },
      { name: "תשריט בית משותף", url: "/docs/1/condo-plan.pdf", type: "condo_plan" },
      { name: "היתר בנייה", url: "/docs/1/permit.pdf", type: "permit" },
      { name: "זכויות בנייה", url: "/docs/1/rights.pdf", type: "rights" },
      { name: "שומת מכרעת", url: "/docs/1/decisive-appraisal.pdf", type: "appraisal_decisive" },
      { name: "שומת רמ״י", url: "/docs/1/rmi-appraisal.pdf", type: "appraisal_rmi" }
    ],
    pricePerSqmDisplay: 33529,
    deltaVsAreaPct: 2.5,
    domPercentile: 75,
    competition1km: "בינוני",
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
    permitDateDisplay: '2024-01-15',
    permitStatusDisplay: 'מאושר',
    permitDetails: 'תוספת קומה',
    permitMainArea: 120,
    permitServiceArea: 30,
    permitApplicant: 'בעלים',
    permitDocUrl: '/docs/1/permit.pdf',
    mainRightsSqm: 150,
    serviceRightsSqm: 40,
    additionalPlanRights: 'תב"ע 1234',
    planStatus: 'בתוקף',
    publicObligations: 'הקצאת שטח ציבורי',
    publicTransport: "5 דק' הליכה לרכבת הקלה",
    openSpacesNearby: 'גן מאיר',
    publicBuildings: 'בית ספר יסודי, גני ילדים',
    parking: 'מצוקת חניה בינונית',
    nearbyProjects: 'פרויקט תמ"א ברח\' הרצל 150',
    rightsUsagePct: 70,
    legalRestrictions: 'הערת אזהרה לטובת בנק',
    urbanRenewalPotential: 'תמ"א 38/2',
    bettermentLevy: 'היטל צפוי כ-50 אלף ₪',
    assetId: 1,
    assetStatus: 'done',
    sources: ['yad2', 'gis_permit', 'gis_rights', 'tabu'],
    primarySource: 'yad2',
    _meta: {
      // Source attribution for enriched fields
      zoning: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      buildingRights: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      permitStatus: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      permitDate: { source: 'מנהל התכנון', fetched_at: '2025-09-01', url: '/docs/1/permit.pdf' },
      program: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      mainRightsSqm: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      serviceRightsSqm: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      additionalPlanRights: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      publicObligations: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      planStatus: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      remainingRightsSqm: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      riskFlags: { source: 'משרד הפנים', fetched_at: '2025-09-01' },
      publicTransport: { source: 'משרד התחבורה', fetched_at: '2025-09-01' },
      openSpacesNearby: { source: 'OpenStreetMap', fetched_at: '2025-09-01' },
      publicBuildings: { source: 'עיריית תל אביב', fetched_at: '2025-09-01' },
      parking: { source: 'עיריית תל אביב', fetched_at: '2025-09-01' },
      nearbyProjects: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      permitDetails: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      permitMainArea: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      permitServiceArea: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      permitApplicant: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      permitDocUrl: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      noiseLevel: { source: 'המשרד להגנת הסביבה', fetched_at: '2025-09-01' },
      greenWithin300m: { source: 'OpenStreetMap', fetched_at: '2025-09-01' },
      antennaDistanceM: { source: 'משרד התקשורת', fetched_at: '2025-09-01' },
      pricePerSqm: { source: 'יד2', fetched_at: '2025-09-01' }
    }
  },
  {
    id: 2,
    address: "רוטשילד 45 פנטהאוס 8 דירה 12 תל אביב",
    price: 4200000,
    bedrooms: 4,
    bathrooms: 3,
    area: 120,
    type: "דירה",
    images: ["/placeholder-home.jpg"],
    description: "דירת פנטהאוס מפוארת עם מרפסת גדולה",
    features: ["מעלית", "חניה", "מרפסת גדולה", "חדר עבודה"],
    contactInfo: {
      agent: "דנה לוי",
      phone: "052-7654321",
      email: "dana@example.com"
    },
    
    // Basic address fields
    city: "תל אביב",
    neighborhood: "רוטשילד",
    street: "שדרות רוטשילד",
    number: 45,
    gush: "5678",
    helka: "12",
    subhelka: "3",
    lat: 32.0668,
    lon: 34.7778,
    normalizedAddress: "שדרות רוטשילד 45, תל אביב",
    
    // Building details
    buildingType: "דירה",
    floor: 8,
    apartmentNumber: "12",
    totalFloors: 8,
    rooms: 5,
    totalArea: 140,
    balconyArea: 25,
    parkingSpaces: 2,
    storageRoom: true,
    elevator: true,
    airConditioning: true,
    furnished: false,
    renovated: false,
    yearBuilt: 2020,
    lastRenovation: undefined,
    
    // Financial fields
    pricePerSqm: 35000,
    
    // Legal/Planning fields
    zoning: "מגורים א' מיוחד",
    buildingRights: "8 קומות + גג",
    permitStatus: "בטיפול",
    permitDate: "2024-02-01",
    documents: [
      { name: "נסח טאבו", url: "/docs/2/tabu.pdf", type: "tabu" },
      { name: "היתר בנייה", url: "/docs/2/permit.pdf", type: "permit" },
      { name: "שומת רמ״י", url: "/docs/2/rmi-appraisal.pdf", type: "appraisal_rmi" }
    ],
    pricePerSqmDisplay: 35000,
    deltaVsAreaPct: 8.3,
    domPercentile: 90,
    competition1km: "גבוה",
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
    rentEstimate: 12000,
    permitDateDisplay: '2024-02-01',
    permitStatusDisplay: 'בטיפול',
    permitDetails: 'תוספת מרפסת',
    permitMainArea: 160,
    permitServiceArea: 40,
    permitApplicant: 'יזמים',
    permitDocUrl: '/docs/2/permit.pdf',
    mainRightsSqm: 180,
    serviceRightsSqm: 50,
    additionalPlanRights: 'תב"ע 5678',
    planStatus: 'בתהליך',
    publicObligations: 'שביל ציבורי',
    publicTransport: "2 דק' הליכה לרכבת הקלה",
    openSpacesNearby: 'פארק רוטשילד',
    publicBuildings: 'ספרייה עירונית, מוזיאון',
    parking: 'חניה תת קרקעית',
    nearbyProjects: 'מגדל משרדים סמוך',
    rightsUsagePct: 55,
    legalRestrictions: 'שעבוד לטובת בנק',
    urbanRenewalPotential: 'פינוי בינוי',
    bettermentLevy: 'היטל צפוי כ-80 אלף ₪',
    assetId: 2,
    assetStatus: 'pending',
    sources: ['yad2'],
    primarySource: 'yad2',
    _meta: {
      // Source attribution for enriched fields
      zoning: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      buildingRights: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      permitStatus: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      permitDate: { source: 'מנהל התכנון', fetched_at: '2025-09-01', url: '/docs/2/permit.pdf' },
      program: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      mainRightsSqm: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      serviceRightsSqm: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      additionalPlanRights: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      publicObligations: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      planStatus: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      remainingRightsSqm: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      riskFlags: { source: 'משרד הפנים', fetched_at: '2025-09-01' },
      publicTransport: { source: 'משרד התחבורה', fetched_at: '2025-09-01' },
      openSpacesNearby: { source: 'OpenStreetMap', fetched_at: '2025-09-01' },
      publicBuildings: { source: 'עיריית תל אביב', fetched_at: '2025-09-01' },
      parking: { source: 'עיריית תל אביב', fetched_at: '2025-09-01' },
      nearbyProjects: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      permitDetails: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      permitMainArea: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      permitServiceArea: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      permitApplicant: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      permitDocUrl: { source: 'מנהל התכנון', fetched_at: '2025-09-01' },
      noiseLevel: { source: 'המשרד להגנת הסביבה', fetched_at: '2025-09-01' },
      greenWithin300m: { source: 'OpenStreetMap', fetched_at: '2025-09-01' },
      antennaDistanceM: { source: 'משרד התקשורת', fetched_at: '2025-09-01' },
      pricePerSqm: { source: 'יד2', fetched_at: '2025-09-01' }
    }
  }
]

// Mock data functions for API routes
export function appraisalByAsset(id: number) {
  return {
    assetId: id,
    marketValue: 2850000,
    appraisedValue: 2800000,
    date: "2024-01-15",
    appraiser: "שמואל דוד",
    notes: "הערכה בהתבסס על נתוני שוק עדכניים"
  }
}

export function compsByAsset(id: number) {
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

export function rightsByAsset(id: number) {
  return {
    assetId: id,
    buildingRights: "זכויות בנייה: 4 קומות + גג",
    landUse: "מגורים א'",
    restrictions: ["איסור שינוי יעוד", "חובת שמירה על חזית היסטורית"],
    permits: ["היתר בנייה בתוקף", "היתר עסק למשרד"],
    lastUpdate: "2024-01-20"
  }
}

// Alerts/Notifications data
export interface Alert {
  id: number
  type: 'price_drop' | 'new_asset' | 'market_change' | 'document_update' | 'permit_status'
  title: string
  message: string
  assetId?: number
  assetAddress?: string
  priority: 'high' | 'medium' | 'low'
  isRead: boolean
  createdAt: string
  actionUrl?: string
}

export const alerts: Alert[] = [
  {
    id: 1,
    type: "price_drop",
    title: "ירידת מחיר בנכס",
    message: "הנכס ברחוב הרצל 123 ירד במחיר ב-50,000 ₪",
    assetId: 1,
    assetAddress: "רחוב הרצל 123, תל אביב",
    priority: "high",
    isRead: false,
    createdAt: "2024-01-15T10:30:00Z",
    actionUrl: "/assets/1"
  },
  {
    id: 2,
    type: "new_asset",
    title: "נכס חדש התווסף",
    message: "נכס חדש במרכז תל אביב התאים לקריטריונים שלך - 3 חדרים, עד 3M ₪",
    priority: "medium",
    isRead: false,
    createdAt: "2024-01-14T15:45:00Z"
  },
  {
    id: 3,
    type: "market_change",
    title: "שינוי בשוק הנדל״ן",
    message: "עלייה של 2.3% במחירי הנדל״ן באזור מרכז תל אביב החודש",
    priority: "medium",
    isRead: false,
    createdAt: "2024-01-13T09:00:00Z"
  },
  {
    id: 4,
    type: "document_update",
    title: "עדכון מסמכים",
    message: "תוכנית בנייה חדשה פורסמה לאזור רוטשילד - עלולה להשפיע על ערך הנכס",
    assetId: 2,
    assetAddress: "שדרות רוטשילד 45, תל אביב",
    priority: "high",
    isRead: true,
    createdAt: "2024-01-12T14:20:00Z",
    actionUrl: "/assets/2"
  },
  {
    id: 5,
    type: "permit_status",
    title: "עדכון היתר בנייה",
    message: "היתר הבנייה עבור הנכס ברוטשילד אושר - ניתן להתחיל בעבודות",
    assetId: 2,
    assetAddress: "שדרות רוטשילד 45, תל אביב",
    priority: "low",
    isRead: true,
    createdAt: "2024-01-10T11:15:00Z",
    actionUrl: "/assets/2"
  }
]

// Helper functions for alerts
export function getActiveAlerts(): Alert[] {
  return alerts.filter(alert => !alert.isRead)
}

export function getActiveAlertsCount(): number {
  return getActiveAlerts().length
}

export function getActiveAssetsCount(): number {
  return assets.filter(asset => asset.assetStatus === "active").length
}

export function deleteAsset(id: number): Asset | null {
  const index = assets.findIndex(a => a.id === id)
  if (index !== -1) {
    return assets.splice(index, 1)[0]
  }
  return null
}
