'use client'

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
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
import type { DealStage } from '@/lib/deals/types'
import {
  DEAL_METADATA,
  INITIAL_DOCUMENTS,
  INITIAL_MORTGAGE_OFFERS,
  INITIAL_OFFERS,
  INITIAL_TASKS,
  PARTIES,
  type DealDocument,
  type DocumentKind,
  type DocumentStatus,
  type DocumentVisibility,
  type OfferConditions,
  type DealTask,
  type MortgageOffer,
  type Offer,
  type Party,
} from './mock-data'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import { PersistentBreadcrumb, type PersistentBreadcrumbItemType } from '@/components/ui/persistent-breadcrumb'
import {
  ArrowRightLeft,
  ArrowLeft,
  CheckCircle2,
  Clock3,
  Download,
  FileText,
  FileUp,
  Gavel,
  Handshake,
  Layers,
  AlertCircle,
  UploadCloud,
  Loader2,
  ShieldCheck,
  Sparkles,
  Home,
  Building,
  Briefcase,
  Trash2,
} from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { authAPI } from '@/lib/auth'

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

type BackendDealSummary = {
  id: number
  stage?: DealStage
}

type BackendDocument = {
  id: number
  deal?: number | null
  asset?: number | null
  kind: DocumentKind
  title: string
  storage_url?: string
  visibility_scope: DocumentVisibility
  status?: DocumentStatus
  created_at?: string
  updated_at?: string
  extracted_json?: Record<string, unknown> | null
}

type UploadFormState = {
  title: string
  kind: DocumentKind
  visibility: DocumentVisibility
  file: File | null
}

const STAGE_FLOW: { key: DealStage; label: string; helper: string }[] = [
  { key: 'discovery', label: 'איתור והערכה', helper: 'איסוף חומר רקע והכנת הנכס לעסקה' },
  { key: 'negotiation', label: 'מו״מ', helper: 'ניהול הצעות נגדיות ודיוקים במחיר' },
  { key: 'legal', label: 'משפטי', helper: 'טיוטות חוזה, הערות וחתימות' },
  { key: 'financing', label: 'מימון', helper: 'בדיקת מסלולים ואישורי אשראי' },
  { key: 'closing', label: 'סגירה', helper: 'מסירת נכס והתחשבנות' },
]

const TIMELINE_FILTERS = [
  { key: 'all' as const, label: 'כל הפעילות' },
  { key: 'offers' as const, label: 'הצעות' },
  { key: 'documents' as const, label: 'מסמכים' },
  { key: 'tasks' as const, label: 'משימות' },
]

type DocFilterKey = 'all' | DocumentKind

const DOC_FILTERS: { key: DocFilterKey; label: string }[] = [
  { key: 'all', label: 'הכל' },
  { key: 'legal', label: 'משפטי' },
  { key: 'appraisal', label: 'שומה' },
  { key: 'architect', label: 'אדריכל' },
  { key: 'mortgage', label: 'משכנתא' },
  { key: 'generic', label: 'אחר' },
]

const DOC_KIND_LABELS: Record<DocumentKind, string> = {
  legal: 'מסמך משפטי',
  appraisal: 'שומת שמאי',
  architect: 'מסמך אדריכלי',
  mortgage: 'מסמכי מימון',
  generic: 'מסמך נוסף',
}

const DOC_VISIBILITY_LABELS: Record<DocumentVisibility, string> = {
  deal: 'כל הצדדים',
  buyer_side: 'צד הקונה',
  seller_side: 'צד המוכר',
}

const DOC_STATUS_LABELS: Record<DocumentStatus, string> = {
  processing: 'בטיפול',
  ready: 'מוכן להורדה',
  failed: 'העלאה נכשלה',
}

const DEFAULT_UPLOAD_FORM: UploadFormState = {
  title: '',
  kind: 'legal',
  visibility: 'deal',
  file: null,
}

function mapBackendDocument(doc: BackendDocument): DealDocument {
  const uploadedAt = doc.updated_at || doc.created_at || new Date().toISOString()
  const extracted = doc.extracted_json || {}
  const summaryCandidate = typeof (extracted as Record<string, unknown>).summary === 'string'
    ? (extracted as Record<string, string>).summary
    : typeof (extracted as Record<string, unknown>).notes === 'string'
      ? (extracted as Record<string, string>).notes
      : null
  const uploaderCandidate = typeof (extracted as Record<string, unknown>).uploader === 'string'
    ? (extracted as Record<string, string>).uploader
    : typeof (extracted as Record<string, unknown>).uploader_name === 'string'
      ? (extracted as Record<string, string>).uploader_name
      : null
  const linkedOfferCandidate = typeof (extracted as Record<string, unknown>).linked_offer_id === 'string'
    ? (extracted as Record<string, string>).linked_offer_id
    : undefined

  return {
    id: String(doc.id),
    title: doc.title,
    kind: doc.kind,
    uploadedAt,
    uploader: uploaderCandidate || 'צוות העסקה',
    visibility: doc.visibility_scope,
    summary: summaryCandidate || 'מסמך נוסף שנוסף לסביבת העסקה.',
    linkedOfferId: linkedOfferCandidate,
    status: doc.status || 'processing',
    storageUrl: doc.storage_url,
  }
}

function statusBadgeVariant(status: DocumentStatus): 'success' | 'info' | 'destructive' {
  switch (status) {
    case 'ready':
      return 'success'
    case 'failed':
      return 'destructive'
    default:
      return 'info'
  }
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
  const searchParams = useSearchParams()
  const [offers, setOffers] = useState<Offer[]>(INITIAL_OFFERS)
  const [documents, setDocuments] = useState<DealDocument[]>(() => [...INITIAL_DOCUMENTS])
  const [tasks, setTasks] = useState<DealTask[]>(INITIAL_TASKS)
  const [mortgageOffers] = useState<MortgageOffer[]>(INITIAL_MORTGAGE_OFFERS)
  const [timelineFilter, setTimelineFilter] = useState<(typeof TIMELINE_FILTERS)[number]['key']>('all')
  const [docsFilter, setDocsFilter] = useState<DocFilterKey>('all')
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null)
  const [recommendedMortgageId, setRecommendedMortgageId] = useState<string>('mortgage-1')
  const [dealId, setDealId] = useState<number | null>(null)
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [documentsError, setDocumentsError] = useState<string | null>(null)
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false)
  const [uploadForm, setUploadForm] = useState<UploadFormState>(DEFAULT_UPLOAD_FORM)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  useEffect(() => {
    let cancelled = false

    const fetchDocuments = async () => {
      setDocumentsLoading(true)
      setDocumentsError(null)
      try {
        const dealsResponse = await apiClient.get<{ deals?: BackendDealSummary[] }>(
          `/api/deals?asset_id=${assetId}`
        )
        if (cancelled) return

        const dealsList = Array.isArray(dealsResponse.data?.deals)
          ? dealsResponse.data?.deals
          : []
        const activeDeal = dealsList?.[0]

        if (!activeDeal?.id) {
          setDealId(null)
          setDocuments([...INITIAL_DOCUMENTS])
          setDocumentsError('לא נמצאה סביבת עסקה פעילה לנכס זה.')
          return
        }

        setDealId(activeDeal.id)

        const docsResponse = await apiClient.get<{ documents?: BackendDocument[] }>(
          `/api/deal-workspace/documents?deal_id=${activeDeal.id}`
        )
        if (cancelled) return

        if (docsResponse.ok && docsResponse.data) {
          const raw = (docsResponse.data as { documents?: BackendDocument[] })?.documents
          const payload = Array.isArray(raw)
            ? raw
            : Array.isArray(docsResponse.data)
              ? (docsResponse.data as BackendDocument[])
              : []

          if (payload.length > 0) {
            setDocuments(payload.map(mapBackendDocument))
          } else {
            setDocuments([])
          }
          setDocumentsError(null)
        } else {
          setDocuments([...INITIAL_DOCUMENTS])
          setDocumentsError(
            docsResponse.error || 'כשל בטעינת המסמכים - מוצגים נתוני דמו.'
          )
        }
      } catch (error) {
        if (cancelled) return
        console.error('Failed to load deal workspace documents:', error)
        setDocuments([...INITIAL_DOCUMENTS])
        setDocumentsError('כשל בטעינת המסמכים - מוצגים נתוני דמו.')
      } finally {
        if (!cancelled) {
          setDocumentsLoading(false)
        }
      }
    }

    fetchDocuments()

    return () => {
      cancelled = true
    }
  }, [assetId])

  const handleUploadDialogChange = useCallback((open: boolean) => {
    setIsUploadDialogOpen(open)
    if (!open) {
      setUploadForm({ ...DEFAULT_UPLOAD_FORM })
      setUploadError(null)
      setIsUploading(false)
    }
  }, [])

  const handleUploadSubmit = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      if (!uploadForm.file) {
        setUploadError('בחרו קובץ להעלאה.')
        return
      }
      if (!dealId) {
        setUploadError('לא נמצאה סביבת עסקה פעילה להעלאת מסמך.')
        return
      }

      setIsUploading(true)
      setUploadError(null)

      const formData = new FormData()
      formData.append('file', uploadForm.file)
      formData.append('deal_id', String(dealId))
      formData.append('asset_id', assetId)
      formData.append('kind', uploadForm.kind)
      formData.append('visibility', uploadForm.visibility)
      const derivedTitle = uploadForm.title.trim() || uploadForm.file.name || 'מסמך'
      formData.append('title', derivedTitle)

      try {
        const response = await apiClient.request<{ document?: BackendDocument }>(
          '/api/deal-workspace/documents/upload',
          {
            method: 'POST',
            body: formData,
          }
        )

        if (!response.ok || !response.data?.document) {
          throw new Error(response.error || 'ההעלאה נכשלה')
        }

        const backendDoc = response.data.document as BackendDocument
        setDocuments(prev => [mapBackendDocument(backendDoc), ...prev])
        setDocumentsError(null)
        handleUploadDialogChange(false)
      } catch (error) {
        console.error('Failed to upload deal workspace document:', error)
        setUploadError(error instanceof Error ? error.message : 'ההעלאה נכשלה')
      } finally {
        setIsUploading(false)
      }
    },
    [assetId, dealId, handleUploadDialogChange, uploadForm.file, uploadForm.kind, uploadForm.title, uploadForm.visibility]
  )

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
    return documents.reduce<Partial<Record<DocumentKind, number>>>((acc, doc) => {
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

  const handleDocumentDeleted = useCallback(async () => {
    // Refresh documents list after deletion
    if (!dealId) return
    setDocumentsLoading(true)
    setDocumentsError(null)
    try {
      const docsResponse = await apiClient.get<{ documents?: BackendDocument[] }>(
        `/api/deal-workspace/documents?deal_id=${dealId}`
      )

      if (docsResponse.ok && docsResponse.data) {
        const raw = (docsResponse.data as { documents?: BackendDocument[] })?.documents
        const payload = Array.isArray(raw)
          ? raw
          : Array.isArray(docsResponse.data)
            ? (docsResponse.data as BackendDocument[])
            : []

        if (payload.length > 0) {
          setDocuments(payload.map(mapBackendDocument))
        } else {
          setDocuments([])
        }
        setDocumentsError(null)
      }
    } catch (error) {
      console.error('Failed to refresh documents:', error)
    } finally {
      setDocumentsLoading(false)
    }
  }, [dealId])

  const docsSummary = useMemo(() => {
    const parts = DOC_FILTERS.filter(filter => filter.key !== 'all').map(filter => {
      const key = filter.key as DocumentKind
      const count = documentCounts[key] ?? 0
      return `${count} ${filter.label}`
    })
    return parts.join(' • ')
  }, [documentCounts])

  const [navigationSource, setNavigationSource] = useState<'deals' | 'asset'>('asset')

  useEffect(() => {
    // Check for explicit 'from' query parameter first
    const fromParam = searchParams.get('from')
    if (fromParam === 'deals') {
      setNavigationSource('deals')
      return
    }
    // Fallback to checking document.referrer if available
    if (typeof window !== 'undefined' && document.referrer) {
      try {
        const referrerUrl = new URL(document.referrer)
        if (referrerUrl.pathname === '/deals') {
          setNavigationSource('deals')
          return
        }
      } catch {
        // Ignore invalid URLs
      }
    }
    // Default to asset details
    setNavigationSource('asset')
  }, [searchParams])

  const breadcrumbItems: PersistentBreadcrumbItemType[] = useMemo(() => {
    if (navigationSource === 'deals') {
      return [
        { label: 'בית', href: '/', icon: Home },
        { label: 'עסקאות', href: '/deals', icon: Briefcase },
        { label: 'סביבת עסקה' },
      ]
    }
    // Default: from asset details
    return [
      { label: 'בית', href: '/', icon: Home },
      { label: 'נכסים', href: '/assets', icon: Building },
      { label: DEAL_METADATA.address, href: `/assets/${assetId}` },
      { label: 'סביבת עסקה' },
    ]
  }, [navigationSource, assetId])

  return (
    <DashboardLayout>
      <DashboardShell>
        <PersistentBreadcrumb
          items={breadcrumbItems}
          showBackToAssets={true}
        />

        <DashboardHeader
          heading={`סביבת עסקה לנכס ${DEAL_METADATA.address}`}
          text='נהלו הצעות, מסמכים, משימות ומשכנתאות במבט אחד מרוכז.'
        />

        <div className='grid gap-4 sm:gap-6 pb-6 sm:pb-10 min-w-0'>
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

          <div className='grid gap-4 sm:gap-6 md:grid-cols-[2fr_1fr] lg:grid-cols-[2fr_1fr] min-w-0'>
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
              onUploadClick={() => setIsUploadDialogOpen(true)}
              isLoading={documentsLoading}
              error={documentsError}
              assetId={assetId}
              onDocumentDeleted={handleDocumentDeleted}
            />
          </div>

          <div className='grid gap-4 sm:gap-6 md:grid-cols-[3fr_2fr] lg:grid-cols-[3fr_2fr] min-w-0'>
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
      <Dialog open={isUploadDialogOpen} onOpenChange={handleUploadDialogChange}>
        <DialogContent className='mx-4 sm:mx-0 max-w-[calc(100vw-2rem)] sm:max-w-lg'>
          <DialogHeader>
            <DialogTitle className='text-lg sm:text-xl'>העלה מסמך חדש לסביבת העסקה</DialogTitle>
            <DialogDescription className='text-sm'>
              צרפו מסמכי משכנתא, מסמכים משפטיים או חומרים נוספים לזמינות לכלל צוות העסקה.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleUploadSubmit} className='space-y-3 sm:space-y-4'>
            <div className='space-y-2'>
              <Label htmlFor='document-title'>כותרת המסמך</Label>
              <Input
                id='document-title'
                value={uploadForm.title}
                onChange={event => setUploadForm(prev => ({ ...prev, title: event.target.value }))}
                placeholder={uploadForm.file?.name || 'לדוגמה: אישור משכנתא'}
              />
            </div>
            <div className='grid gap-4 md:grid-cols-2'>
              <div className='space-y-2'>
                <Label>סוג המסמך</Label>
                <Select
                  value={uploadForm.kind}
                  onValueChange={value =>
                    setUploadForm(prev => ({ ...prev, kind: value as DocumentKind }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder='בחרו סוג מסמך' />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value='mortgage'>מסמכי משכנתא</SelectItem>
                    <SelectItem value='legal'>מסמך משפטי</SelectItem>
                    <SelectItem value='appraisal'>שומת שמאי</SelectItem>
                    <SelectItem value='architect'>מסמך אדריכלי</SelectItem>
                    <SelectItem value='generic'>מסמך אחר</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className='space-y-2'>
                <Label>חשיפה לצדדים</Label>
                <Select
                  value={uploadForm.visibility}
                  onValueChange={value =>
                    setUploadForm(prev => ({ ...prev, visibility: value as DocumentVisibility }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder='בחרו למי המסמך חשוף' />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value='deal'>כל הצדדים</SelectItem>
                    <SelectItem value='buyer_side'>צד הקונה</SelectItem>
                    <SelectItem value='seller_side'>צד המוכר</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className='space-y-2'>
              <Label htmlFor='document-file'>בחר קובץ</Label>
              <Input
                id='document-file'
                type='file'
                accept='.pdf,.doc,.docx,.jpg,.jpeg,.png'
                onChange={event => {
                  const file = event.target.files?.[0] ?? null
                  setUploadForm(prev => ({ ...prev, file }))
                }}
              />
              <p className='text-xs text-muted-foreground'>ניתן להעלות קובצי PDF, Word או תמונה עד 10MB.</p>
            </div>
            {uploadError ? (
              <div className='rounded-md border border-destructive/40 bg-destructive/10 p-2 text-sm text-destructive'>
                {uploadError}
              </div>
            ) : null}
            <DialogFooter className='flex flex-wrap justify-end gap-2'>
              <Button
                type='button'
                variant='outline'
                onClick={() => handleUploadDialogChange(false)}
                disabled={isUploading}
              >
                בטל
              </Button>
              <Button type='submit' disabled={isUploading || !uploadForm.file}>
                {isUploading ? (
                  <>
                    <Loader2 className='h-4 w-4 ms-2 animate-spin' />
                    מעלה...
                  </>
                ) : (
                  'שמור מסמך'
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
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
      <Card className='min-w-0'>
        <CardHeader className='gap-3 sm:gap-4 p-4 sm:p-6'>
          <div className='flex flex-col sm:flex-row sm:flex-wrap sm:items-center sm:justify-between gap-3'>
            <div>
              <CardTitle className='text-2xl sm:text-3xl font-semibold'>נכס {assetId}</CardTitle>
              <CardDescription className='text-sm sm:text-base'>{address}</CardDescription>
            </div>
            <Badge variant='info' className='flex items-center gap-2 w-fit'>
              <Gavel className='h-4 w-4' />
              {stageMeta.label}
            </Badge>
          </div>

          <div className='grid gap-3 sm:gap-4 sm:grid-cols-2 md:grid-cols-3'>
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

        <div className='flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-3 sm:gap-4'>
          {STAGE_FLOW.map((item, index) => (
            <div key={item.key} className='flex items-center gap-2'>
              <div
                className={cn(
                  'flex h-8 w-8 sm:h-9 sm:w-9 items-center justify-center rounded-full border text-xs sm:text-sm font-semibold shrink-0',
                  index < stageIndex
                    ? 'bg-primary text-primary-foreground border-primary'
                    : index === stageIndex
                      ? 'border-primary text-primary'
                      : 'border-border text-muted-foreground'
                )}
              >
                {index + 1}
              </div>
              <div className='min-w-0'>
                <div className='text-xs sm:text-sm font-medium'>{item.label}</div>
                <div className='text-xs text-muted-foreground'>{item.helper}</div>
              </div>
            </div>
          ))}
        </div>

        <div className='rounded-lg border bg-muted/40 p-3 sm:p-4'>
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
    <div className='rounded-lg border bg-background p-3 sm:p-4 shadow-sm'>
      <div className='flex items-center gap-2 text-xs sm:text-sm font-medium text-muted-foreground'>
        {icon}
        {label}
      </div>
      <div className='mt-2 text-lg sm:text-xl font-semibold'>{value}</div>
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
    <Card className='h-full min-w-0'>
      <CardHeader className='p-4 sm:p-6'>
        <CardTitle className='flex items-center gap-2 text-lg sm:text-xl'>
          <ArrowRightLeft className='h-4 w-4 sm:h-5 sm:w-5 text-primary shrink-0' />
          ציר פעילות העסקה
        </CardTitle>
        <CardDescription className='text-xs sm:text-sm'>עקבו אחר הצעות, מסמכים ומשימות בזמן אמת.</CardDescription>
      </CardHeader>
      <CardContent className='flex h-full flex-col gap-3 sm:gap-4 p-4 sm:p-6'>
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

        <div className='space-y-3 sm:space-y-4'>
          {events.map(event => (
            <div key={event.id} className='rounded-lg border bg-background p-3 sm:p-4'>
              <div className='flex flex-col sm:flex-row sm:flex-wrap sm:items-center sm:justify-between gap-2'>
                <div className='flex items-center gap-2 flex-wrap'>
                  <Badge
                    size='sm'
                    variant={event.side === 'buyer' ? 'success' : event.side === 'seller' ? 'secondary' : 'neutral'}
                    className='text-xs'
                  >
                    {TIMELINE_TYPE_LABELS[event.type]}
                  </Badge>
                  <div className='text-xs sm:text-sm font-medium'>{event.title}</div>
                </div>
                <div className='text-xs text-muted-foreground'>{formatDateTime(event.timestamp)}</div>
              </div>
              <p className='mt-2 text-xs sm:text-sm text-muted-foreground'>{event.description}</p>
              {event.statusLabel ? (
                <div className='mt-2 text-xs font-semibold text-muted-foreground'>סטטוס: {event.statusLabel}</div>
              ) : null}
            </div>
          ))}
          {events.length === 0 ? (
            <div className='rounded-lg border border-dashed p-4 sm:p-6 text-center text-xs sm:text-sm text-muted-foreground'>
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
  activeFilter: DocFilterKey
  onFilterChange: (value: DocFilterKey) => void
  onLinkDocument: (docId: string) => void
  selectedDocumentId: string | null
  summary: string
  onUploadClick: () => void
  isLoading: boolean
  error?: string | null
  assetId: string
  onDocumentDeleted?: () => void
}

function DocsPanel({
  documents,
  allDocuments,
  activeFilter,
  onFilterChange,
  onLinkDocument,
  selectedDocumentId,
  summary,
  onUploadClick,
  isLoading,
  error,
  assetId,
  onDocumentDeleted,
}: DocsPanelProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [documentToDelete, setDocumentToDelete] = useState<DealDocument | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const handleDownloadDocument = useCallback(
    async (doc: DealDocument) => {
      if (!doc.storageUrl) {
        console.error('Document has no storage URL')
        return
      }

      try {
        // Get authentication token
        const token = authAPI.getAccessToken()
        if (!token) {
          console.error('No authentication token available')
          return
        }

        let downloadUrl: string

        // Check if storageUrl is a relative URL (starts with /api/assets/)
        if (doc.storageUrl.startsWith('/api/assets/')) {
          // Extract assetId and documentId from relative URL
          // Format: /api/assets/{assetId}/documents/{documentId}/download
          const urlMatch = doc.storageUrl.match(/\/api\/assets\/(\d+)\/documents\/(\d+)\/download/)
          if (urlMatch) {
            const [, urlAssetId, documentId] = urlMatch
            downloadUrl = `/api/assets/${urlAssetId}/documents/${documentId}/download`
          } else {
            // If it's a relative URL but not in the expected format, try to use it directly
            downloadUrl = doc.storageUrl
          }
        } else {
          // Absolute URL - extract the path and construct Next.js API route
          try {
            const url = new URL(doc.storageUrl)
            const pathMatch = url.pathname.match(/\/api\/assets\/(\d+)\/documents\/(\d+)\/download/)
            if (pathMatch) {
              const [, urlAssetId, documentId] = pathMatch
              downloadUrl = `/api/assets/${urlAssetId}/documents/${documentId}/download`
            } else {
              // If we can't extract from URL, try to use the storage_url directly
              // This might be a direct backend URL that we need to proxy
              console.warn('Could not extract IDs from storage URL, using direct fetch:', doc.storageUrl)
              downloadUrl = doc.storageUrl
            }
          } catch {
            // Invalid URL format, use as-is
            downloadUrl = doc.storageUrl
          }
        }

        // Fetch the document with authentication
        const response = await fetch(downloadUrl, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
          },
          credentials: 'include',
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ error: 'Download failed' }))
          console.error('Download failed:', errorData)
          return
        }

        // Get the blob and filename
        const blob = await response.blob()
        const contentDisposition = response.headers.get('Content-Disposition')
        let filename = doc.title || 'document'

        // Extract filename from Content-Disposition header if available
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/i)
          if (filenameMatch) {
            filename = filenameMatch[1]
          }
        }

        // Create download link and trigger download
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error('Error downloading document:', error)
      }
    },
    []
  )

  const handleDeleteClick = useCallback((doc: DealDocument) => {
    setDocumentToDelete(doc)
    setDeleteDialogOpen(true)
  }, [])

  const handleDeleteConfirm = useCallback(async () => {
    if (!documentToDelete) return

    setIsDeleting(true)
    try {
      const response = await apiClient.delete(`/api/deal-workspace/documents/${documentToDelete.id}`)

      if (!response.ok) {
        throw new Error(response.error || 'מחיקת המסמך נכשלה')
      }

      // Remove document from local state
      if (onDocumentDeleted) {
        onDocumentDeleted()
      }

      setDeleteDialogOpen(false)
      setDocumentToDelete(null)
    } catch (error) {
      console.error('Failed to delete document:', error)
      alert(error instanceof Error ? error.message : 'מחיקת המסמך נכשלה')
    } finally {
      setIsDeleting(false)
    }
  }, [documentToDelete, onDocumentDeleted])

  const handleDeleteCancel = useCallback(() => {
    setDeleteDialogOpen(false)
    setDocumentToDelete(null)
  }, [])

  return (
    <Card className='h-full min-w-0'>
      <CardHeader className='p-4 sm:p-6'>
        <CardTitle className='flex items-center gap-2 text-lg sm:text-xl'>
          <FileUp className='h-4 w-4 sm:h-5 sm:w-5 text-primary shrink-0' />
          מסמכים ותובנות
        </CardTitle>
        <CardDescription className='text-xs sm:text-sm'>{summary}</CardDescription>
      </CardHeader>
      <CardContent className='space-y-3 sm:space-y-4 p-4 sm:p-6'>
        <div className='flex flex-wrap items-center justify-between gap-3'>
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
          <Button size='sm' onClick={onUploadClick} variant='default'>
            <UploadCloud className='h-4 w-4 ms-2' />
            העלה מסמך
          </Button>
        </div>

        {error ? (
          <div className='flex items-center gap-2 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-xs sm:text-sm text-destructive'>
            <AlertCircle className='h-4 w-4 shrink-0' />
            {error}
          </div>
        ) : null}

        {isLoading ? (
          <div className='rounded-lg border border-dashed p-4 sm:p-6 text-center text-xs sm:text-sm text-muted-foreground'>
            <Loader2 className='me-2 inline h-4 w-4 animate-spin' />
            טוען מסמכים...
          </div>
        ) : (
          <div className='space-y-3'>
            {documents.map(doc => (
              <div key={doc.id} className='rounded-lg border bg-background p-3 sm:p-4'>
                <div className='flex flex-col sm:flex-row sm:flex-wrap sm:items-center sm:justify-between gap-2'>
                  <div className='min-w-0 flex-1'>
                    <div className='text-xs sm:text-sm font-semibold'>{doc.title}</div>
                    <div className='text-xs text-muted-foreground'>הועלה ב־{formatDateTime(doc.uploadedAt)} • {doc.uploader}</div>
                  </div>
                  <div className='flex items-center gap-2 flex-wrap'>
                    <Badge size='sm' variant={doc.kind === 'legal' ? 'secondary' : doc.kind === 'mortgage' ? 'info' : 'neutral'}>
                      {DOC_KIND_LABELS[doc.kind]}
                    </Badge>
                    {doc.status ? (
                      <Badge size='sm' variant={statusBadgeVariant(doc.status)}>
                        {DOC_STATUS_LABELS[doc.status]}
                      </Badge>
                    ) : null}
                  </div>
                </div>
                <p className='mt-2 text-sm text-muted-foreground'>{doc.summary}</p>
                <div className='mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground'>
                  <span>חשיפה: {DOC_VISIBILITY_LABELS[doc.visibility]}</span>
                  {doc.linkedOfferId ? <span>מקושר להצעה {doc.linkedOfferId}</span> : null}
                </div>
                <div className='mt-3 flex flex-wrap gap-2'>
                  <Button
                    size='sm'
                    variant={selectedDocumentId === doc.id ? 'default' : 'outline'}
                    onClick={() => onLinkDocument(doc.id)}
                  >
                    קשר להצעה האחרונה
                  </Button>
                  <Button
                    size='sm'
                    variant='outline'
                    disabled={!doc.storageUrl}
                    onClick={() => handleDownloadDocument(doc)}
                  >
                    <Download className='h-4 w-4 ms-2' />
                    הורד מסמך
                  </Button>
                  <Button
                    size='sm'
                    variant='outline'
                    onClick={() => handleDeleteClick(doc)}
                    className='text-destructive hover:text-destructive hover:bg-destructive/10'
                  >
                    <Trash2 className='h-4 w-4 ms-2' />
                    מחק
                  </Button>
                </div>
              </div>
            ))}
            <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>מחיקת מסמך</AlertDialogTitle>
                  <AlertDialogDescription>
                    האם אתם בטוחים שברצונכם למחוק את המסמך "{documentToDelete?.title}"? פעולה זו לא ניתנת לביטול.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel onClick={handleDeleteCancel} disabled={isDeleting}>
                    בטל
                  </AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleDeleteConfirm}
                    disabled={isDeleting}
                    className='bg-destructive text-destructive-foreground hover:bg-destructive/90'
                  >
                    {isDeleting ? (
                      <>
                        <Loader2 className='h-4 w-4 ms-2 animate-spin' />
                        מוחק...
                      </>
                    ) : (
                      'מחק'
                    )}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
            {documents.length === 0 ? (
              <div className='rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground'>
                אין מסמכים במסנן שנבחר.
              </div>
            ) : null}
          </div>
        )}
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
    <Card className='h-full min-w-0'>
      <CardHeader className='p-4 sm:p-6'>
        <CardTitle className='flex items-center gap-2 text-lg sm:text-xl'>
          <Sparkles className='h-4 w-4 sm:h-5 sm:w-5 text-primary shrink-0' />
          מחולל הצעות
        </CardTitle>
        <CardDescription className='text-xs sm:text-sm'>צרו הצעות נגדיות והשוו במהירות להצעה האחרונה שהתקבלה.</CardDescription>
      </CardHeader>
      <CardContent className='p-4 sm:p-6'>
        <form className='space-y-3 sm:space-y-4' onSubmit={handleSubmit}>
          <div className='grid gap-3 sm:gap-4 sm:grid-cols-2'>
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

          <div className='grid gap-3 sm:gap-4 sm:grid-cols-2 md:grid-cols-3'>
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

          <div className='space-y-3 rounded-lg border bg-muted/40 p-3 sm:p-4'>
            <div className='text-xs sm:text-sm font-semibold text-muted-foreground'>השוואה להצעה האחרונה</div>
            {latestOffer ? (
              diff.length > 0 ? (
                <ul className='space-y-2 text-xs sm:text-sm'>
                  {diff.map(item => (
                    <li key={item.label} className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 rounded-md bg-background p-2'>
                      <div className='font-medium'>{item.label}</div>
                      <div className='text-xs text-muted-foreground'>
                        <span className='me-2 line-through decoration-muted'>{item.previous}</span>
                        <span className='font-semibold text-primary'>{item.next}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className='text-xs sm:text-sm text-muted-foreground'>לא זוהו שינויים ביחס להצעה שהתקבלה.</p>
              )
            ) : (
              <p className='text-xs sm:text-sm text-muted-foreground'>התחילו לנסח הצעה כדי לראות השוואות.</p>
            )}
          </div>

          {statusMessage ? <div className='text-xs sm:text-sm text-emerald-600'>{statusMessage}</div> : null}

          <div className='flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-2 sm:gap-3'>
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
        'rounded-lg border p-3 sm:p-4 text-left transition-colors w-full',
        active ? 'border-primary bg-primary/10' : 'border-dashed border-muted-foreground/50'
      )}
      aria-pressed={active}
    >
      <div className='text-xs sm:text-sm font-semibold'>{label}</div>
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
    <Card className='h-full min-w-0'>
      <CardHeader className='p-4 sm:p-6'>
        <CardTitle className='flex items-center gap-2 text-lg sm:text-xl'>
          <Layers className='h-4 w-4 sm:h-5 sm:w-5 text-primary shrink-0' />
          השוואת משכנתאות
        </CardTitle>
        <CardDescription className='text-xs sm:text-sm'>השוו בין הצעות הבנקים ובחרו את מסלול המימון המתאים ביותר.</CardDescription>
      </CardHeader>
      <CardContent className='space-y-3 sm:space-y-4 p-4 sm:p-6'>
        <div className='overflow-x-auto'>
          <Table>
          <TableHeader>
            <TableRow>
              <TableHead>בנק</TableHead>
              <TableHead>מסלול</TableHead>
              <TableHead>ריבית</TableHead>
              <TableHead>ריבית בפועל</TableHead>
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
        </div>
        <CardFooter className='flex-col sm:flex-row justify-between gap-2 sm:gap-0 px-0 pt-3 sm:pt-0 text-xs text-muted-foreground'>
          <span>הריביות מוצגות כריבית בפועל כולל הערכת עמלות וביטוחים.</span>
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
    <Card className='min-w-0'>
      <CardHeader className='p-4 sm:p-6'>
        <CardTitle className='flex items-center gap-2 text-lg sm:text-xl'>
          <ShieldCheck className='h-4 w-4 sm:h-5 sm:w-5 text-primary shrink-0' />
          מעקב משפטי וסגירה
        </CardTitle>
        <CardDescription className='text-xs sm:text-sm'>נהלו חסמים ומשימות קריטיות עד לחתימה וסגירה.</CardDescription>
      </CardHeader>
      <CardContent className='space-y-4 sm:space-y-6 p-4 sm:p-6'>
        <div className='space-y-3'>
          <div className='text-sm font-semibold text-muted-foreground'>משימות פעילות</div>
          {grouped.active.map(task => (
            <TaskRow key={task.id} task={task} onStatusChange={onStatusChange} />
          ))}
          {grouped.active.length === 0 ? (
            <div className='rounded-lg border border-dashed p-3 sm:p-4 text-xs sm:text-sm text-muted-foreground'>
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
            <div className='rounded-lg border border-dashed p-3 sm:p-4 text-xs sm:text-sm text-muted-foreground'>
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
    <div className='rounded-lg border bg-background p-3 sm:p-4'>
      <div className='flex flex-col sm:flex-row sm:flex-wrap sm:items-center sm:justify-between gap-2'>
        <div className='min-w-0 flex-1'>
          <div className='text-xs sm:text-sm font-semibold'>{task.title}</div>
          <div className='text-xs text-muted-foreground'>אחראי: {task.owner} • יעד {formatDate(task.dueDate)}</div>
        </div>
        <Badge size='sm' variant={statusVariant} className='w-fit'>{TASK_STATUS_LABELS[task.status]}</Badge>
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
