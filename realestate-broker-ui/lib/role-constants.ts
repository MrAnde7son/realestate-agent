export const ROLE_LABELS = {
  admin: 'מנהל מערכת',
  broker: 'מתווך',
  appraiser: 'שמאי',
  private: 'פרטי',
} as const

export const ROLE_DESCRIPTIONS = {
  admin: 'גישה מלאה לכל הפונקציות',
  broker: 'גישה מלאה למודול הלקוחות, דוחות וניתוחי שוק מקצועיים',
  appraiser: 'גישה מלאה למודול הלקוחות, דוחות ושומות מקצועיות',
  private: 'גישה לפונקציות בסיסיות ולנתוני שוק',
} as const

export type UserRole = keyof typeof ROLE_LABELS

export function getRoleLabel(role: string): string {
  return ROLE_LABELS[role as UserRole] || role
}

export function getRoleDescription(role: string): string {
  return ROLE_DESCRIPTIONS[role as UserRole] || ''
}
