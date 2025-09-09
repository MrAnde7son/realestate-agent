export const ROLE_LABELS = {
  admin: 'מנהל מערכת',
  member: 'משתמש רגיל'
} as const

export const ROLE_DESCRIPTIONS = {
  admin: 'גישה מלאה לכל הפונקציות',
  member: 'גישה לפונקציות בסיסיות'
} as const

export type UserRole = keyof typeof ROLE_LABELS

export function getRoleLabel(role: string): string {
  return ROLE_LABELS[role as UserRole] || role
}

export function getRoleDescription(role: string): string {
  return ROLE_DESCRIPTIONS[role as UserRole] || ''
}
