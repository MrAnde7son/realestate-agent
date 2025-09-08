// Hebrew alert type constants and labels
export const ALERT_TYPES = {
  PRICE_DROP: 'PRICE_DROP',
  NEW_LISTING: 'NEW_LISTING',
  MARKET_TREND: 'MARKET_TREND',
  DOCS_UPDATE: 'DOCS_UPDATE',
  PERMIT_STATUS: 'PERMIT_STATUS',
  NEW_GOV_TX: 'NEW_GOV_TX',
  LISTING_REMOVED: 'LISTING_REMOVED',
} as const

export const ALERT_TYPE_LABELS = {
  [ALERT_TYPES.PRICE_DROP]: 'ירידת מחיר',
  [ALERT_TYPES.NEW_LISTING]: 'נכס חדש',
  [ALERT_TYPES.MARKET_TREND]: 'שינוי בשוק',
  [ALERT_TYPES.DOCS_UPDATE]: 'עדכון מסמכים',
  [ALERT_TYPES.PERMIT_STATUS]: 'סטטוס היתרים',
  [ALERT_TYPES.NEW_GOV_TX]: 'עסקה חדשה בסביבה',
  [ALERT_TYPES.LISTING_REMOVED]: 'מודעה הוסרה',
} as const

export const ALERT_FREQUENCIES = {
  IMMEDIATE: 'immediate',
  DAILY: 'daily',
} as const

export const ALERT_FREQUENCY_LABELS = {
  [ALERT_FREQUENCIES.IMMEDIATE]: 'מיידי',
  [ALERT_FREQUENCIES.DAILY]: 'יומי',
} as const

export const ALERT_SCOPES = {
  GLOBAL: 'global',
  ASSET: 'asset',
} as const

export const ALERT_SCOPE_LABELS = {
  [ALERT_SCOPES.GLOBAL]: 'כללי',
  [ALERT_SCOPES.ASSET]: 'נכס ספציפי',
} as const

export const ALERT_CHANNELS = {
  EMAIL: 'email',
  WHATSAPP: 'whatsapp',
} as const

export const ALERT_CHANNEL_LABELS = {
  [ALERT_CHANNELS.EMAIL]: 'אימייל',
  [ALERT_CHANNELS.WHATSAPP]: 'ווטסאפ',
} as const

// Default parameters for each alert type
export const ALERT_DEFAULT_PARAMS = {
  [ALERT_TYPES.PRICE_DROP]: { pct: 3 },
  [ALERT_TYPES.MARKET_TREND]: { delta_pct: 5, window_days: 30, radius_km: 1.0 },
  [ALERT_TYPES.NEW_GOV_TX]: { radius_m: 500 },
  [ALERT_TYPES.LISTING_REMOVED]: { misses: 2 },
} as const

// Hebrew labels for parameters
export const ALERT_PARAM_LABELS = {
  pct: 'אחוז ירידה',
  delta_pct: 'אחוז שינוי',
  window_days: 'ימים לחישוב',
  radius_km: 'רדיוס בקילומטרים',
  radius_m: 'רדיוס במטרים',
  misses: 'מספר פעמים חסר',
} as const

// Validation rules for parameters
export const ALERT_PARAM_VALIDATION = {
  [ALERT_TYPES.PRICE_DROP]: {
    pct: { min: 0, max: 100, type: 'number', label: 'אחוז ירידה' }
  },
  [ALERT_TYPES.MARKET_TREND]: {
    delta_pct: { min: 0, max: 100, type: 'number', label: 'אחוז שינוי' },
    window_days: { min: 7, max: 180, type: 'integer', label: 'ימים לחישוב' },
    radius_km: { min: 0.1, max: 5, type: 'number', label: 'רדיוס בקילומטרים' }
  },
  [ALERT_TYPES.NEW_GOV_TX]: {
    radius_m: { min: 50, max: 2000, type: 'integer', label: 'רדיוס במטרים' }
  },
  [ALERT_TYPES.LISTING_REMOVED]: {
    misses: { min: 1, max: 10, type: 'integer', label: 'מספר פעמים חסר' }
  },
} as const

export type AlertType = typeof ALERT_TYPES[keyof typeof ALERT_TYPES]
export type AlertFrequency = typeof ALERT_FREQUENCIES[keyof typeof ALERT_FREQUENCIES]
export type AlertScope = typeof ALERT_SCOPES[keyof typeof ALERT_SCOPES]
export type AlertChannel = typeof ALERT_CHANNELS[keyof typeof ALERT_CHANNELS]
