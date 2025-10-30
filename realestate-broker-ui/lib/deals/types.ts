export type DealStage = 'discovery' | 'negotiation' | 'legal' | 'financing' | 'closing' | 'abandoned'

export type DealConfidentiality = 'standard' | 'restricted' | 'internal'

export type DealParticipant = {
  id: number
  role: string
  side: 'buyer' | 'seller' | 'neutral'
  user: number | null
  invitation_status: string
  external_contact_json?: Record<string, unknown>
}

export type DealAssetSummary = {
  id: number
  address?: string | null
  city?: string | null
  neighborhood?: string | null
  price?: number | null
  status?: string | null
  building_type?: string | null
}

export type DealSummary = {
  id: number
  asset: number
  stage: DealStage
  deal_lead: number | null
  confidentiality_level: DealConfidentiality
  created_at: string
  updated_at: string
  party_roles: DealParticipant[]
  asset_summary?: DealAssetSummary | null
}

export const DEAL_STAGE_ORDER: DealStage[] = [
  'discovery',
  'negotiation',
  'legal',
  'financing',
  'closing',
  'abandoned',
]

export const DEAL_STAGE_LABELS: Record<DealStage, { label: string; description: string }> = {
  discovery: {
    label: 'איתור והערכה',
    description: 'הערכת הנכס, איסוף נתונים ותיאום ציפיות עם הצדדים',
  },
  negotiation: {
    label: 'מו״מ',
    description: 'ניהול הצעות נגדיות ודיוקים במסחר',
  },
  legal: {
    label: 'משפטי',
    description: 'טיוטות חוזה, הערות וחתימות סופיות',
  },
  financing: {
    label: 'מימון',
    description: 'ליווי מול בנקים והשלמת מסמכי אשראי',
  },
  closing: {
    label: 'סגירה',
    description: 'מסירת הנכס, התחשבנויות ותיעוד סופי',
  },
  abandoned: {
    label: 'ננטש',
    description: 'עסקה שהופסקה או הושהתה',
  },
}

export function isActiveStage(stage: DealStage): boolean {
  return stage !== 'abandoned'
}
