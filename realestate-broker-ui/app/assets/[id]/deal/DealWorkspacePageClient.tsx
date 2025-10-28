'use client'

import React, { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Separator } from '@/components/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { fmtCurrency, fmtNumber } from '@/lib/utils'
import { cn } from '@/lib/utils'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import {
  ArrowRightLeft,
  ArrowLeft,
  CheckCircle2,
  Clock3,
  FileText,
  FileUp,
  Gavel,
  Handshake,
  Layers,
  ShieldCheck,
  Sparkles,
  Home,
  Building,
} from 'lucide-react'

type DealStage = 'discovery' | 'negotiation' | 'legal' | 'financing' | 'closing'

type Party = {
  id: string
  name: string
  role: string
  side: 'buyer' | 'seller' | 'neutral'
  email: string
}

type OfferConditions = {
  inspection: boolean
  appraisalContingency: boolean
  financingContingencyDays: number
}

type Offer = {
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

type DealDocument = {
  id: string
  title: string
  kind: 'legal' | 'appraisal' | 'architect' | 'mortgage'
  uploadedAt: string
  uploader: string
  visibility: 'deal' | 'buyer_side' | 'seller_side'
  summary: string
  linkedOfferId?: string
}

type DealTask = {
  id: string
  title: string
  owner: string
  status: 'todo' | 'in_progress' | 'blocked' | 'done'
  dueDate: string
  blocker?: string
}

type MortgageOffer = {
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

type TimelineEvent = {
  id: string
  type: 'offer' | 'document' | 'task'
  title: string
  timestamp: string
  description: string
  side?: 'buyer' | 'seller' | 'neutral'
  statusLabel?: string
}

type OfferDraft = {
  amount: number
  downPaymentPct: number
  financingType: Offer['financingType']
  expiresInHours: number
  message: string
  conditions: OfferConditions
}

const STAGE_FLOW: { key: DealStage; label: string; helper: string }[] = [
  { key: 'discovery', label: 'איתור והערכה', helper: 'איסוף חומר רקע והכנת הנכס לעסקה' },
  { key: 'negotiation', label: 'מו״מ', helper: 'ניהול הצעות נגדיות ודיוקים במחיר' },
  { key: 'legal', label: 'משפטי', helper: 'טיוטות חוזה, הערות וחתימות' },
  { key: 'financing', label: 'מימון', helper: 'בדיקת מסלולים ואישורי אשראי' },
  { key: 'closing', label: 'סגירה', helper: 'מסירת נכס והתחשבנות' },
]

const PARTIES: Party[] = [
  { id: 'party-buyer', name: 'דנה לוי', role: 'קונה', side: 'buyer', email: 'dana@example.com' },
  { id: 'party-buyer-agent', name: 'נועם אזולאי', role: 'מתווך קונה', side: 'buyer', email: 'noam@nreteam.com' },
  { id: 'party-buyer-lawyer', name: 'עו״ד ליאורה שור', role: 'עו״ד קונה', side: 'buyer', email: 'liora@shorelegal.il' },
  { id: 'party-seller', name: 'איתי כהן', role: 'מוכר', side: 'seller', email: 'itay@example.com' },
  { id: 'party-seller-agent', name: 'רות שלהב', role: 'מתווך מוכר', side: 'seller', email: 'ruth@listings.co.il' },
  { id: 'party-seller-lawyer', name: 'עו״ד יוסי בר', role: 'עו״ד מוכר', side: 'seller', email: 'yossi@barlegal.il' },
  { id: 'party-banker', name: 'מוקד בנק לאומי', role: 'בנקאי משכנתאות', side: 'neutral', email: 'mortgage@leumi.co.il' },
]

const INITIAL_OFFERS: Offer[] = [
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
    financingType: 'mixed',
    expiresAt: '2024-10-31T15:10:00Z',
    status: 'countered',
    side: 'buyer',
    message: 'הצעת נגד על 4.25 מ׳ עם קביעת הערכת שווי מוקדמת.',
    conditions: {
      inspection: true,
      appraisalContingency: true,
      financingContingencyDays: 21,
    },
  },
  {
    id: 'offer-101',
    submittedAt: '2024-10-27T10:00:00Z',
    amount: 4_150_000,
    downPaymentPct: 30,
    financingType: 'mortgage',
    expiresAt: '2024-10-29T10:00:00Z',
    status: 'countered',
    side: 'buyer',
    message: 'הצעה ראשונית הכוללת בדיקת נכס סטנדרטית.',
    conditions: {
      inspection: true,
      appraisalContingency: true,
      financingContingencyDays: 21,
    },
  },
]

const INITIAL_DOCUMENTS: DealDocument[] = [
  {
    id: 'doc-legal-1',
    title: 'טיוטת הסכם מכר',
    kind: 'legal',
    uploadedAt: '2024-11-02T14:10:00Z',
    uploader: 'עו״ד ליאורה שור',
    visibility: 'buyer_side',
    summary: 'טיוטה ראשונה עם הערות על סעיפי אחריות.',
  },
  {
    id: 'doc-legal-2',
    title: 'גילוי נאות של המוכר',
    kind: 'legal',
    uploadedAt: '2024-10-28T09:15:00Z',
    uploader: 'רות שלהב',
    visibility: 'deal',
    summary: 'חבילת גילוי מלאה חתומה ומאומתת.',
  },
  {
    id: 'doc-appraisal-1',
    title: 'שומת שמאי',
    kind: 'appraisal',
    uploadedAt: '2024-10-30T11:20:00Z',
    uploader: 'דנה לוי',
    visibility: 'buyer_side',
    summary: 'שווי מוערך ₪4.35 מ׳, סטייה של ‎+1.2% מול נדל״נר.',
  },
  {
    id: 'doc-architect-1',
    title: 'תכנית שיפוץ מוצעת',
    kind: 'architect',
    uploadedAt: '2024-10-25T16:40:00Z',
    uploader: 'סטודיו ארצי',
    visibility: 'deal',
    summary: 'שינויים מוצעים בתכנית עם הערות תאימות לזכויות בנייה.',
  },
  {
    id: 'doc-mortgage-1',
    title: 'הצעת בנק לאומי',
    kind: 'mortgage',
    uploadedAt: '2024-11-01T12:05:00Z',
    uploader: 'מוקד בנק לאומי',
    visibility: 'buyer_side',
    summary: 'מסלול קבוע ל־25 שנה בריבית 3.95%.',
  },
]

const INITIAL_TASKS: DealTask[] = [
  {
    id: 'task-1',
    title: 'סקירת נסח טאבו מעודכן',
    owner: 'עו״ד ליאורה שור',
    status: 'in_progress',
    dueDate: '2024-11-06',
  },
  {
    id: 'task-2',
    title: 'סגירת סעיף פיצוי מוסכם',
    owner: 'עו״ד יוסי בר',
    status: 'blocked',
    dueDate: '2024-11-05',
    blocker: 'ממתינים לאישור המוכר לחלון מסירת הנכס.',
  },
  {
    id: 'task-3',
    title: 'תיאום בדיקה סופית בנכס',
    owner: 'דנה לוי',
    status: 'todo',
    dueDate: '2024-11-12',
  },
  {
    id: 'task-4',
    title: 'איסוף תלושי שכר מעודכנים למשכנתא',
    owner: 'מוקד בנק לאומי',
    status: 'done',
    dueDate: '2024-10-31',
  },
]

const INITIAL_MORTGAGE_OFFERS: MortgageOffer[] = [
  {
    id: 'mortgage-1',
    lender: 'בנק לאומי',
    productType: 'mixed',
    ratePct: 3.95,
    aprPct: 4.12,
    termMonths: 300,
    monthlyPayment: 12_240,
    feesTotal: 4_500,
    validUntil: '2024-11-15T21:00:00Z',
    score: 86,
  },
  {
    id: 'mortgage-2',
    lender: 'מזרחי טפחות',
    productType: 'mixed',
    ratePct: 4.10,
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

const DEAL_METADATA = {
  stage: 'legal' as DealStage,
  askingPrice: 4_500_000,
  acceptedOfferAmount: 4_320_000,
  targetClosingDate: '2025-01-15',
  lastUpdated: '2024-11-03T08:45:00Z',
  address: 'הרצל 17, תל אביב',
}

const TIMELINE_FILTERS = [
  { key: 'all' as const, label: 'כל הפעילות' },
  { key: 'offers' as const, label: 'הצעות' },
  { key: 'documents' as const, label: 'מסמכים' },
  { key: 'tasks' as const, label: 'משימות' },
]

const DOC_FILTERS = [
  { key: 'all' as const, label: 'הכל' },
  { key: 'legal' as const, label: 'משפטי' },
  { key: 'appraisal' as const, label: 'שומה' },
  { key: 'architect' as const, label: 'אדריכל' },
  { key: 'mortgage' as const, label: 'משכנתא' },
]

const DOC_KIND_LABELS: Record<DealDocument['kind'], string> = {
  legal: 'מסמך משפטי',
  appraisal: 'שומת שמאי',
  architect: 'מסמך אדריכלי',
  mortgage: 'מסמכי מימון',
}

const DOC_VISIBILITY_LABELS: Record<DealDocument['visibility'], string> = {
  deal: 'כל הצדדים',
  buyer_side: 'צד הקונה',
  seller_side: 'צד המוכר',
}

const OFFER_STATUS_LABELS: Record<Offer['status'], string> = {
  accepted: 'התקבלה',
  countered: 'הוגשה נגדית',
  pending: 'ממתינה',
  withdrawn: 'נמשכה',
}

const TASK_STATUS_LABELS: Record<DealTask['status'], string> = {
  todo: 'טרם החל',
  in_progress: 'בתהליך',
  blocked: 'חסום',
  done: 'הושלם',
}

const TIMELINE_TYPE_LABELS: Record<TimelineEvent['type'], string> = {
  offer: 'הצעה',
  document: 'מסמך',
  task: 'משימה',
}

const FINANCING_TYPE_LABELS: Record<Offer['financingType'], string> = {
  cash: 'מזומן',
  mortgage: 'משכנתא',
  mixed: 'משולב',
}

const MORTGAGE_PRODUCT_LABELS: Record<MortgageOffer['productType'], string> = {
  fixed: 'קבועה',
  variable: 'משתנה',
  mixed: 'משולבת',
}

function formatDateTime(value: string) {
  const date = new Date(value)
  return new Intl.DateTimeFormat('he-IL', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'Asia/Jerusalem',
  }).format(date)
}

function formatDate(value: string) {
  const date = new Date(value)
  return new Intl.DateTimeFormat('he-IL', {
    dateStyle: 'medium',
    timeZone: 'Asia/Jerusalem',
  }).format(date)
}

type DealWorkspacePageClientProps = {
  assetId: string
}

export default function DealWorkspacePageClient({ assetId }: DealWorkspacePageClientProps) {
  const [offers, setOffers] = useState<Offer[]>(INITIAL_OFFERS)
  const [documents, setDocuments] = useState<DealDocument[]>(INITIAL_DOCUMENTS)
  const [tasks, setTasks] = useState<DealTask[]>(INITIAL_TASKS)
  const [mortgageOffers] = useState<MortgageOffer[]>(INITIAL_MORTGAGE_OFFERS)
  const [timelineFilter, setTimelineFilter] = useState<(typeof TIMELINE_FILTERS)[number]['key']>('all')
  const [docsFilter, setDocsFilter] = useState<(typeof DOC_FILTERS)[number]['key']>('all')
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null)
  const [recommendedMortgageId, setRecommendedMortgageId] = useState<string>('mortgage-1')

  const stageMeta = useMemo(() => STAGE_FLOW.find(stage => stage.key === DEAL_METADATA.stage) ?? STAGE_FLOW[0], [])

  const timelineEvents = useMemo<TimelineEvent[]>(() => {
    const offerEvents = offers.map<TimelineEvent>(offer => ({
      id: `timeline-offer-${offer.id}`,
      type: 'offer',
      title: `${offer.side === 'buyer' ? 'הצעת קונה' : 'הצעת מוכר'} ₪${fmtNumber(offer.amount)}`,
      timestamp: offer.submittedAt,
      description: offer.message,
      side: offer.side,
      statusLabel: OFFER_STATUS_LABELS[offer.status],
    }))

    const documentEvents = documents.map<TimelineEvent>(doc => ({
      id: `timeline-doc-${doc.id}`,
      type: 'document',
      title: `${DOC_KIND_LABELS[doc.kind]} הועלה`,
      timestamp: doc.uploadedAt,
      description: `${doc.title} • ${doc.summary}`,
      side: doc.visibility === 'buyer_side' ? 'buyer' : doc.visibility === 'seller_side' ? 'seller' : 'neutral',
    }))

    const taskEvents = tasks.map<TimelineEvent>(task => ({
      id: `timeline-task-${task.id}`,
      type: 'task',
      title: `משימה ${task.status === 'done' ? 'הושלמה' : 'עודכנה'}`,
      timestamp: `${task.dueDate}T09:00:00Z`,
      description: `${task.title} • אחראי: ${task.owner}`,
      side: 'neutral',
      statusLabel: TASK_STATUS_LABELS[task.status],
    }))

    return [...offerEvents, ...documentEvents, ...taskEvents].sort((a, b) =>
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )
  }, [documents, offers, tasks])

  const filteredTimelineEvents = useMemo(() => {
    if (timelineFilter === 'all') return timelineEvents
    return timelineEvents.filter(event => event.type === timelineFilter.slice(0, -1))
  }, [timelineEvents, timelineFilter])

  const filteredDocuments = useMemo(() => {
    if (docsFilter === 'all') return documents
    return documents.filter(doc => doc.kind === docsFilter)
  }, [docsFilter, documents])

  const documentCounts = useMemo(() => {
    return documents.reduce<Record<string, number>>((acc, doc) => {
      acc[doc.kind] = (acc[doc.kind] ?? 0) + 1
      return acc
    }, {})
  }, [documents])

  const latestOffer = useMemo(() =>
    [...offers].sort((a, b) => new Date(b.submittedAt).getTime() - new Date(a.submittedAt).getTime())[0],
  [offers]
  )

  const handleOfferSubmit = (draft: OfferDraft) => {
    const now = new Date().toISOString()
    const newOffer: Offer = {
      id: `offer-${Date.now()}`,
      submittedAt: now,
      amount: draft.amount,
      downPaymentPct: draft.downPaymentPct,
      financingType: draft.financingType,
      expiresAt: new Date(Date.now() + draft.expiresInHours * 60 * 60 * 1000).toISOString(),
      status: 'pending',
      side: 'buyer',
      message: draft.message || 'טיוטה נוצרה מתוך סביבת העסקה.',
      conditions: draft.conditions,
    }
    setOffers(prev => [newOffer, ...prev])
  }

  const handleLinkDocument = (docId: string) => {
    setDocuments(prev =>
      prev.map(doc =>
        doc.id === docId
          ? { ...doc, linkedOfferId: latestOffer?.id }
          : doc
      )
    )
    setSelectedDocumentId(docId)
  }

  const handleTaskStatusChange = (taskId: string, status: DealTask['status']) => {
    setTasks(prev => prev.map(task => (task.id === taskId ? { ...task, status } : task)))
  }

  const handleRecommendMortgage = (mortgageId: string) => {
    setRecommendedMortgageId(mortgageId)
  }

  const docsSummary = useMemo(() => {
    const legal = documentCounts['legal'] ?? 0
    const appraisal = documentCounts['appraisal'] ?? 0
    const architect = documentCounts['architect'] ?? 0
    const mortgage = documentCounts['mortgage'] ?? 0
    return `${legal} משפטי • ${appraisal} שומה • ${architect} אדריכלי • ${mortgage} מימון`
  }, [documentCounts])

  return (
    <DashboardLayout>
      <DashboardShell>
        <Breadcrumb className='mb-4'>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href='/' className='flex items-center gap-1'>
                <Home className='h-4 w-4' />
                בית
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbLink href='/assets' className='flex items-center gap-1'>
                <Building className='h-4 w-4' />
                נכסים
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbLink href={`/assets/${assetId}`} className='flex items-center gap-1'>
                {DEAL_METADATA.address}
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>סביבת עסקה</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>

        <div className='mb-4 flex justify-end'>
          <Button variant='ghost' size='sm' asChild>
            <Link href={`/assets/${assetId}`}>
              <ArrowLeft className='h-4 w-4 rtl:rotate-180' />
              חזרה לפרטי הנכס
            </Link>
          </Button>
        </div>

        <DashboardHeader
          heading={`סביבת עסקה לנכס ${assetId}`}
          text='נהלו הצעות, מסמכים, משימות ומשכנתאות במבט אחד מרוכז.'
        />

        <div className='grid gap-6 pb-10'>
          <DealHeader
            assetId={assetId}
            address={DEAL_METADATA.address}
            stage={DEAL_METADATA.stage}
            stageMeta={stageMeta}
            parties={PARTIES}
            askingPrice={DEAL_METADATA.askingPrice}
            acceptedOfferAmount={DEAL_METADATA.acceptedOfferAmount}
            targetClosingDate={DEAL_METADATA.targetClosingDate}
            lastUpdated={DEAL_METADATA.lastUpdated}
            documentsCount={documents.length}
          />

          <div className='grid gap-6 lg:grid-cols-[2fr_1fr]'>
            <TimelinePanel
              activeFilter={timelineFilter}
              events={filteredTimelineEvents}
              onFilterChange={setTimelineFilter}
              filterOptions={TIMELINE_FILTERS}
            />

            <DocsPanel
              documents={filteredDocuments}
              allDocuments={documents}
              activeFilter={docsFilter}
              onFilterChange={setDocsFilter}
              onLinkDocument={handleLinkDocument}
              selectedDocumentId={selectedDocumentId}
              summary={docsSummary}
            />
          </div>

          <div className='grid gap-6 lg:grid-cols-[3fr_2fr]'>
            <OfferComposer
              latestOffer={latestOffer}
              onSubmit={handleOfferSubmit}
            />

            <MortgageCompareTable
              offers={mortgageOffers}
              recommendedId={recommendedMortgageId}
              onRecommend={handleRecommendMortgage}
            />
          </div>

          <LegalChecklist
            tasks={tasks}
            onStatusChange={handleTaskStatusChange}
          />
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}

type DealHeaderProps = {
  assetId: string
  address: string
  stage: DealStage
  stageMeta: { key: DealStage; label: string; helper: string }
  parties: Party[]
  askingPrice: number
  acceptedOfferAmount: number
  targetClosingDate: string
  lastUpdated: string
  documentsCount: number
}

function DealHeader({
  assetId,
  address,
  stage,
  stageMeta,
  parties,
  askingPrice,
  acceptedOfferAmount,
  targetClosingDate,
  lastUpdated,
  documentsCount,
}: DealHeaderProps) {
  const stageIndex = STAGE_FLOW.findIndex(item => item.key === stage)

  return (
    <Card>
      <CardHeader className='gap-4'>
        <div className='flex flex-wrap items-center justify-between gap-3'>
          <div>
            <CardTitle className='text-3xl font-semibold'>נכס {assetId}</CardTitle>
            <CardDescription>{address}</CardDescription>
          </div>
          <Badge variant='info' className='flex items-center gap-2'>
            <Gavel className='h-4 w-4' />
            {stageMeta.label}
          </Badge>
        </div>

        <div className='grid gap-4 md:grid-cols-3'>
          <DealHeaderStat
            label='הצעה מאושרת'
            icon={<Handshake className='h-4 w-4 text-primary' />}
            value={fmtCurrency(acceptedOfferAmount)}
            helper={`מול מחיר מבוקש ${fmtCurrency(askingPrice)} (${computeGap(acceptedOfferAmount, askingPrice)})`}
          />
          <DealHeaderStat
            label='תאריך יעד לסגירה'
            icon={<Clock3 className='h-4 w-4 text-primary' />}
            value={formatDate(targetClosingDate)}
            helper={`עודכן לאחרונה ${formatDateTime(lastUpdated)}`}
          />
          <DealHeaderStat
            label='מסמכים בסביבה'
            icon={<FileText className='h-4 w-4 text-primary' />}
            value={`${documentsCount} מסמכים`}
            helper='חלוקת מסמכים לפי צד'
          />
        </div>

        <Separator />

        <div className='flex flex-wrap items-center gap-3'>
          {STAGE_FLOW.map((item, index) => (
            <div key={item.key} className='flex items-center gap-2'>
              <div
                className={cn(
                  'flex h-9 w-9 items-center justify-center rounded-full border text-sm font-semibold',
                  index < stageIndex
                    ? 'bg-primary text-primary-foreground border-primary'
                    : index === stageIndex
                      ? 'border-primary text-primary'
                      : 'border-border text-muted-foreground'
                )}
              >
                {index + 1}
              </div>
              <div>
                <div className='text-sm font-medium'>{item.label}</div>
                <div className='text-xs text-muted-foreground'>{item.helper}</div>
              </div>
            </div>
          ))}
        </div>

        <div className='rounded-lg border bg-muted/40 p-4'>
          <div className='text-sm font-semibold text-muted-foreground'>צדדים מעורבים</div>
          <div className='mt-3 flex flex-wrap gap-2'>
            {parties.map(party => (
              <Badge
                key={party.id}
                variant={party.side === 'buyer' ? 'success' : party.side === 'seller' ? 'secondary' : 'neutral'}
                size='sm'
                className='gap-1'
              >
                <ShieldCheck className='h-3 w-3' />
                {party.role}
                <span className='text-xs text-muted-foreground'>• {party.name}</span>
              </Badge>
            ))}
          </div>
        </div>
      </CardHeader>
    </Card>
  )
}

type DealHeaderStatProps = {
  label: string
  value: string
  helper: string
  icon: React.ReactNode
}

function DealHeaderStat({ label, value, helper, icon }: DealHeaderStatProps) {
  return (
    <div className='rounded-lg border bg-background p-4 shadow-sm'>
      <div className='flex items-center gap-2 text-sm font-medium text-muted-foreground'>
        {icon}
        {label}
      </div>
      <div className='mt-2 text-xl font-semibold'>{value}</div>
      <div className='text-xs text-muted-foreground'>{helper}</div>
    </div>
  )
}

type TimelinePanelProps = {
  events: TimelineEvent[]
  activeFilter: (typeof TIMELINE_FILTERS)[number]['key']
  onFilterChange: (value: (typeof TIMELINE_FILTERS)[number]['key']) => void
  filterOptions: typeof TIMELINE_FILTERS
}

function TimelinePanel({ events, activeFilter, onFilterChange, filterOptions }: TimelinePanelProps) {
  return (
    <Card className='h-full'>
      <CardHeader>
        <CardTitle className='flex items-center gap-2 text-xl'>
          <ArrowRightLeft className='h-5 w-5 text-primary' />
          ציר פעילות העסקה
        </CardTitle>
        <CardDescription>עקבו אחר הצעות, מסמכים ומשימות בזמן אמת.</CardDescription>
      </CardHeader>
      <CardContent className='flex h-full flex-col gap-4'>
        <div className='flex flex-wrap gap-2'>
          {filterOptions.map(option => (
            <Button
              key={option.key}
              variant={option.key === activeFilter ? 'default' : 'outline'}
              size='sm'
              onClick={() => onFilterChange(option.key)}
            >
              {option.label}
            </Button>
          ))}
        </div>

        <div className='space-y-4'>
          {events.map(event => (
            <div key={event.id} className='rounded-lg border bg-background p-4'>
              <div className='flex flex-wrap items-center justify-between gap-2'>
                <div className='flex items-center gap-2'>
                  <Badge
                    size='sm'
                    variant={event.side === 'buyer' ? 'success' : event.side === 'seller' ? 'secondary' : 'neutral'}
                  >
                    {TIMELINE_TYPE_LABELS[event.type]}
                  </Badge>
                  <div className='text-sm font-medium'>{event.title}</div>
                </div>
                <div className='text-xs text-muted-foreground'>{formatDateTime(event.timestamp)}</div>
              </div>
              <p className='mt-2 text-sm text-muted-foreground'>{event.description}</p>
              {event.statusLabel ? (
                <div className='mt-2 text-xs font-semibold text-muted-foreground'>סטטוס: {event.statusLabel}</div>
              ) : null}
            </div>
          ))}
          {events.length === 0 ? (
            <div className='rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground'>
              אין פעילות במסנן הנבחר. נסו לסנן אחרת כדי לראות אירועים נוספים.
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}

type DocsPanelProps = {
  documents: DealDocument[]
  allDocuments: DealDocument[]
  activeFilter: (typeof DOC_FILTERS)[number]['key']
  onFilterChange: (value: (typeof DOC_FILTERS)[number]['key']) => void
  onLinkDocument: (docId: string) => void
  selectedDocumentId: string | null
  summary: string
}

function DocsPanel({
  documents,
  allDocuments,
  activeFilter,
  onFilterChange,
  onLinkDocument,
  selectedDocumentId,
  summary,
}: DocsPanelProps) {
  return (
    <Card className='h-full'>
      <CardHeader>
        <CardTitle className='flex items-center gap-2 text-xl'>
          <FileUp className='h-5 w-5 text-primary' />
          מסמכים ותובנות
        </CardTitle>
        <CardDescription>{summary}</CardDescription>
      </CardHeader>
      <CardContent className='space-y-4'>
        <div className='flex flex-wrap gap-2'>
          {DOC_FILTERS.map(filter => {
            const count = filter.key === 'all'
              ? allDocuments.length
              : allDocuments.filter(doc => doc.kind === filter.key).length
            return (
              <Button
                key={filter.key}
                size='sm'
                variant={filter.key === activeFilter ? 'default' : 'outline'}
                onClick={() => onFilterChange(filter.key)}
              >
                {filter.label}
                <Badge size='sm' variant='outline' className='me-2 border-none bg-transparent text-muted-foreground'>
                  {count}
                </Badge>
              </Button>
            )
          })}
        </div>

        <div className='space-y-3'>
          {documents.map(doc => (
            <div key={doc.id} className='rounded-lg border bg-background p-4'>
              <div className='flex flex-wrap items-center justify-between gap-2'>
                <div>
                  <div className='text-sm font-semibold'>{doc.title}</div>
                  <div className='text-xs text-muted-foreground'>הועלה ב־{formatDateTime(doc.uploadedAt)} • {doc.uploader}</div>
                </div>
                <Badge size='sm' variant={doc.kind === 'legal' ? 'secondary' : doc.kind === 'mortgage' ? 'info' : 'neutral'}>
                  {DOC_KIND_LABELS[doc.kind]}
                </Badge>
              </div>
              <p className='mt-2 text-sm text-muted-foreground'>{doc.summary}</p>
              <div className='mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground'>
                <span>חשיפה: {DOC_VISIBILITY_LABELS[doc.visibility]}</span>
                {doc.linkedOfferId ? <span>מקושר להצעה {doc.linkedOfferId}</span> : null}
              </div>
              <Button
                size='sm'
                className='mt-3'
                variant={selectedDocumentId === doc.id ? 'default' : 'outline'}
                onClick={() => onLinkDocument(doc.id)}
              >
                קשר להצעה האחרונה
              </Button>
            </div>
          ))}
          {documents.length === 0 ? (
            <div className='rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground'>
              אין מסמכים במסנן שנבחר.
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}

type OfferComposerProps = {
  latestOffer?: Offer
  onSubmit: (draft: OfferDraft) => void
}

function OfferComposer({ latestOffer, onSubmit }: OfferComposerProps) {
  const [draft, setDraft] = useState<OfferDraft>(() => ({
    amount: latestOffer?.amount ?? 4_300_000,
    downPaymentPct: latestOffer?.downPaymentPct ?? 30,
    financingType: latestOffer?.financingType ?? 'mixed',
    expiresInHours: 48,
    message: 'ממליצים על זיכוי ₪20 אלף למוצרי חשמל והקדמת מועד הסגירה.',
    conditions: latestOffer?.conditions ?? {
      inspection: true,
      appraisalContingency: true,
      financingContingencyDays: 14,
    },
  }))
  const [statusMessage, setStatusMessage] = useState<string>('')

  useEffect(() => {
    if (!latestOffer) return
    setDraft(prev => ({
      ...prev,
      amount: latestOffer.amount,
      downPaymentPct: latestOffer.downPaymentPct,
      financingType: latestOffer.financingType,
      conditions: latestOffer.conditions,
    }))
  }, [latestOffer])

  const diff = useMemo(() => {
    if (!latestOffer) return [] as { label: string; previous: string; next: string }[]
    const items: { label: string; previous: string; next: string }[] = []
    if (draft.amount !== latestOffer.amount) {
      items.push({
        label: 'סכום ההצעה',
        previous: fmtCurrency(latestOffer.amount),
        next: fmtCurrency(draft.amount),
      })
    }
    if (draft.downPaymentPct !== latestOffer.downPaymentPct) {
      items.push({
        label: 'אחוז הון עצמי',
        previous: `${latestOffer.downPaymentPct}%`,
        next: `${draft.downPaymentPct}%`,
      })
    }
    if (draft.financingType !== latestOffer.financingType) {
      items.push({
        label: 'סוג המימון',
        previous: FINANCING_TYPE_LABELS[latestOffer.financingType],
        next: FINANCING_TYPE_LABELS[draft.financingType],
      })
    }
    if (draft.conditions.financingContingencyDays !== latestOffer.conditions.financingContingencyDays) {
      items.push({
        label: 'תנאי מימון (ימים)',
        previous: `${latestOffer.conditions.financingContingencyDays} ימים`,
        next: `${draft.conditions.financingContingencyDays} ימים`,
      })
    }
    if (draft.conditions.inspection !== latestOffer.conditions.inspection) {
      items.push({
        label: 'בדק בית',
        previous: latestOffer.conditions.inspection ? 'כלול' : 'לא כלול',
        next: draft.conditions.inspection ? 'כלול' : 'לא כלול',
      })
    }
    if (draft.conditions.appraisalContingency !== latestOffer.conditions.appraisalContingency) {
      items.push({
        label: 'תנאי שומה',
        previous: latestOffer.conditions.appraisalContingency ? 'נדרש' : 'בוטל',
        next: draft.conditions.appraisalContingency ? 'נדרש' : 'בוטל',
      })
    }
    return items
  }, [draft, latestOffer])

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSubmit(draft)
    setStatusMessage('טיוטת ההצעה נשמרה בציר הזמן.')
  }

  const handleGenerateSuggestion = () => {
    setDraft(prev => ({
      ...prev,
      amount: prev.amount + 15_000,
      message: 'הצעת המערכת: העלאה קלה במחיר והפחתת תנאי המימון ל־12 ימים.',
      conditions: {
        ...prev.conditions,
        financingContingencyDays: Math.max(12, prev.conditions.financingContingencyDays - 2),
      },
    }))
    setStatusMessage('ההמלצה הוחלה על בסיס עסקאות דומות וקצב ההתקדמות.')
  }

  return (
    <Card className='h-full'>
      <CardHeader>
        <CardTitle className='flex items-center gap-2 text-xl'>
          <Sparkles className='h-5 w-5 text-primary' />
          מחולל הצעות
        </CardTitle>
        <CardDescription>צרו הצעות נגדיות והשוו במהירות להצעה האחרונה שהתקבלה.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className='space-y-4' onSubmit={handleSubmit}>
          <div className='grid gap-4 sm:grid-cols-2'>
            <label className='space-y-1 text-sm font-medium'>
              סכום ההצעה (₪)
              <Input
                value={draft.amount}
                type='number'
                onChange={event => setDraft({ ...draft, amount: Number(event.target.value) })}
              />
            </label>
            <label className='space-y-1 text-sm font-medium'>
              הון עצמי (%)
              <Input
                value={draft.downPaymentPct}
                type='number'
                onChange={event => setDraft({ ...draft, downPaymentPct: Number(event.target.value) })}
              />
            </label>
            <label className='space-y-1 text-sm font-medium'>
              סוג מימון
              <div className='flex gap-2'>
                {(['cash', 'mortgage', 'mixed'] as const).map(option => (
                  <Button
                    key={option}
                    type='button'
                    size='sm'
                    variant={draft.financingType === option ? 'default' : 'outline'}
                    onClick={() => setDraft({ ...draft, financingType: option })}
                    aria-pressed={draft.financingType === option}
                  >
                    {FINANCING_TYPE_LABELS[option]}
                  </Button>
                ))}
              </div>
            </label>
            <label className='space-y-1 text-sm font-medium'>
              תוקף (שעות)
              <Input
                value={draft.expiresInHours}
                type='number'
                onChange={event => setDraft({ ...draft, expiresInHours: Number(event.target.value) })}
              />
            </label>
          </div>

          <div className='grid gap-4 md:grid-cols-3'>
            <ConditionToggle
              label='בדק בית'
              description='השאר תנאי בדיקת נכס'
              active={draft.conditions.inspection}
              onToggle={() =>
                setDraft(prev => ({
                  ...prev,
                  conditions: { ...prev.conditions, inspection: !prev.conditions.inspection },
                }))
              }
            />
            <ConditionToggle
              label='שומת שמאי'
              description='דרוש שומת שמאי מעודכנת'
              active={draft.conditions.appraisalContingency}
              onToggle={() =>
                setDraft(prev => ({
                  ...prev,
                  conditions: { ...prev.conditions, appraisalContingency: !prev.conditions.appraisalContingency },
                }))
              }
            />
            <label className='space-y-1 text-sm font-medium'>
              תנאי מימון (ימים)
              <Input
                value={draft.conditions.financingContingencyDays}
                type='number'
                onChange={event =>
                  setDraft(prev => ({
                    ...prev,
                    conditions: {
                      ...prev.conditions,
                      financingContingencyDays: Number(event.target.value),
                    },
                  }))
                }
              />
            </label>
          </div>

          <label className='space-y-1 text-sm font-medium'>
            הודעה למוכר
            <Textarea
              value={draft.message}
              rows={4}
              onChange={event => setDraft({ ...draft, message: event.target.value })}
            />
          </label>

          <div className='space-y-3 rounded-lg border bg-muted/40 p-4'>
            <div className='text-sm font-semibold text-muted-foreground'>השוואה להצעה האחרונה</div>
            {latestOffer ? (
              diff.length > 0 ? (
                <ul className='space-y-2 text-sm'>
                  {diff.map(item => (
                    <li key={item.label} className='flex items-center justify-between rounded-md bg-background p-2'>
                      <div className='font-medium'>{item.label}</div>
                      <div className='text-xs text-muted-foreground'>
                        <span className='me-2 line-through decoration-muted'>{item.previous}</span>
                        <span className='font-semibold text-primary'>{item.next}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className='text-sm text-muted-foreground'>לא זוהו שינויים ביחס להצעה שהתקבלה.</p>
              )
            ) : (
              <p className='text-sm text-muted-foreground'>התחילו לנסח הצעה כדי לראות השוואות.</p>
            )}
          </div>

          {statusMessage ? <div className='text-sm text-emerald-600'>{statusMessage}</div> : null}

          <div className='flex flex-wrap items-center gap-3'>
            <Button type='submit' className='flex items-center gap-2'>
              <CheckCircle2 className='h-4 w-4' /> שמור טיוטת הצעה
            </Button>
            <Button type='button' variant='outline' onClick={handleGenerateSuggestion} className='flex items-center gap-2'>
              <Sparkles className='h-4 w-4 text-primary' /> הצע שיפור אוטומטי
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

type ConditionToggleProps = {
  label: string
  description: string
  active: boolean
  onToggle: () => void
}

function ConditionToggle({ label, description, active, onToggle }: ConditionToggleProps) {
  return (
    <button
      type='button'
      onClick={onToggle}
      className={cn(
        'rounded-lg border p-4 text-left transition-colors',
        active ? 'border-primary bg-primary/10' : 'border-dashed border-muted-foreground/50'
      )}
      aria-pressed={active}
    >
      <div className='text-sm font-semibold'>{label}</div>
      <div className='text-xs text-muted-foreground'>{description}</div>
      <div className='mt-2 text-xs font-medium text-primary'>{active ? 'כלול' : 'לא כלול'}</div>
    </button>
  )
}

type MortgageCompareTableProps = {
  offers: MortgageOffer[]
  recommendedId: string
  onRecommend: (id: string) => void
}

function MortgageCompareTable({ offers, recommendedId, onRecommend }: MortgageCompareTableProps) {
  return (
    <Card className='h-full'>
      <CardHeader>
        <CardTitle className='flex items-center gap-2 text-xl'>
          <Layers className='h-5 w-5 text-primary' />
          השוואת משכנתאות
        </CardTitle>
        <CardDescription>השוו בין הצעות הבנקים ובחרו את מסלול המימון המתאים ביותר.</CardDescription>
      </CardHeader>
      <CardContent className='space-y-4'>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>בנק</TableHead>
              <TableHead>מסלול</TableHead>
              <TableHead>ריבית</TableHead>
              <TableHead>APR</TableHead>
              <TableHead>תשלום חודשי</TableHead>
              <TableHead>עמלות</TableHead>
              <TableHead>ציון</TableHead>
              <TableHead>בחירה</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {offers.map(offer => (
              <TableRow key={offer.id} className={cn(recommendedId === offer.id && 'border-primary/70 bg-primary/5')}> 
                <TableCell className='font-semibold'>{offer.lender}</TableCell>
                <TableCell>{MORTGAGE_PRODUCT_LABELS[offer.productType]}</TableCell>
                <TableCell>{offer.ratePct.toFixed(2)}%</TableCell>
                <TableCell>{offer.aprPct.toFixed(2)}%</TableCell>
                <TableCell>{fmtCurrency(offer.monthlyPayment)}</TableCell>
                <TableCell>{fmtCurrency(offer.feesTotal)}</TableCell>
                <TableCell>
                  <Badge variant={offer.score >= 85 ? 'success' : offer.score >= 75 ? 'info' : 'warning'} size='sm'>
                    {offer.score}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Button
                    size='sm'
                    variant={offer.id === recommendedId ? 'default' : 'outline'}
                    onClick={() => onRecommend(offer.id)}
                  >
                    {offer.id === recommendedId ? 'מסלול מומלץ' : 'סמן כמומלץ'}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <CardFooter className='justify-between px-0 pt-0 text-xs text-muted-foreground'>
          <span>הריביות מוצגות כ-APR כולל הערכת עמלות וביטוחים.</span>
          <span>בתוקף עד {formatDateTime(offers[0].validUntil)}</span>
        </CardFooter>
      </CardContent>
    </Card>
  )
}

type LegalChecklistProps = {
  tasks: DealTask[]
  onStatusChange: (taskId: string, status: DealTask['status']) => void
}

function LegalChecklist({ tasks, onStatusChange }: LegalChecklistProps) {
  const grouped = useMemo(() => {
    return {
      active: tasks.filter(task => task.status !== 'done'),
      completed: tasks.filter(task => task.status === 'done'),
    }
  }, [tasks])

  return (
    <Card>
      <CardHeader>
        <CardTitle className='flex items-center gap-2 text-xl'>
          <ShieldCheck className='h-5 w-5 text-primary' />
          מעקב משפטי וסגירה
        </CardTitle>
        <CardDescription>נהלו חסמים ומשימות קריטיות עד לחתימה וסגירה.</CardDescription>
      </CardHeader>
      <CardContent className='space-y-6'>
        <div className='space-y-3'>
          <div className='text-sm font-semibold text-muted-foreground'>משימות פעילות</div>
          {grouped.active.map(task => (
            <TaskRow key={task.id} task={task} onStatusChange={onStatusChange} />
          ))}
          {grouped.active.length === 0 ? (
            <div className='rounded-lg border border-dashed p-4 text-sm text-muted-foreground'>
              כל המשימות הושלמו. ממתינים לחתימות.
            </div>
          ) : null}
        </div>

        <Separator />

        <div className='space-y-3'>
          <div className='text-sm font-semibold text-muted-foreground'>משימות שהושלמו</div>
          {grouped.completed.map(task => (
            <TaskRow key={task.id} task={task} onStatusChange={onStatusChange} isCompleted />
          ))}
          {grouped.completed.length === 0 ? (
            <div className='rounded-lg border border-dashed p-4 text-sm text-muted-foreground'>
              אין משימות שהושלמו עדיין.
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}

type TaskRowProps = {
  task: DealTask
  onStatusChange: (taskId: string, status: DealTask['status']) => void
  isCompleted?: boolean
}

function TaskRow({ task, onStatusChange, isCompleted }: TaskRowProps) {
  const statusVariant: 'warning' | 'success' | 'info' =
    task.status === 'blocked' ? 'warning' : task.status === 'done' ? 'success' : 'info'

  return (
    <div className='rounded-lg border bg-background p-4'>
      <div className='flex flex-wrap items-center justify-between gap-2'>
        <div>
          <div className='text-sm font-semibold'>{task.title}</div>
          <div className='text-xs text-muted-foreground'>אחראי: {task.owner} • יעד {formatDate(task.dueDate)}</div>
        </div>
        <Badge size='sm' variant={statusVariant}>{TASK_STATUS_LABELS[task.status]}</Badge>
      </div>
      {task.blocker ? <p className='mt-2 text-xs text-amber-600'>{task.blocker}</p> : null}
      <div className='mt-3 flex flex-wrap items-center gap-2'>
        {!isCompleted ? (
          <>
            <Button size='sm' variant='outline' onClick={() => onStatusChange(task.id, 'in_progress')}>
              סמן כבתהליך
            </Button>
            <Button size='sm' variant='outline' onClick={() => onStatusChange(task.id, 'blocked')}>
              דווח על חסם
            </Button>
            <Button size='sm' onClick={() => onStatusChange(task.id, 'done')}>
              סמן כהושלם
            </Button>
          </>
        ) : (
          <Button size='sm' variant='outline' onClick={() => onStatusChange(task.id, 'todo')}>
            פתח משימה מחדש
          </Button>
        )}
      </div>
    </div>
  )
}

function computeGap(accepted: number, asking: number) {
  const delta = ((accepted - asking) / asking) * 100
  const formatted = delta >= 0 ? `+${delta.toFixed(1)}%` : `${delta.toFixed(1)}%`
  return formatted
}
