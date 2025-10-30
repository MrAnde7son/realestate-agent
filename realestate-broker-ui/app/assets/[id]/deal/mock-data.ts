import type { DealConfidentiality, DealParticipant, DealStage, DealSummary } from '@/lib/deals/types'

export type Party = {
  id: string
  name: string
  role: string
  side: 'buyer' | 'seller' | 'neutral'
  email: string
}

export type OfferConditions = {
  inspection: boolean
  appraisalContingency: boolean
  financingContingencyDays: number
}

export type Offer = {
  id: string
  submittedAt: string
  amount: number
  downPaymentPct: number
  financingType: 'cash' | 'mortgage' | 'mixed'
  expiresAt: string
  status: 'pending' | 'accepted' | 'countered' | 'withdrawn'
  side: 'buyer' | 'seller'
  message: string
  conditions: OfferConditions
}

export type DocumentKind = 'legal' | 'appraisal' | 'architect' | 'mortgage' | 'generic'

export type DocumentVisibility = 'deal' | 'buyer_side' | 'seller_side'

export type DocumentStatus = 'processing' | 'ready' | 'failed'

export type DealDocument = {
  id: string
  title: string
  kind: DocumentKind
  uploadedAt: string
  uploader: string
  visibility: DocumentVisibility
  summary: string
  linkedOfferId?: string
  status?: DocumentStatus
  storageUrl?: string
}

export type DealTask = {
  id: string
  title: string
  owner: string
  status: 'todo' | 'in_progress' | 'blocked' | 'done'
  dueDate: string
  blocker?: string
}

export type MortgageOffer = {
  id: string
  lender: string
  productType: 'fixed' | 'variable' | 'mixed'
  ratePct: number
  aprPct: number
  termMonths: number
  monthlyPayment: number
  feesTotal: number
  validUntil: string
  score: number
}

export type DealWorkspaceMock = {
  stage: DealStage
  askingPrice: number
  acceptedOfferAmount: number
  targetClosingDate: string
  lastUpdated: string
  address: string
}

export const PARTIES: Party[] = [
  { id: 'party-buyer', name: 'דנה לוי', role: 'קונה', side: 'buyer', email: 'dana@example.com' },
  { id: 'party-buyer-agent', name: 'נועם אזולאי', role: 'מתווך קונה', side: 'buyer', email: 'noam@nreteam.com' },
  { id: 'party-buyer-lawyer', name: 'עו״ד ליאורה שור', role: 'עו״ד קונה', side: 'buyer', email: 'liora@shorelegal.il' },
  { id: 'party-seller', name: 'איתי כהן', role: 'מוכר', side: 'seller', email: 'itay@example.com' },
  { id: 'party-seller-agent', name: 'רות שלהב', role: 'מתווך מוכר', side: 'seller', email: 'ruth@listings.co.il' },
  { id: 'party-seller-lawyer', name: 'עו״ד יוסי בר', role: 'עו״ד מוכר', side: 'seller', email: 'yossi@barlegal.il' },
  { id: 'party-banker', name: 'מוקד בנק לאומי', role: 'בנקאי משכנתאות', side: 'neutral', email: 'mortgage@leumi.co.il' },
]

export const INITIAL_OFFERS: Offer[] = [
  {
    id: 'offer-103',
    submittedAt: '2024-11-03T08:45:00Z',
    amount: 4_320_000,
    downPaymentPct: 30,
    financingType: 'mixed',
    expiresAt: '2024-11-05T08:45:00Z',
    status: 'accepted',
    side: 'seller',
    message: 'התקבל עם לוח זמנים מוסכם לבדיקות וכניסה ב־15 בינואר.',
    conditions: {
      inspection: true,
      appraisalContingency: true,
      financingContingencyDays: 14,
    },
  },
  {
    id: 'offer-102',
    submittedAt: '2024-10-29T15:10:00Z',
    amount: 4_250_000,
    downPaymentPct: 35,
    financingType: 'mortgage',
    expiresAt: '2024-11-01T15:10:00Z',
    status: 'countered',
    side: 'buyer',
    message: 'מעוניינים לסגור בעסקה עם בדיקת חשמל מקיפה והקדמת תאריך מסירה לשבוע הראשון של ינואר.',
    conditions: {
      inspection: true,
      appraisalContingency: true,
      financingContingencyDays: 21,
    },
  },
  {
    id: 'offer-101',
    submittedAt: '2024-10-20T11:30:00Z',
    amount: 4_150_000,
    downPaymentPct: 25,
    financingType: 'mortgage',
    expiresAt: '2024-10-23T11:30:00Z',
    status: 'withdrawn',
    side: 'buyer',
    message: 'מבקשים הנחה לטובת שיפוץ והארכת לוחות זמנים לבדיקות.',
    conditions: {
      inspection: true,
      appraisalContingency: false,
      financingContingencyDays: 28,
    },
  },
]

export const INITIAL_DOCUMENTS: DealDocument[] = [
  {
    id: 'doc-legal-001',
    title: 'טיוטת הסכם מכר מתוקנת',
    kind: 'legal',
    uploadedAt: '2024-11-02T16:20:00Z',
    uploader: 'עו״ד ליאורה שור',
    visibility: 'deal',
    summary: 'עדכון סעיף מסירת החזקה ותיקוני אחריות לתשתיות.',
    status: 'ready',
    storageUrl: 'https://example.com/doc-legal-001.pdf',
    linkedOfferId: 'offer-103',
  },
  {
    id: 'doc-appraisal-001',
    title: 'דו״ח שמאי מילר - עדכון שווי',
    kind: 'appraisal',
    uploadedAt: '2024-10-31T09:45:00Z',
    uploader: 'שמאי אברהם מילר',
    visibility: 'deal',
    summary: 'הערכת שווי מעודכנת ל-4.35M ₪ בהתאם להשוואות דומות בסביבה.',
    status: 'ready',
    storageUrl: 'https://example.com/doc-appraisal-001.pdf',
  },
  {
    id: 'doc-architect-001',
    title: 'תוכנית שינויים מאושרת',
    kind: 'architect',
    uploadedAt: '2024-10-28T14:05:00Z',
    uploader: 'סטודיו קו ישר',
    visibility: 'buyer_side',
    summary: 'סקיצה לחלוקת פנים חדשה הכוללת הוספת משרד ביתי.',
    status: 'ready',
    storageUrl: 'https://example.com/doc-architect-001.pdf',
  },
  {
    id: 'doc-mortgage-001',
    title: 'אישור עקרוני - בנק לאומי',
    kind: 'mortgage',
    uploadedAt: '2024-10-25T10:15:00Z',
    uploader: 'מוקד בנק לאומי',
    visibility: 'buyer_side',
    summary: 'אישור מימון עד 70% משווי העסקה עם ריבית קבועה ל-20 שנה.',
    status: 'ready',
    storageUrl: 'https://example.com/doc-mortgage-001.pdf',
  },
]

export const INITIAL_TASKS: DealTask[] = [
  {
    id: 'task-001',
    title: 'תיאום בדיקת חשמל',
    owner: 'נועם אזולאי',
    status: 'in_progress',
    dueDate: '2024-11-07',
    blocker: 'ממתינים לאישור כניסה מהדיירים',
  },
  {
    id: 'task-002',
    title: 'איסוף מסמכי בנק מעודכנים',
    owner: 'דנה לוי',
    status: 'todo',
    dueDate: '2024-11-05',
  },
  {
    id: 'task-003',
    title: 'אישור סעיפי אחריות משפטית',
    owner: 'עו״ד יוסי בר',
    status: 'blocked',
    dueDate: '2024-11-09',
    blocker: 'נדרש מענה מהקונה על סעיף ביטול',
  },
  {
    id: 'task-004',
    title: 'בדיקת מסמכי טאבו',
    owner: 'רות שלהב',
    status: 'done',
    dueDate: '2024-10-27',
  },
]

export const INITIAL_MORTGAGE_OFFERS: MortgageOffer[] = [
  {
    id: 'mortgage-1',
    lender: 'בנק הפועלים',
    productType: 'variable',
    ratePct: 3.95,
    aprPct: 4.12,
    termMonths: 300,
    monthlyPayment: 11_980,
    feesTotal: 6_200,
    validUntil: '2024-11-15T21:00:00Z',
    score: 86,
  },
  {
    id: 'mortgage-2',
    lender: 'מזרחי טפחות',
    productType: 'mixed',
    ratePct: 4.1,
    aprPct: 4.28,
    termMonths: 300,
    monthlyPayment: 12_540,
    feesTotal: 3_800,
    validUntil: '2024-11-18T21:00:00Z',
    score: 82,
  },
  {
    id: 'mortgage-3',
    lender: 'בנק דיסקונט',
    productType: 'fixed',
    ratePct: 4.35,
    aprPct: 4.41,
    termMonths: 240,
    monthlyPayment: 13_120,
    feesTotal: 5_500,
    validUntil: '2024-11-10T21:00:00Z',
    score: 74,
  },
]

export const DEAL_METADATA: DealWorkspaceMock = {
  stage: 'legal',
  askingPrice: 4_500_000,
  acceptedOfferAmount: 4_320_000,
  targetClosingDate: '2025-01-15',
  lastUpdated: '2024-11-03T08:45:00Z',
  address: 'הרצל 17, תל אביב',
}

const MOCK_PARTY_ROLES: DealParticipant[] = [
  {
    id: 1001,
    role: 'מתווך קונה',
    side: 'buyer',
    user: 201,
    invitation_status: 'accepted',
    external_contact_json: { email: 'noam@nreteam.com', name: 'נועם אזולאי' },
  },
  {
    id: 1002,
    role: 'מתווך מוכר',
    side: 'seller',
    user: 202,
    invitation_status: 'accepted',
    external_contact_json: { email: 'ruth@listings.co.il', name: 'רות שלהב' },
  },
  {
    id: 1003,
    role: 'קונה',
    side: 'buyer',
    user: null,
    invitation_status: 'invited',
    external_contact_json: { email: 'dana@example.com', name: 'דנה לוי' },
  },
]

const confidentiality: DealConfidentiality = 'standard'

export const DEAL_SUMMARIES_MOCK: DealSummary[] = [
  {
    id: 501,
    asset: 501,
    stage: DEAL_METADATA.stage,
    deal_lead: 201,
    confidentiality_level: confidentiality,
    created_at: '2024-09-12T09:15:00Z',
    updated_at: DEAL_METADATA.lastUpdated,
    party_roles: MOCK_PARTY_ROLES,
    asset_summary: {
      id: 501,
      address: DEAL_METADATA.address,
      city: 'תל אביב',
      neighborhood: 'לב העיר',
      price: DEAL_METADATA.askingPrice,
      status: 'active',
      building_type: 'דירה',
    },
  },
  {
    id: 502,
    asset: 502,
    stage: 'negotiation',
    deal_lead: 305,
    confidentiality_level: confidentiality,
    created_at: '2024-08-03T13:45:00Z',
    updated_at: '2024-10-30T16:00:00Z',
    party_roles: [
      {
        id: 1010,
        role: 'מנהל עסקה',
        side: 'neutral',
        user: 305,
        invitation_status: 'accepted',
        external_contact_json: { email: 'amit@brokerage.co.il', name: 'עמית מזרחי' },
      },
      {
        id: 1011,
        role: 'קונה',
        side: 'buyer',
        user: null,
        invitation_status: 'accepted',
        external_contact_json: { email: 'liat@example.com', name: 'ליאת בן עמי' },
      },
      {
        id: 1012,
        role: 'מוכר',
        side: 'seller',
        user: null,
        invitation_status: 'accepted',
        external_contact_json: { email: 'ronen@example.com', name: 'רונן פרידמן' },
      },
    ],
    asset_summary: {
      id: 502,
      address: 'אבן גבירול 98, תל אביב',
      city: 'תל אביב',
      neighborhood: 'הצפון הישן',
      price: 3_850_000,
      status: 'active',
      building_type: 'דירת גג',
    },
  },
  {
    id: 503,
    asset: 503,
    stage: 'discovery',
    deal_lead: 411,
    confidentiality_level: confidentiality,
    created_at: '2024-10-01T07:30:00Z',
    updated_at: '2024-10-28T09:20:00Z',
    party_roles: [
      {
        id: 1020,
        role: 'מתווך מוביל',
        side: 'neutral',
        user: 411,
        invitation_status: 'accepted',
        external_contact_json: { email: 'shira@brokerage.co.il', name: 'שירה פז' },
      },
      {
        id: 1021,
        role: 'קונה',
        side: 'buyer',
        user: null,
        invitation_status: 'pending',
        external_contact_json: { email: 'adi@example.com', name: 'עדי הרשקוביץ' },
      },
    ],
    asset_summary: {
      id: 503,
      address: 'רוטשילד 12, חיפה',
      city: 'חיפה',
      neighborhood: 'הדר',
      price: 2_150_000,
      status: 'prospect',
      building_type: 'דירת גן',
    },
  },
  {
    id: 504,
    asset: 504,
    stage: 'financing',
    deal_lead: 510,
    confidentiality_level: confidentiality,
    created_at: '2024-05-22T10:15:00Z',
    updated_at: '2024-10-27T11:50:00Z',
    party_roles: [
      {
        id: 1030,
        role: 'מתווך מוכר',
        side: 'seller',
        user: 510,
        invitation_status: 'accepted',
        external_contact_json: { email: 'roi@example.com', name: 'רועי רבינוביץ׳' },
      },
      {
        id: 1031,
        role: 'קונה',
        side: 'buyer',
        user: null,
        invitation_status: 'accepted',
        external_contact_json: { email: 'karin@example.com', name: 'קרין לוי' },
      },
    ],
    asset_summary: {
      id: 504,
      address: 'הנשיא 4, ראשון לציון',
      city: 'ראשון לציון',
      neighborhood: 'מרכז העיר',
      price: 2_980_000,
      status: 'under_contract',
      building_type: 'דירת 5 חדרים',
    },
  },
]
