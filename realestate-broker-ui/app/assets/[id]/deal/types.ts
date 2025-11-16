import type { DealParticipant, DealStage } from '@/lib/deals/types'

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

export type DealWorkspaceMetadata = {
  stage: DealStage
  askingPrice: number
  acceptedOfferAmount: number
  targetClosingDate: string
  lastUpdated: string
  address: string
}

/**
 * Maps backend DealParticipant[] to frontend Party[] format
 */
export function mapPartyRolesToParties(partyRoles: DealParticipant[]): Party[] {
  return partyRoles.map((participant, index) => {
    const contact = participant.external_contact_json || {}
    return {
      id: `party-${participant.id}`,
      name: typeof contact.name === 'string' ? contact.name : `משתתף ${index + 1}`,
      role: participant.role,
      side: participant.side as 'buyer' | 'seller' | 'neutral',
      email: typeof contact.email === 'string' ? contact.email : '',
    }
  })
}

