export interface Asset {
  id: number
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
  contact_info: {
    agent: string
    phone: string
    email: string
  }
  
  // Basic address fields
  city?: string
  neighborhood?: string
  street?: string
  number?: number
  gush?: string
  helka?: string
  subhelka?: string
  lat?: number
  lon?: number
  normalized_address?: string
  
  // Building details
  building_type?: string
  floor?: number
  total_floors?: number
  rooms?: number
  total_area?: number
  balcony_area?: number
  parking_spaces?: number
  storage_room?: boolean
  elevator?: boolean
  air_conditioning?: boolean
  furnished?: boolean
  renovated?: boolean
  year_built?: number
  last_renovation?: number
  
  // Financial fields
  price_per_sqm?: number
  rent_estimate?: number
  
  // Legal/Planning fields
  building_rights?: string
  permit_status?: string
  permit_date?: string
  zoning?: string
  
  // Additional properties for table display
  net_sqm?: number
  price_per_sqm_display?: number
  delta_vs_area_pct?: number
  dom_percentile?: number
  competition_1km?: string
  risk_flags?: string[]
  price_gap_pct?: number
  expected_price_range?: string
  remaining_rights_sqm?: number
  program?: string
  last_permit_q?: string
  noise_level?: number
  green_within_300m?: boolean
  schools_within_500m?: boolean
  model_price?: number
  confidence_pct?: number
  cap_rate_pct?: number
  antenna_distance_m?: number
  shelter_distance_m?: number
  documents?: { name: string; url: string; type?: string }[]
  
  // Asset enrichment fields
  asset_id?: number
  asset_status?: string
  sources?: string[]
  primary_source?: string
  permit_date_display?: string
  permit_status_display?: string
  permit_details?: string
  permit_main_area?: number
  permit_service_area?: number
  permit_applicant?: string
  permit_doc_url?: string
  main_rights_sqm?: number
  service_rights_sqm?: number
  additional_plan_rights?: string
  plan_status?: string
  public_obligations?: string
  public_transport?: string
  open_spaces_nearby?: string
  public_buildings?: string
  parking?: string
  nearby_projects?: string
  rights_usage_pct?: number
  legal_restrictions?: string
  urban_renewal_potential?: string
  betterment_levy?: string
}

export const assets: Asset[] = [
  {
    id: 1,
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
    contact_info: {
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
    normalized_address: "רחוב הרצל 123, תל אביב",
    
    // Building details
    building_type: "דירה",
    floor: 3,
    total_floors: 6,
    rooms: 4,
    total_area: 95,
    balcony_area: 10,
    parking_spaces: 1,
    storage_room: true,
    elevator: true,
    air_conditioning: true,
    furnished: false,
    renovated: true,
    year_built: 2015,
    last_renovation: 2022,
    
    // Financial fields
    price_per_sqm: 33529,
    rent_estimate: 9500,
    
    // Legal/Planning fields
    zoning: "מגורים א'",
    building_rights: "4 קומות + גג",
    permit_status: "מאושר",
    permit_date: "2024-01-15",
    documents: [
      { name: "נסח טאבו", url: "/docs/1/tabu.pdf", type: "tabu" },
      { name: "תשריט בית משותף", url: "/docs/1/condo-plan.pdf", type: "condo_plan" },
      { name: "היתר בנייה", url: "/docs/1/permit.pdf", type: "permit" },
      { name: "זכויות בנייה", url: "/docs/1/rights.pdf", type: "rights" },
      { name: "שומת מכרעת", url: "/docs/1/decisive-appraisal.pdf", type: "appraisal_decisive" },
      { name: "שומת רמ״י", url: "/docs/1/rmi-appraisal.pdf", type: "appraisal_rmi" }
    ],
    net_sqm: 85,
    price_per_sqm_display: 33529,
    delta_vs_area_pct: 2.5,
    dom_percentile: 75,
    competition_1km: "בינוני",
    risk_flags: [],
    price_gap_pct: -5.2,
    expected_price_range: "2.7M - 3.0M",
    remaining_rights_sqm: 45,
    program: "תמ״א 38",
    last_permit_q: "Q2/24",
    noise_level: 2,
    green_within_300m: true,
    schools_within_500m: true,
    model_price: 3000000,
    confidence_pct: 85,
    cap_rate_pct: 3.2,
    antenna_distance_m: 150,
    shelter_distance_m: 80,
    permit_date_display: '2024-01-15',
    permit_status_display: 'מאושר',
    permit_details: 'תוספת קומה',
    permit_main_area: 120,
    permit_service_area: 30,
    permit_applicant: 'בעלים',
    permit_doc_url: '/docs/1/permit.pdf',
    main_rights_sqm: 150,
    service_rights_sqm: 40,
    additional_plan_rights: 'תב"ע 1234',
    plan_status: 'בתוקף',
    public_obligations: 'הקצאת שטח ציבורי',
    public_transport: "5 דק' הליכה לרכבת הקלה",
    open_spaces_nearby: 'גן מאיר',
    public_buildings: 'בית ספר יסודי, גני ילדים',
    parking: 'מצוקת חניה בינונית',
    nearby_projects: 'פרויקט תמ"א ברח\' הרצל 150',
    rights_usage_pct: 70,
    legal_restrictions: 'הערת אזהרה לטובת בנק',
    urban_renewal_potential: 'תמ"א 38/2',
    betterment_levy: 'היטל צפוי כ-50 אלף ₪'
  },
  {
    id: 2,
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
    contact_info: {
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
    normalized_address: "שדרות רוטשילד 45, תל אביב",
    
    // Building details
    building_type: "דירה",
    floor: 8,
    total_floors: 8,
    rooms: 5,
    total_area: 140,
    balcony_area: 25,
    parking_spaces: 2,
    storage_room: true,
    elevator: true,
    air_conditioning: true,
    furnished: false,
    renovated: false,
    year_built: 2020,
    last_renovation: undefined,
    
    // Financial fields
    price_per_sqm: 35000,
    
    // Legal/Planning fields
    zoning: "מגורים א' מיוחד",
    building_rights: "8 קומות + גג",
    permit_status: "בטיפול",
    permit_date: "2024-02-01",
    documents: [
      { name: "נסח טאבו", url: "/docs/2/tabu.pdf", type: "tabu" },
      { name: "היתר בנייה", url: "/docs/2/permit.pdf", type: "permit" },
      { name: "שומת רמ״י", url: "/docs/2/rmi-appraisal.pdf", type: "appraisal_rmi" }
    ],
    net_sqm: 120,
    price_per_sqm_display: 35000,
    delta_vs_area_pct: 8.3,
    dom_percentile: 90,
    competition_1km: "גבוה",
    risk_flags: ["אנטנה סלולרית"],
    price_gap_pct: 12.1,
    expected_price_range: "3.8M - 4.3M",
    remaining_rights_sqm: 80,
    program: "פינוי בינוי",
    last_permit_q: "Q1/24",
    noise_level: 4,
    green_within_300m: false,
    schools_within_500m: true,
    model_price: 3750000,
    confidence_pct: 92,
    cap_rate_pct: 2.8,
    antenna_distance_m: 80,
    shelter_distance_m: 120,
    rent_estimate: 12000
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
  return assets.filter(asset => asset.status === "active").length
}

// Add a new asset to the in-memory store
export function addAsset(asset: Asset): void {
  assets.push(asset)
}

export function deleteAsset(id: number): Asset | null {
  const index = assets.findIndex(a => a.id === id)
  if (index !== -1) {
    return assets.splice(index, 1)[0]
  }
  return null
}
