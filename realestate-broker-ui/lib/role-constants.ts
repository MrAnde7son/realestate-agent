export const ROLE_LABELS = {
  admin: 'מנהל מערכת',
  broker: 'מתווך',
  appraiser: 'שמאי',
  investor: 'משקיע',
  viewer: 'צופה',
} as const

export const ROLE_DESCRIPTIONS = {
  admin: 'גישה מלאה לכל הפונקציות',
  broker: 'גישה מלאה למודול הלקוחות, דוחות וניתוחי שוק מקצועיים',
  appraiser: 'גישה מלאה למודול הלקוחות, דוחות ושומות מקצועיות',
  investor: 'גישה לפונקציות השקעה, דוחות בסיסיים והתראות',
  viewer: 'גישה לצפייה בלבד בנתונים שהוקצו על ידי הארגון',
} as const

export type UserRole = keyof typeof ROLE_LABELS

export function getRoleLabel(role: string): string {
  return ROLE_LABELS[role as UserRole] || role
}

export function getRoleDescription(role: string): string {
  return ROLE_DESCRIPTIONS[role as UserRole] || ''
}
