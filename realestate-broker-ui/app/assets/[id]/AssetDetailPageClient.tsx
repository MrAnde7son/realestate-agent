'use client'
import React, { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAnalytics } from '@/hooks/useAnalytics'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
  CardBody,
} from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import DataBadge from '@/components/DataBadge'
import * as Tooltip from '@radix-ui/react-tooltip'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { PageLoader } from '@/components/ui/page-loader'
import { ArrowLeft, RefreshCw, FileText, Loader2, Home, Building, Phone } from 'lucide-react'
import ImageGallery from '@/components/ImageGallery'
import { useAuth } from '@/lib/auth-context'
import { apiClient } from '@/lib/api-client'
import { useDedupedEffect } from '@/hooks/use-deduped-effect'
import OnboardingProgress from '@/components/OnboardingProgress'
import { selectOnboardingState, getCompletionPct } from '@/onboarding/selectors'
import { AssetLeadsPanel } from '@/components/crm/asset-leads-panel'
import PlansTable from '@/components/PlansTable'
import TransactionsTable from '@/components/TransactionsTable'
import { ListingsPanel } from '@/components/crm/listings-panel'
import DecisiveAppraisalsTable, { DecisiveAppraisalRow } from '@/components/DecisiveAppraisalsTable'
import RamiAppraisalsTable, { RamiAppraisalRow } from '@/components/RamiAppraisalsTable'
import DocumentsTable, { DocumentRow } from '@/components/DocumentsTable'
import PermitsTable, { PermitRow } from '@/components/PermitsTable'
import type { SortingState } from '@tanstack/react-table'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'

const SUPPORTED_LLM_PROVIDERS = ['gemini', 'openai'] as const
type SupportedLLMProvider = (typeof SUPPORTED_LLM_PROVIDERS)[number]

const normalizeProvider = (value: string | null | undefined): SupportedLLMProvider | null => {
  if (!value) return null
  const normalized = value.toLowerCase()
  return (SUPPORTED_LLM_PROVIDERS as readonly string[]).includes(normalized)
    ? (normalized as SupportedLLMProvider)
    : null
}

const DEFAULT_LLM_PROVIDER: SupportedLLMProvider =
  normalizeProvider(process.env.LLM_DEFAULT_PROVIDER) ?? 'gemini'

const ALL_SECTIONS = ['summary','permits','plans','environment', 'rights','comparables','mortgage','appendix']

const formatListingTypeLabel = (value?: string | null) => {
  if (!value) return '—'
  const normalized = value.toLowerCase()
  if (normalized === 'rent') return 'השכרה'
  if (normalized === 'sale') return 'מכירה'
  return value
}

const formatAdTypeLabel = (value?: string | null) => {
  if (!value) return '—'
  const normalized = value.toLowerCase()
  if (normalized === 'private') return 'פרטי'
  if (normalized === 'broker' || normalized === 'agency' || normalized === 'agent') return 'מתווך'
  return value
}

const formatListingSourceLabel = (value?: string | null) => {
  if (!value) return '—'
  const normalized = value.toLowerCase()
  if (normalized === 'yad2') return 'יד2'
  return value
}

const sanitizePhoneNumber = (value?: string | null) => (value ? value.replace(/[^+\d]/g, '') : '')

const formatListingRooms = (rooms?: number | null, display?: string | null) => {
  if (typeof display === 'string') {
    const trimmed = display.trim()
    if (trimmed) {
      if (/^\d+(\.\d+)?$/.test(trimmed)) {
        return `${trimmed} חדרים`
      }
      return trimmed
    }
  }
  if (rooms === null || rooms === undefined || Number.isNaN(rooms)) {
    return null
  }
  const numericRooms = Number(rooms)
  if (!Number.isFinite(numericRooms)) {
    return null
  }
  const formatted = Number.isInteger(numericRooms)
    ? numericRooms.toString()
    : Number(numericRooms.toFixed(1)).toString()
  return `${formatted} חדרים`
}

const toNumericOrNull = (value: unknown): number | null => {
  if (value === null || value === undefined) return null
  if (typeof value === 'number') return Number.isFinite(value) ? value : null
  if (typeof value === 'bigint') return Number(value)
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) return null
    const normalized = trimmed.replace(/[^0-9.\-]/g, '')
    if (!normalized) return null
    const parsed = Number(normalized)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

const toStringOrNull = (value: unknown): string | null => {
  if (value === null || value === undefined) return null
  if (typeof value === 'string') {
    const trimmed = value.trim()
    return trimmed.length ? trimmed : null
  }
  if (typeof value === 'number' || typeof value === 'bigint') {
    return String(value)
  }
  return null
}

const ensureStringList = (value: unknown): string[] =>
  Array.isArray(value)
    ? value
        .map((item) => (typeof item === 'string' ? item.trim() : null))
        .filter((item): item is string => Boolean(item && item.length))
    : []

const extractFeatureLabels = (raw: unknown): string[] => {
  const collected: string[] = []
  if (Array.isArray(raw)) {
    collected.push(...ensureStringList(raw))
  } else if (raw && typeof raw === 'object') {
    const obj = raw as Record<string, unknown>
    if (Array.isArray(obj.tags)) {
      collected.push(...ensureStringList(obj.tags))
    }
    if (Array.isArray(obj.features)) {
      collected.push(...ensureStringList(obj.features))
    }
    if (Array.isArray(obj.amenities)) {
      collected.push(...ensureStringList(obj.amenities))
    }
  }
  return Array.from(new Set(collected))
}

const normalizePrimaryListing = (listing: any) => {
  if (!listing || typeof listing !== 'object') return null

  const contactInfoRaw = listing.contactInfo ?? listing.contact_info
  const baseContactInfo =
    contactInfoRaw && typeof contactInfoRaw === 'object' ? { ...contactInfoRaw } : {}

  const contactName =
    listing.contactName ??
    listing.contact_name ??
    baseContactInfo.name ??
    baseContactInfo.agent ??
    null

  const contactPhone =
    listing.contactPhone ??
    listing.contact_phone ??
    baseContactInfo.phone ??
    baseContactInfo.brokerPhone ??
    null

  if (contactName != null) baseContactInfo.name = contactName
  if (contactPhone != null) baseContactInfo.phone = contactPhone

  const hasContactInfo = Object.values(baseContactInfo).some(
    (value) => value !== null && value !== undefined && `${value}`.trim().length > 0
  )

  const roomsValue = toNumericOrNull(listing.rooms ?? listing.rooms_count ?? listing.roomsCount)
  const sizeValue = toNumericOrNull(
    listing.size ?? listing.area ?? listing.squareMeters ?? listing.square_meters
  )
  const priceValue = toNumericOrNull(
    listing.price ?? listing.listing_price ?? listing.priceValue ?? listing.price_value
  )

  const roomsDisplayValue =
    toStringOrNull(listing.roomsDisplay ?? listing.rooms_display ?? listing.roomsText ?? listing.rooms_text) ??
    formatListingRooms(roomsValue ?? undefined, undefined)

  const floorRaw =
    listing.floor ??
    listing.floorNumber ??
    listing.floor_number ??
    listing.floorDisplay ??
    listing.floor_display ??
    listing.floorLabel ??
    listing.floor_label

  const floorValue =
    typeof floorRaw === 'number'
      ? (Number.isFinite(floorRaw) ? floorRaw : null)
      : toStringOrNull(floorRaw)

  const featureLabels = extractFeatureLabels(listing.features ?? listing.tags)

  const datePosted =
    listing.datePosted ??
    listing.date_posted ??
    listing.postedAt ??
    listing.posted_at ??
    listing.scrapedAt ??
    listing.scraped_at ??
    listing.fetched_at ??
    null

  return {
    id: listing.id ?? listing.external_id ?? null,
    source: toStringOrNull(listing.source) ?? null,
    title:
      toStringOrNull(
        listing.title ?? listing.heading ?? listing.headline ?? listing.name ?? listing.caption
      ) ?? null,
    price: priceValue,
    address:
      toStringOrNull(
        listing.address ?? listing.location ?? listing.fullAddress ?? listing.full_address
      ) ?? null,
    rooms: roomsValue ?? null,
    roomsDisplay: roomsDisplayValue ?? null,
    size: sizeValue ?? null,
    propertyType: toStringOrNull(listing.propertyType ?? listing.property_type) ?? null,
    listingType: listing.listingType ?? listing.listing_type ?? null,
    adType: listing.adType ?? listing.ad_type ?? listing.seller_type ?? null,
    description:
      toStringOrNull(
        listing.description ??
          listing.details ??
          listing.about ??
          listing.text ??
          listing.body ??
          listing.summary
      ) ?? null,
    floor: floorValue,
    contactName: toStringOrNull(contactName),
    contactPhone: toStringOrNull(contactPhone),
    contactInfo: hasContactInfo ? baseContactInfo : null,
    recentDeal:
      typeof listing.recentDeal === 'boolean'
        ? listing.recentDeal
        : typeof listing.recent_deal === 'boolean'
          ? listing.recent_deal
          : null,
    photos: Array.from(
      new Set([
        ...ensureStringList(listing.photos),
        ...ensureStringList(listing.images),
      ])
    ),
    videoUrl:
      toStringOrNull(listing.videoUrl ?? listing.video_url ?? listing.video ?? listing.videoLink) ??
      null,
    url:
      toStringOrNull(listing.url ?? listing.link ?? listing.listingUrl ?? listing.listing_url) ??
      null,
    features: featureLabels.length > 0 ? featureLabels : null,
    datePosted: datePosted ?? null,
  }
}

const mapFilterValues = (values?: Array<string | { value?: string; key?: string; id?: string }>) => {
  if (!values) return []
  return values
    .map((entry) => {
      if (typeof entry === 'string') return entry
      if (!entry || typeof entry !== 'object') return ''
      if ('value' in entry && entry.value) return entry.value
      if ('key' in entry && entry.key) return entry.key
      if ('id' in entry && entry.id) return entry.id
      return ''
    })
    .filter((value): value is string => Boolean(value))
}

// Helper functions for Hebrew translations
const getContributionTypeDisplay = (type: string): string => {
  const translations: Record<string, string> = {
    'creation': 'יצירת נכס',
    'enrichment': 'העשרת נתונים',
    'verification': 'אימות נתונים',
    'update': 'עדכון שדה',
    'source_add': 'הוספת מקור',
    'comment': 'הערה/תגובה'
  }
  return translations[type] || type
}

const getSourceDisplay = (source: string): string => {
  const translations: Record<string, string> = {
    'manual': 'ידני',
    'yad2': 'יד2',
    'nadlan': 'נדלן',
    'gis_permit': 'היתר GIS',
    'gis_rights': 'זכויות GIS',
    'rami_plan': 'תוכנית רמי',
    'tabu': 'טאבו'
  }
  return translations[source] || source
}

interface AssetDetailPageClientProps {
  assetId: string
}

export default function AssetDetailPageClient({ assetId }: AssetDetailPageClientProps) {
  const { trackFeatureUsage } = useAnalytics()
  const [asset, setAsset] = useState<any>(null)
  const [comparables, setComparables] = useState<any[]>([])
  const [appraisal, setAppraisal] = useState<any | null>(null)
  const [decisiveAppraisals, setDecisiveAppraisals] = useState<any[]>([])
  const [ramiAppraisals, setRamiAppraisals] = useState<any[]>([])
  const [transactionsData, setTransactionsData] = useState<{ items: any[]; total: number; filters: { source: string[] } }>({ items: [], total: 0, filters: { source: [] } })
  const [transactionsLoading, setTransactionsLoading] = useState(false)
  const [transactionsSorting, setTransactionsSorting] = useState<SortingState>([{ id: 'date', desc: true }])
  const [transactionsPagination, setTransactionsPagination] = useState({ pageIndex: 0, pageSize: 10 })
  const [marketAnalysis, setMarketAnalysis] = useState<any>(null)
  const [permitsData, setPermitsData] = useState<{ items: PermitRow[]; total: number; filters: { stage: string[]; document_type: string[]; source: string[]; request_type: string[] } }>({ items: [], total: 0, filters: { stage: [], document_type: [], source: [], request_type: [] } })
  const [plansData, setPlansData] = useState<{ items: any[]; total: number; filters: { source: string[]; status: string[] } }>({ items: [], total: 0, filters: { source: [], status: [] } })
  const [uploading, setUploading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [generatingReport, setGeneratingReport] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [syncMessage, setSyncMessage] = useState<string>('')
  const [creatingMessage, setCreatingMessage] = useState(false)
  const [shareMessage, setShareMessage] = useState<string | null>(null)
  const [shareUrl, setShareUrl] = useState<string | null>(null)
  const [shareModal, setShareModal] = useState(false)
  const [language, setLanguage] = useState('he')
  const [sectionsModal, setSectionsModal] = useState(false)
  const [sections, setSections] = useState<string[]>(ALL_SECTIONS)
  const [activeTab, setActiveTab] = useState('analysis')
  const [rightsRows, setRightsRows] = useState<any[]>([])
  const [rightsLoading, setRightsLoading] = useState(false)
  const [rightsError, setRightsError] = useState<string | null>(null)
  const [documentsData, setDocumentsData] = useState<{ items: any[]; total: number; filters: { category: string[]; type: string[]; source: string[]; status: string[] } }>({ items: [], total: 0, filters: { category: [], type: [], source: [], status: [] } })
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [documentsError, setDocumentsError] = useState<string | null>(null)
  const [rightsSearch, setRightsSearch] = useState('')
  const [rightsDocFilter, setRightsDocFilter] = useState('all')
  const [calculatedRights, setCalculatedRights] = useState<any>(null)
  const [transactionsSearch, setTransactionsSearch] = useState('')
  const [plansSearch, setPlansSearch] = useState('')
  const [plansSourceFilter, setPlansSourceFilter] = useState('all')
  const [plansStatusFilter, setPlansStatusFilter] = useState('all')
  const [plansPlanNumberFilter, setPlansPlanNumberFilter] = useState('')
  const [plansDescriptionFilter, setPlansDescriptionFilter] = useState('')
  const [plansSorting, setPlansSorting] = useState<SortingState>([{ id: 'effective_date', desc: true }])
  const [plansPagination, setPlansPagination] = useState({ pageIndex: 0, pageSize: 10 })
  const [plansLoading, setPlansLoading] = useState(false)
  const [transactionsSourceFilter, setTransactionsSourceFilter] = useState('all')
  const [transactionsPriceMin, setTransactionsPriceMin] = useState<number | undefined>(undefined)
  const [transactionsPriceMax, setTransactionsPriceMax] = useState<number | undefined>(undefined)
  const [transactionsPricePerSqmMin, setTransactionsPricePerSqmMin] = useState<number | undefined>(undefined)
  const [transactionsPricePerSqmMax, setTransactionsPricePerSqmMax] = useState<number | undefined>(undefined)
  const [transactionsAreaMin, setTransactionsAreaMin] = useState<number | undefined>(undefined)
  const [transactionsAreaMax, setTransactionsAreaMax] = useState<number | undefined>(undefined)
  const [transactionsAddressFilter, setTransactionsAddressFilter] = useState('')
  const [permitsSearch, setPermitsSearch] = useState('')
  const [permitsStageFilter, setPermitsStageFilter] = useState('all')
  const [permitsTypeFilter, setPermitsTypeFilter] = useState('all')
  const [permitsSourceFilter, setPermitsSourceFilter] = useState('all')
  const [permitsRequestTypeFilter, setPermitsRequestTypeFilter] = useState('all')
  const [permitsPermitNumberFilter, setPermitsPermitNumberFilter] = useState('')
  const [permitsRequestNumberFilter, setPermitsRequestNumberFilter] = useState('')
  const [permitsDescriptionFilter, setPermitsDescriptionFilter] = useState('')
  const [permitsApprovalDateFrom, setPermitsApprovalDateFrom] = useState<string | undefined>(undefined)
  const [permitsApprovalDateTo, setPermitsApprovalDateTo] = useState<string | undefined>(undefined)
  const [permitsExpiryDateFrom, setPermitsExpiryDateFrom] = useState<string | undefined>(undefined)
  const [permitsExpiryDateTo, setPermitsExpiryDateTo] = useState<string | undefined>(undefined)
  const [permitsSorting, setPermitsSorting] = useState<SortingState>([{ id: 'approvalDate', desc: true }])
  const [permitsPagination, setPermitsPagination] = useState({ pageIndex: 0, pageSize: 10 })
  const [permitsLoading, setPermitsLoading] = useState(false)
  const [decisiveSourceFilter, setDecisiveSourceFilter] = useState('all')
  const [ramiSourceFilter, setRamiSourceFilter] = useState('all')
  const [ramiStatusFilter, setRamiStatusFilter] = useState('all')
  const [documentsTableSearch, setDocumentsTableSearch] = useState('')
  const [documentsCategoryFilter, setDocumentsCategoryFilter] = useState('all')
  const [documentsTypeFilter, setDocumentsTypeFilter] = useState('all')
  const [documentsSourceFilter, setDocumentsSourceFilter] = useState('all')
  const [documentsStatusFilter, setDocumentsStatusFilter] = useState('all')
  const [documentsSorting, setDocumentsSorting] = useState<SortingState>([{ id: 'documentDate', desc: true }])
  const [documentsPagination, setDocumentsPagination] = useState({ pageIndex: 0, pageSize: 10 })
  const [decisiveSearch, setDecisiveSearch] = useState('')
  const [ramiSearch, setRamiSearch] = useState('')

  const primaryListing = React.useMemo(
    () => normalizePrimaryListing(asset?.primaryListing ?? asset?.primary_listing),
    [asset]
  )

  const listingImages = React.useMemo(() => {
    const collected: string[] = []
    const seen = new Set<string>()
    const appendUnique = (values?: string[] | null) => {
      if (!Array.isArray(values)) return
      for (const value of values) {
        if (typeof value !== 'string') continue
        const trimmed = value.trim()
        if (!trimmed || seen.has(trimmed)) continue
        seen.add(trimmed)
        collected.push(trimmed)
      }
    }

    appendUnique(asset?.images)
    appendUnique(asset?.photos)
    appendUnique(primaryListing?.photos)

    return collected
  }, [asset, primaryListing])

  const parkingRequirements = calculatedRights?.building_privileges?.parking_requirements ?? []
  const primaryParkingRequirement = parkingRequirements.length > 0 ? parkingRequirements[0] : null
  const { parkingValueDisplay, parkingUnitLabel } = useMemo(() => {
    let value = '—'
    let unit = 'מ״ר'

    if (!primaryParkingRequirement) {
      return { parkingValueDisplay: value, parkingUnitLabel: unit }
    }

    const status = primaryParkingRequirement.status
    if (typeof status === 'string' && status.trim()) {
      const normalized = status.trim()
      const statusLabel =
        normalized === 'permitted'
          ? 'מותרת'
          : normalized === 'forbidden'
          ? 'אסורה'
          : normalized
      return {
        parkingValueDisplay: statusLabel,
        parkingUnitLabel: 'סטטוס',
      }
    }

    if (typeof primaryParkingRequirement.value === 'number') {
      value = primaryParkingRequirement.value.toLocaleString()
      unit =
        primaryParkingRequirement.unit === 'spaces'
          ? 'מקומות'
          : primaryParkingRequirement.unit || 'מ״ר'
      return { parkingValueDisplay: value, parkingUnitLabel: unit }
    }

    if (typeof primaryParkingRequirement.area_sqm === 'number') {
      value = primaryParkingRequirement.area_sqm.toLocaleString()
      return { parkingValueDisplay: value, parkingUnitLabel: unit }
    }

    const stringValue =
      typeof primaryParkingRequirement.value === 'string'
        ? primaryParkingRequirement.value.trim()
        : ''

    if (stringValue) {
      return { parkingValueDisplay: stringValue, parkingUnitLabel: '' }
    }

    const rawText =
      typeof primaryParkingRequirement.raw_text === 'string'
        ? primaryParkingRequirement.raw_text.trim()
        : ''

    if (rawText) {
      return { parkingValueDisplay: rawText, parkingUnitLabel: '' }
    }

    return { parkingValueDisplay: value, parkingUnitLabel: unit }
  }, [primaryParkingRequirement])

React.useEffect(() => {
  setPermitsPagination((prev) => (prev.pageIndex === 0 ? prev : { ...prev, pageIndex: 0 }))
}, [
  permitsSearch,
  permitsStageFilter,
  permitsTypeFilter,
  permitsSourceFilter,
  permitsRequestTypeFilter,
  permitsPermitNumberFilter,
  permitsRequestNumberFilter,
  permitsDescriptionFilter,
  permitsApprovalDateFrom,
  permitsApprovalDateTo,
  permitsExpiryDateFrom,
  permitsExpiryDateTo,
])

React.useEffect(() => {
  if (
    permitsRequestTypeFilter !== 'all' &&
    permitsData.filters.request_type.length > 0 &&
    !permitsData.filters.request_type.includes(permitsRequestTypeFilter)
  ) {
    setPermitsRequestTypeFilter('all')
  }
}, [permitsData.filters.request_type, permitsRequestTypeFilter])

React.useEffect(() => {
  setPermitsPagination((prev) => (prev.pageIndex === 0 ? prev : { ...prev, pageIndex: 0 }))
}, [permitsSorting])

React.useEffect(() => {
  setTransactionsPagination((prev) => (prev.pageIndex === 0 ? prev : { ...prev, pageIndex: 0 }))
}, [
  transactionsSearch,
  transactionsSourceFilter,
  transactionsPriceMin,
  transactionsPriceMax,
  transactionsPricePerSqmMin,
  transactionsPricePerSqmMax,
  transactionsAreaMin,
  transactionsAreaMax,
  transactionsAddressFilter,
])

React.useEffect(() => {
  setTransactionsPagination((prev) => (prev.pageIndex === 0 ? prev : { ...prev, pageIndex: 0 }))
}, [transactionsSorting])

React.useEffect(() => {
  setPlansPagination((prev) => (prev.pageIndex === 0 ? prev : { ...prev, pageIndex: 0 }))
}, [plansSearch, plansSourceFilter, plansStatusFilter, plansPlanNumberFilter, plansDescriptionFilter])

React.useEffect(() => {
  setPlansPagination((prev) => (prev.pageIndex === 0 ? prev : { ...prev, pageIndex: 0 }))
}, [plansSorting])

React.useEffect(() => {
  setDocumentsPagination((prev) => (prev.pageIndex === 0 ? prev : { ...prev, pageIndex: 0 }))
}, [documentsTableSearch, documentsCategoryFilter, documentsTypeFilter, documentsSourceFilter, documentsStatusFilter])

React.useEffect(() => {
  setDocumentsPagination((prev) => (prev.pageIndex === 0 ? prev : { ...prev, pageIndex: 0 }))
}, [documentsSorting])
  const router = useRouter()
  const searchParams = useSearchParams()
  const provider = useMemo<SupportedLLMProvider>(() => {
    const providerKeys = ['provider', 'llm_provider', 'llm-provider']
    for (const key of providerKeys) {
      const normalized = normalizeProvider(searchParams.get(key))
      if (normalized) {
        return normalized
      }
    }
    return DEFAULT_LLM_PROVIDER
  }, [searchParams])
  const id = assetId
  const { user, isAuthenticated } = useAuth()
  const canViewCrm = ['broker', 'appraiser', 'admin'].includes(user?.role || '')
  const onboardingState = React.useMemo(() => selectOnboardingState(user), [user])
  const resolveMetaEntry = React.useCallback(
    (key: string) => {
      const meta = asset?._meta
      if (!meta || typeof meta !== 'object') {
        return undefined
      }
      const candidates = new Set<string>([key])
      if (key.includes('primaryListing')) {
        candidates.add(key.replace('primaryListing', 'primary_listing'))
      }
      if (key.includes('.')) {
        candidates.add(key.replace(/\./g, '_'))
      }
      for (const candidate of candidates) {
        const entry = (meta as Record<string, any>)[candidate]
        if (entry) {
          return entry
        }
      }
      return undefined
    },
    [asset]
  )
  const renderValue = (value: React.ReactNode, key: string) => {
    const metaEntry = resolveMetaEntry(key)
    return (
      <span className="flex items-center gap-1">
        {value ?? '—'}
        <DataBadge source={metaEntry?.source} fetchedAt={metaEntry?.fetched_at} url={metaEntry?.url} />
      </span>
    )
  }

  const toSafeString = (value: unknown): string => {
    if (value === null || value === undefined) return ''
    if (typeof value === 'string') return value
    if (typeof value === 'number' || typeof value === 'bigint') return String(value)
    return ''
  }

  const firstNonEmpty = (...values: unknown[]): string => {
    for (const value of values) {
      const str = toSafeString(value).trim()
      if (str) return str
    }
    return ''
  }

  const parseDateValue = (value: unknown): Date | null => {
    if (value === null || value === undefined || value === '') return null
    if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
    if (typeof value === 'number' || typeof value === 'bigint') {
      const numeric = Number(value)
      if (Number.isNaN(numeric)) return null
      return new Date(numeric > 1e12 ? numeric : numeric * 1000)
    }
    if (typeof value === 'string') {
      const trimmed = value.trim()
      if (!trimmed) return null
      const match = trimmed.match(/Date\((\d+)\)/)
      if (match) {
        const millis = Number(match[1])
        return Number.isNaN(millis) ? null : new Date(millis)
      }
      if (/^\d+$/.test(trimmed)) {
        const numeric = Number(trimmed)
        if (!Number.isNaN(numeric)) {
          return new Date(numeric > 1e12 ? numeric : numeric * 1000)
        }
      }
      const parsed = new Date(trimmed)
      return Number.isNaN(parsed.getTime()) ? null : parsed
    }
    return null
  }

  const formatDateValue = (value: unknown): string | null => {
    const parsed = parseDateValue(value)
    return parsed ? parsed.toLocaleDateString('he-IL') : null
  }

  const normalizedPermits = permitsData.items

  const normalizedDecisiveAppraisals = useMemo<DecisiveAppraisalRow[]>(() => {
    return decisiveAppraisals.map((app: any, index: number) => {
      const id = toSafeString(app?.id) || `decisive-${index}`
      const appraiser = toSafeString(app?.appraiser || app?.title)
      const date = toSafeString(app?.date || app?.document_date)
      const fetchedAt = toSafeString(app?.fetched_at)
      const source = toSafeString(app?.source)
      const url = toSafeString(app?.url)
      let value: number | string | undefined = app?.appraisedValue ?? app?.value ?? app?.marketValue
      if (typeof value === 'string') {
        const numeric = Number(value.replace(/[^0-9.-]+/g, ''))
        value = Number.isNaN(numeric) ? value : numeric
      }

      const searchValues = [
        appraiser,
        date,
        fetchedAt,
        source,
        toSafeString(app?.external_id),
        typeof value === 'number' ? value.toString() : toSafeString(value),
      ].filter(Boolean) as string[]

      return {
        id,
        appraiser,
        date,
        value,
        source,
        fetchedAt,
        url,
        searchValues,
      }
    })
  }, [decisiveAppraisals])

  const normalizedRamiAppraisals = useMemo<RamiAppraisalRow[]>(() => {
    return ramiAppraisals.map((app: any, index: number) => {
      const id = toSafeString(app?.id) || `rami-${index}`
      const planNumber = toSafeString(app?.plan_number || app?.planNumber)
      const date = toSafeString(app?.date || app?.document_date)
      const fetchedAt = toSafeString(app?.fetched_at)
      const source = toSafeString(app?.source)
      const status = toSafeString(app?.status)
      const url = toSafeString(app?.url)
      let value: number | string | undefined = app?.marketValue ?? app?.appraisedValue ?? app?.value
      if (typeof value === 'string') {
        const numeric = Number(value.replace(/[^0-9.-]+/g, ''))
        value = Number.isNaN(numeric) ? value : numeric
      }

      const searchValues = [
        planNumber,
        date,
        status,
        fetchedAt,
        source,
        typeof value === 'number' ? value.toString() : toSafeString(value),
      ].filter(Boolean) as string[]

      return {
        id,
        planNumber,
        date,
        value,
        status,
        source,
        fetchedAt,
        url,
        searchValues,
      }
    })
  }, [ramiAppraisals])

  const documentsTableData = useMemo<DocumentRow[]>(() => {
    return (documentsData.items || []).map((doc: any, index: number) => {
      const category = toSafeString(
        doc?.category ??
          doc?.category_display ??
          doc?.categoryName ??
          doc?.category_label
      )
      const type = toSafeString(
        doc?.document_type ??
          doc?.documentType ??
          doc?.type
      )
      const status = toSafeString(doc?.status)
      const source = toSafeString(doc?.source)
      const documentDate = toSafeString(doc?.document_date ?? doc?.documentDate)
      const uploadedAt = toSafeString(doc?.uploaded_at ?? doc?.uploadedAt)
      const uploadedBy = toSafeString(doc?.uploaded_by ?? doc?.uploadedBy)
      const fileUrl = toSafeString(doc?.file_url ?? doc?.fileUrl)
      const externalUrl = toSafeString(doc?.external_url ?? doc?.externalUrl)
      const externalId = toSafeString(doc?.external_id ?? doc?.externalId)
      const description = toSafeString(doc?.description)

      const id =
        toSafeString(doc?.id) ||
        `${category || type || 'document'}-${index}`
      const title = toSafeString(
        doc?.title ??
          doc?.filename ??
          doc?.name ??
          'מסמך ללא שם'
      )
      const isDownloadable =
        typeof doc?.is_downloadable === 'boolean'
          ? doc.is_downloadable && Boolean(fileUrl)
          : Boolean(fileUrl)

      const searchValues = [
        title,
        description,
        category,
        type,
        status,
        source,
        documentDate,
        uploadedAt,
        uploadedBy,
        externalId,
      ].filter(Boolean) as string[]

      return {
        id,
        title,
        description,
        category,
        type,
        status,
        source,
        documentDate,
        uploadedAt,
        uploadedBy,
        fileUrl,
        externalUrl,
        isDownloadable,
        externalId,
        searchValues,
      }
    })
  }, [documentsData.items])

  const availableDocumentFilters = useMemo(() => ({
    category: mapFilterValues(documentsData.filters?.category),
    type: mapFilterValues(documentsData.filters?.type),
    source: mapFilterValues(documentsData.filters?.source),
    status: mapFilterValues(documentsData.filters?.status),
  }), [documentsData.filters])

  const formatNumber = (value?: number, options?: Intl.NumberFormatOptions) =>
    value !== undefined && value !== null
      ? value.toLocaleString('he-IL', options)
      : null

  const formatCurrency = (value?: number) =>
    value !== undefined && value !== null
      ? `₪${value.toLocaleString('he-IL')}`
      : null

  const handleDocumentClick = (e: React.MouseEvent<HTMLAnchorElement>, docUrl: string) => {
    if (!docUrl) {
      e.preventDefault()
      alert('קישור לא זמין')
    } else if (!docUrl.startsWith('http')) {
      // For relative URLs, construct the full URL
      e.preventDefault()
      const fullUrl = docUrl.startsWith('/') 
        ? `${window.location.origin}${docUrl}`
        : `${window.location.origin}/${docUrl}`
      window.open(fullUrl, '_blank')
    }
  }

  const formatPercent = (value?: number, digits = 0) =>
    value !== undefined && value !== null
      ? `${value.toFixed(digits)}%`
      : null

  const transactionSourceOptions = useMemo(() => {
    const mapLabel = (value: string) => {
      switch (value) {
        case 'collected_government':
        case 'government':
          return 'ממשלתי'
        case 'internal':
          return 'מאגר פנימי'
        default:
          return value || 'לא ידוע'
      }
    }
    const available = transactionsData.filters.source || []
    return [
      { value: 'all', label: 'הכל' },
      ...available
        .filter((value): value is string => typeof value === 'string' && value.length > 0)
        .map((value) => ({ value, label: mapLabel(value) })),
    ]
  }, [transactionsData.filters.source])

  const permitRadius = asset?._meta?.radius ?? 50
  
  const remainingRightsDisplayValue = useMemo(() => {
    const fromCalculated =
      calculatedRights?.summary?.remaining_rights_sqm ??
      calculatedRights?.remaining_rights?.remaining_area_sqm
    if (fromCalculated !== undefined && fromCalculated !== null) {
      return fromCalculated
    }
    if (asset?.remainingRightsSqm !== undefined && asset?.remainingRightsSqm !== null) {
      return asset.remainingRightsSqm
    }
    // Legacy snake_case support if returned directly from backend
    const legacy = (asset as any)?.remaining_rights_sqm
    if (legacy !== undefined && legacy !== null) {
      return legacy
    }
    return null
  }, [asset, calculatedRights])

  const summaryMetrics = useMemo(() => {
    const remaining = remainingRightsDisplayValue

    let additional: number | null =
      calculatedRights?.summary?.additional_rights_percentage ??
      null
    if (
      additional == null &&
      asset?.remainingRightsSqm !== undefined &&
      asset?.remainingRightsSqm !== null &&
      asset?.area
    ) {
      additional = Math.round((asset.remainingRightsSqm / asset.area) * 100)
    }

    let estimated: number | null =
      calculatedRights?.summary?.estimated_rights_value_k ??
      null
    if (
      estimated == null &&
      asset?.pricePerSqm &&
      remaining !== null &&
      remaining > 0
    ) {
      estimated = Math.round((asset.pricePerSqm * remaining * 0.7) / 1000)
    }

    return {
      remaining,
      additional,
      estimated,
    }
  }, [asset, calculatedRights, remainingRightsDisplayValue])

  const loadRightsData = React.useCallback(async () => {
    if (!id) return
    setRightsLoading(true)
    setRightsError(null)
    try {
      const response = await apiClient.get(`/api/assets/${id}/rights`)
      if (!response.ok) {
        throw new Error(response.error || 'Failed to load rights')
      }
      const data = response.data
      // Store calculated rights for the new UI
      const calculated = data.calculated_rights || null
      setCalculatedRights(calculated)
      
      const remainingRightsFromCalc =
        calculated?.summary?.remaining_rights_sqm ??
        calculated?.remaining_rights?.remaining_area_sqm
      if (remainingRightsFromCalc !== undefined && remainingRightsFromCalc !== null) {
        setAsset((prev: any) => (prev ? { ...prev, remainingRightsSqm: remainingRightsFromCalc } : prev))
      }
      const parcelAreaFromCalc = calculated?.summary?.parcel_area_sqm
      if (parcelAreaFromCalc !== undefined && parcelAreaFromCalc !== null) {
        setAsset((prev: any) => (prev ? { ...prev, parcelArea: parcelAreaFromCalc } : prev))
      }
      
      // Combine tabu_data, gis_rights, and detailed_rights into a single array for display
      const allRightsRows = [
        ...(data.tabu_data || []),
        ...(data.gis_rights || []),
        ...(data.detailed_rights?.[0]?.rights_details || []),
        ...(data.detailed_rights?.[0]?.building_lines || []),
        ...(data.detailed_rights?.[0]?.floor_details || []),
        ...(data.detailed_rights?.[0]?.notes || [])
      ]
      setRightsRows(allRightsRows)
    } catch (rightsErr) {
      console.error('Error loading rights data:', rightsErr)
      setRightsRows([])
      setCalculatedRights(null)
      setRightsError('שגיאה בטעינת נתוני טאבו')
    } finally {
      setRightsLoading(false)
    }
  }, [id])

  // Load documents organized by category
  const loadDocumentsTable = React.useCallback(async () => {
    if (!id) return

    setDocumentsLoading(true)
    setDocumentsError(null)

    try {
      const params = new URLSearchParams()
      params.set('limit', String(documentsPagination.pageSize))
      params.set('offset', String(documentsPagination.pageIndex * documentsPagination.pageSize))
      params.set('asset_id', String(id))

      if (documentsTableSearch.trim()) {
        params.set('search', documentsTableSearch.trim())
      }
      if (documentsCategoryFilter !== 'all') {
        params.set('category', documentsCategoryFilter)
      }
      if (documentsTypeFilter !== 'all') {
        params.set('type', documentsTypeFilter)
      }
      if (documentsSourceFilter !== 'all') {
        params.set('source', documentsSourceFilter)
      }
      if (documentsStatusFilter !== 'all') {
        params.set('status', documentsStatusFilter)
      }

      const sortMapping: Record<string, string> = {
        title: 'title',
        category: 'category',
        type: 'document_type',
        status: 'status',
        source: 'source',
        documentDate: 'document_date',
        uploadedAt: 'uploaded_at',
        uploadedBy: 'uploaded_by',
      }

      const primarySort = documentsSorting[0]
      const orderingField = primarySort ? sortMapping[primarySort.id] || 'document_date' : 'document_date'
      const orderingValue = primarySort ? `${primarySort.desc ? '-' : ''}${orderingField}` : '-document_date'
      params.set('ordering', orderingValue)

      const response = await fetch(`/api/documents/table?${params.toString()}`)
      if (!response.ok) {
        throw new Error('Failed to load documents')
      }
      const data = await response.json()
      setDocumentsData({
        items: data.results || [],
        total: data.count || 0,
        filters: {
          category: data.filters?.category || [],
          type: data.filters?.type || [],
          source: data.filters?.source || [],
          status: data.filters?.status || [],
        },
      })
    } catch (error) {
      console.error('Error loading documents:', error)
      setDocumentsError('שגיאה בטעינת מסמכים')
      setDocumentsData({ items: [], total: 0, filters: { category: [], type: [], source: [], status: [] } })
    } finally {
      setDocumentsLoading(false)
    }
  }, [
    id,
    documentsPagination,
    documentsSorting,
    documentsTableSearch,
    documentsCategoryFilter,
    documentsTypeFilter,
    documentsSourceFilter,
    documentsStatusFilter,
  ])

useDedupedEffect(() => {
  if (activeTab !== 'documents') return
  loadDocumentsTable()
}, [activeTab, loadDocumentsTable])

  useDedupedEffect(() => {
    setLoading(true)
    apiClient.get(`/api/assets/${id}`)
      .then(response => {
        if (!response.ok) throw new Error(response.error || 'Failed to load asset')
        const assetData = response.data?.asset || response.data
        setAsset(assetData)
      })
      .catch(err => {
        console.error('Error loading asset:', err)
        setError('שגיאה בטעינת הנכס')
      })
      .finally(() => setLoading(false))
  }, [id])

useDedupedEffect(() => {
  if (activeTab !== 'appraisals') return
  fetch(`/api/assets/${id}/appraisal`)
    .then(res => {
      if (!res.ok) throw new Error('Failed to load appraisal')
      return res.json()
    })
    .then(data => {
      setComparables(data.comps || [])
      setAppraisal(data.appraisal || null)
      setDecisiveAppraisals(data.decisive_appraisals || [])
      setRamiAppraisals(data.rami_appraisals || [])
    })
    .catch(err => console.error('Error loading appraisal:', err))
}, [activeTab, id])

const loadPermits = React.useCallback(async () => {
  if (!id) return
  setPermitsLoading(true)
  try {
    const params = new URLSearchParams()
    params.set('limit', String(permitsPagination.pageSize))
    params.set('offset', String(permitsPagination.pageIndex * permitsPagination.pageSize))

    if (permitsSearch.trim()) {
      params.set('search', permitsSearch.trim())
    }
    if (permitsStageFilter !== 'all') {
      params.set('stage', permitsStageFilter)
    }
    if (permitsTypeFilter !== 'all') {
      params.set('document_type', permitsTypeFilter)
    }
    if (permitsSourceFilter !== 'all') {
      params.set('source', permitsSourceFilter)
    }
    if (permitsRequestTypeFilter !== 'all') {
      params.set('request_type', permitsRequestTypeFilter)
    }
    if (permitsPermitNumberFilter.trim()) {
      params.set('permit_number', permitsPermitNumberFilter.trim())
    }
    if (permitsRequestNumberFilter.trim()) {
      params.set('request_number', permitsRequestNumberFilter.trim())
    }
    if (permitsDescriptionFilter.trim()) {
      params.set('description', permitsDescriptionFilter.trim())
    }
    if (permitsApprovalDateFrom) {
      params.set('approval_date_from', permitsApprovalDateFrom)
    }
    if (permitsApprovalDateTo) {
      params.set('approval_date_to', permitsApprovalDateTo)
    }
    if (permitsExpiryDateFrom) {
      params.set('expiry_date_from', permitsExpiryDateFrom)
    }
    if (permitsExpiryDateTo) {
      params.set('expiry_date_to', permitsExpiryDateTo)
    }

    const sortMapping: Record<string, string> = {
      approvalDate: 'approval_date',
      issueDate: 'issue_date',
      expiryDate: 'expiry_date',
      permitNumber: 'permit_number',
      requestNumber: 'request_number',
      stage: 'stage',
      documentType: 'document_type',
      source: 'source',
      title: 'title',
    }

    const primarySort = permitsSorting[0]
    const orderingField = primarySort ? sortMapping[primarySort.id] || 'approval_date' : 'approval_date'
    const orderingValue = primarySort ? `${primarySort.desc ? '-' : ''}${orderingField}` : '-approval_date'
    params.set('ordering', orderingValue)

    const response = await fetch(`/api/assets/${id}/permits?${params.toString()}`)
    if (!response.ok) {
      throw new Error('Failed to load permits')
    }
    const data = await response.json()
    setPermitsData({
      items: data.permits || [],
      total: data.count || 0,
      filters: {
        stage: data.filters?.stage || [],
        document_type: data.filters?.document_type || [],
        source: data.filters?.source || [],
        request_type: data.filters?.request_type || [],
      },
    })
  } catch (err) {
    console.error('Error loading permits:', err)
    setPermitsData({ items: [], total: 0, filters: { stage: [], document_type: [], source: [], request_type: [] } })
  } finally {
    setPermitsLoading(false)
  }
}, [
  id,
  permitsPagination,
  permitsSorting,
  permitsSearch,
  permitsStageFilter,
  permitsTypeFilter,
  permitsSourceFilter,
  permitsRequestTypeFilter,
  permitsPermitNumberFilter,
  permitsRequestNumberFilter,
  permitsDescriptionFilter,
  permitsApprovalDateFrom,
  permitsApprovalDateTo,
  permitsExpiryDateFrom,
  permitsExpiryDateTo,
])

useDedupedEffect(() => {
  if (activeTab !== 'permits') return
  loadPermits()
}, [activeTab, loadPermits])

const loadTransactions = React.useCallback(async () => {
  if (!id) return
  setTransactionsLoading(true)
  try {
    const params = new URLSearchParams()
    params.set('limit', String(transactionsPagination.pageSize))
    params.set('offset', String(transactionsPagination.pageIndex * transactionsPagination.pageSize))

    if (transactionsSearch.trim()) {
      params.set('search', transactionsSearch.trim())
    }
    if (transactionsSourceFilter !== 'all') {
      params.set('source', transactionsSourceFilter)
    }
    if (transactionsPriceMin !== undefined) {
      params.set('price_min', String(transactionsPriceMin))
    }
    if (transactionsPriceMax !== undefined) {
      params.set('price_max', String(transactionsPriceMax))
    }
    if (transactionsPricePerSqmMin !== undefined) {
      params.set('price_per_sqm_min', String(transactionsPricePerSqmMin))
    }
    if (transactionsPricePerSqmMax !== undefined) {
      params.set('price_per_sqm_max', String(transactionsPricePerSqmMax))
    }
    if (transactionsAreaMin !== undefined) {
      params.set('area_min', String(transactionsAreaMin))
    }
    if (transactionsAreaMax !== undefined) {
      params.set('area_max', String(transactionsAreaMax))
    }
    if (transactionsAddressFilter.trim()) {
      params.set('address', transactionsAddressFilter.trim())
    }

    const sortMapping: Record<string, string> = {
      date: 'date',
      price: 'price',
      price_per_sqm: 'price_per_sqm',
      area: 'area',
      rooms: 'rooms',
      address: 'address',
      source: 'source',
    }

    const primarySort = transactionsSorting[0]
    const orderingField = primarySort ? sortMapping[primarySort.id as keyof typeof sortMapping] || 'date' : 'date'
    const orderingValue = primarySort ? `${primarySort.desc ? '-' : ''}${orderingField}` : '-date'
    params.set('ordering', orderingValue)

    const response = await fetch(`/api/assets/${id}/transactions?${params.toString()}`)
    if (!response.ok) {
      throw new Error('Failed to load transactions')
    }
    const data = await response.json()
    setTransactionsData({
      items: data.transactions || [],
      total: data.count || 0,
      filters: {
        source: data.filters?.source || [],
      },
    })
    setMarketAnalysis(data.market_analysis || null)
  } catch (err) {
    console.error('Error loading transactions:', err)
    setTransactionsData({ items: [], total: 0, filters: { source: [] } })
    setMarketAnalysis(null)
  } finally {
    setTransactionsLoading(false)
  }
}, [
  id,
  transactionsPagination,
  transactionsSorting,
  transactionsSearch,
  transactionsSourceFilter,
  transactionsPriceMin,
  transactionsPriceMax,
  transactionsPricePerSqmMin,
  transactionsPricePerSqmMax,
  transactionsAreaMin,
  transactionsAreaMax,
  transactionsAddressFilter,
])

useDedupedEffect(() => {
  if (activeTab !== 'transactions') return
  loadTransactions()
}, [activeTab, loadTransactions])

const loadPlans = React.useCallback(async () => {
  if (!id) return
  setPlansLoading(true)
  try {
    const params = new URLSearchParams()
    params.set('limit', String(plansPagination.pageSize))
    params.set('offset', String(plansPagination.pageIndex * plansPagination.pageSize))

    if (plansSearch.trim()) {
      params.set('search', plansSearch.trim())
    }
    if (plansSourceFilter !== 'all') {
      params.set('source', plansSourceFilter)
    }
    if (plansStatusFilter !== 'all') {
      params.set('status', plansStatusFilter)
    }
    if (plansPlanNumberFilter.trim()) {
      params.set('plan_number', plansPlanNumberFilter.trim())
    }
    if (plansDescriptionFilter.trim()) {
      params.set('description', plansDescriptionFilter.trim())
    }

    const sortMapping: Record<string, string> = {
      plan_number: 'plan_number',
      title: 'title',
      description: 'description',
      status: 'status',
      source: 'source',
      effective_date: 'effective_date',
    }

    const primarySort = plansSorting[0]
    const orderingField = primarySort ? sortMapping[primarySort.id] || 'effective_date' : 'effective_date'
    const orderingValue = primarySort ? `${primarySort.desc ? '-' : ''}${orderingField}` : '-effective_date'
    params.set('ordering', orderingValue)

    const response = await fetch(`/api/assets/${id}/plans?${params.toString()}`)
    if (!response.ok) {
      throw new Error('Failed to load plans')
    }
    const data = await response.json()
    setPlansData({
      items: data.plans || [],
      total: data.count || 0,
      filters: {
        source: data.filters?.source || [],
        status: data.filters?.status || [],
      },
    })
  } catch (err) {
    console.error('Error loading plans:', err)
    setPlansData({ items: [], total: 0, filters: { source: [], status: [] } })
  } finally {
    setPlansLoading(false)
  }
}, [id, plansPagination, plansSorting, plansSearch, plansSourceFilter, plansStatusFilter, plansPlanNumberFilter, plansDescriptionFilter])

useDedupedEffect(() => {
  if (activeTab !== 'plans') return
  loadPlans()
}, [activeTab, loadPlans])

useDedupedEffect(() => {
  if (!id) return
  loadRightsData()
}, [id, loadRightsData])

useDedupedEffect(() => {
  if (activeTab !== 'rights') return
  loadRightsData()
}, [activeTab, loadRightsData])

  useDedupedEffect(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem('reportSections') : null
    if (stored) {
      try { setSections(JSON.parse(stored)) } catch {}
    } else {
      fetch('/api/settings')
        .then(res => res.json())
        .then(data => setSections(data.report_sections || ALL_SECTIONS))
        .catch(() => setSections(ALL_SECTIONS))
    }
  }, [])

  // Initialize active tab from URL
  useEffect(() => {
    const tabFromUrl = searchParams.get('tab')
    if (tabFromUrl && ['analysis', 'permits', 'plans', 'rights', 'transactions', 'appraisals', 'environment', 'documents', 'contributions'].includes(tabFromUrl)) {
      setActiveTab(tabFromUrl)
    }
  }, [searchParams])

  useEffect(() => {
    if (!canViewCrm && activeTab === 'crm') {
      setActiveTab('analysis')
    }
  }, [canViewCrm, activeTab])

  // Update URL when active tab changes
  const handleTabChange = (value: string) => {
    setActiveTab(value)
    const url = new URL(window.location.href)
    url.searchParams.set('tab', value)
    router.replace(url.pathname + url.search, { scroll: false })
  }

  const handleSyncData = async () => {
    if (!id || !asset?.address) return
    setSyncing(true)
    setSyncMessage('מסנכרן נתונים...')
    
    try {
      const response = await apiClient.request(`/api/assets/${id}/sync`, {
        method: 'POST',
        body: JSON.stringify({ address: asset.address })
      })
      
      if (response.ok) {
        setSyncMessage(response.data?.message || 'סנכרון נתונים התחיל בהצלחה')
        
        // Refresh the asset data after a short delay to show updated status
        setTimeout(async () => {
          const assetResponse = await apiClient.get(`/api/assets/${id}`)
          if (assetResponse.ok) {
            setAsset(assetResponse.data?.asset || assetResponse.data)
          }
        }, 2000)
        
        // Clear message after 10 seconds
        setTimeout(() => setSyncMessage(''), 10000)
      } else {
        setSyncMessage(response.error || 'שגיאה בסנכרון הנתונים')
        setTimeout(() => setSyncMessage(''), 5000)
      }
    } catch (err) {
      console.error('Sync failed:', err)
      setSyncMessage('שגיאה בסנכרון הנתונים')
      setTimeout(() => setSyncMessage(''), 5000)
    } finally {
      setSyncing(false)
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="p-6">
          <Breadcrumb className="mb-4">
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink href="/" className="flex items-center gap-1">
                  <Home className="h-4 w-4" />
                  בית
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink href="/assets" className="flex items-center gap-1">
                  <Building className="h-4 w-4" />
                  נכסים
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>טוען...</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <div className="flex items-center gap-2 mb-4">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/assets">
                <ArrowLeft className="h-4 w-4 rtl:rotate-180" />
                חזרה לרשימה
              </Link>
            </Button>
          </div>
          <PageLoader message="טוען נתוני נכס..." showLogo={false} />
        </div>
    </DashboardLayout>
  )
}

  if (error || !asset) {
    return (
      <DashboardLayout>
        <div className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/assets">
                <ArrowLeft className="h-4 w-4 rtl:rotate-180" />
                חזרה לרשימה
              </Link>
            </Button>
          </div>
          <p>{error || 'לא הצלחנו לטעון את פרטי הנכס המבוקש.'}</p>
        </div>
      </DashboardLayout>
    )
  }

  const listingTypeValueRaw = firstNonEmpty(primaryListing?.listingType, asset.listingType, asset?.listing_type)
  const listingTypeValue = listingTypeValueRaw || null
  const adTypeValueRaw = firstNonEmpty(asset.adType, asset?.ad_type, primaryListing?.adType)
  const adTypeValue = adTypeValueRaw || null
  const listingPropertyTypeValueRaw = firstNonEmpty(
    primaryListing?.propertyType,
    asset.type,
    asset?.property_type
  )
  const listingPropertyTypeValue = listingPropertyTypeValueRaw || null
  const contactNameValueRaw = firstNonEmpty(
    asset.contactName,
    asset?.contact_name,
    primaryListing?.contactName,
    asset.contactInfo?.name,
    asset?.contact_info?.name,
    primaryListing?.contactInfo?.name
  )
  const contactNameValue = contactNameValueRaw || null
  const primaryPhoneValueRaw = firstNonEmpty(
    asset.contactPhone,
    asset?.contact_phone,
    primaryListing?.contactPhone,
    asset.contactInfo?.phone,
    asset.contactInfo?.brokerPhone,
    asset?.contact_info?.phone,
    asset?.contact_info?.brokerPhone,
    primaryListing?.contactInfo?.phone,
    primaryListing?.contactInfo?.brokerPhone
  )
  const primaryPhoneValue = primaryPhoneValueRaw || null
  const brokerPhoneCandidate = firstNonEmpty(
    asset.contactInfo?.brokerPhone,
    asset?.contact_info?.brokerPhone,
    primaryListing?.contactInfo?.brokerPhone
  )
  const secondaryPhoneValue =
    brokerPhoneCandidate && brokerPhoneCandidate !== primaryPhoneValueRaw ? brokerPhoneCandidate : null
  const listingUrlValueRaw = firstNonEmpty(primaryListing?.url, asset?.listingUrl, asset?.listing_url)
  const listingUrlValue = listingUrlValueRaw || null
  const listingSourceValueRaw = firstNonEmpty(
    primaryListing?.source,
    asset.primarySource,
    asset?.primary_source
  )
  const listingSourceValue = listingSourceValueRaw || null
  const listingTitleValueRaw = firstNonEmpty(primaryListing?.title)
  const listingTitleValue = listingTitleValueRaw || null
  const listingPriceValue = toNumericOrNull(
    primaryListing?.price ??
      asset.price ??
      asset?.price_value ??
      asset?.priceValue ??
      asset?.modelPrice ??
      asset?.model_price ??
      null
  )
  const listingPriceDisplay = listingPriceValue !== null ? formatCurrency(listingPriceValue) : null
  const listingRoomsValue =
    toNumericOrNull(
      primaryListing?.rooms ??
        asset.rooms ??
        asset?.rooms_count ??
        asset?.roomsCount ??
        asset.bedrooms ??
        asset?.bedrooms_count ??
        asset?.bedroomsCount ??
        null
    ) ?? null
  const listingRoomsDisplay = formatListingRooms(listingRoomsValue ?? null, primaryListing?.roomsDisplay ?? null)
  const listingSizeValue =
    toNumericOrNull(
      primaryListing?.size ??
        asset.area ??
        asset?.netSqm ??
        asset?.net_sqm ??
        asset.totalArea ??
        asset?.total_area ??
        null
    ) ?? null
  const listingSizeFormatted = listingSizeValue !== null && listingSizeValue !== undefined ? formatNumber(listingSizeValue) : null
  const listingSizeDisplay = listingSizeFormatted ? `${listingSizeFormatted} מ״ר` : null
  const listingDatePostedDisplay = formatDateValue(
    primaryListing?.datePosted ??
      asset?.datePosted ??
      asset?.date_posted ??
      asset?.postedAt ??
      asset?.posted_at ??
      null
  )
  const listingFloorDisplay = (() => {
    const floor = primaryListing?.floor ?? asset.floor ?? asset?.floor_number ?? asset?.floorNumber
    if (floor === null || floor === undefined) return null
    if (typeof floor === 'number') {
      if (Number.isNaN(floor)) return null
      return `קומה ${floor}`
    }
    const asString = String(floor).trim()
    if (!asString) return null
    if (/^\d+$/.test(asString)) {
      return `קומה ${asString}`
    }
    return asString
  })()
  const listingDescriptionValue =
    typeof primaryListing?.description === 'string'
      ? primaryListing.description.trim()
      : ''
  const primaryListingFeatures = primaryListing?.features
  const listingFeatures =
    Array.isArray(primaryListingFeatures)
      ? primaryListingFeatures
          .filter((feature): feature is string => typeof feature === 'string' && feature.trim().length > 0)
          .map((feature) => feature.trim())
      : []
  const sanitizedPrimaryPhone = sanitizePhoneNumber(primaryPhoneValue)
  const sanitizedSecondaryPhone = sanitizePhoneNumber(secondaryPhoneValue)
  const hasListingDetails = Boolean(
    listingTypeValue ||
      adTypeValue ||
      contactNameValue ||
      primaryPhoneValue ||
      secondaryPhoneValue ||
      listingUrlValue ||
      listingSourceValue ||
      listingTitleValue ||
      listingPriceDisplay ||
      listingPropertyTypeValue ||
      listingRoomsDisplay ||
      listingSizeDisplay ||
      listingFloorDisplay ||
      listingDatePostedDisplay ||
      (listingDescriptionValue && listingDescriptionValue.length > 0) ||
      listingFeatures.length > 0
  )

  const handleGenerateReport = async (selected: string[]) => {
    if (!id) return

    setGeneratingReport(true)

    try {
      const res = await fetch('/api/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assetId: Number(id), sections: selected })
      })

      if (!res.ok) {
        console.error('Report generation failed:', await res.text())
        return
      }
      localStorage.removeItem('onboardingDismissed')
      window.dispatchEvent(new Event('onboardingUpdate'))
      router.push('/reports')
    } catch (err) {
      console.error('Report generation failed:', err)
    } finally {
      // ensure loading state always clears even on failure
      setGeneratingReport(false)
    }
  }

  const handleCreateMessage = async () => {
    if (!id) return
    setCreatingMessage(true)
    setShareMessage(null)
    setShareUrl(null)
    try {
      const res = await fetch(`/api/assets/${id}/share-message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language, provider })
      })
      if (res.ok) {
        const data = await res.json()
        setShareMessage(data.text)
        setShareUrl(data.share_url)

        // Track marketing message creation
        trackFeatureUsage('marketing_message', parseInt(id), {
          message_type: 'share_message',
          language: language,
          provider
        })
      } else {
        const errorData = await res.json().catch(() => ({}))
        alert(errorData.details || errorData.error || 'שגיאה ביצירת הודעה')
      }
    } catch (err) {
      console.error('Message generation failed:', err)
      alert('שגיאה ביצירת הודעה')
    } finally {
      setCreatingMessage(false)
    }
  }

  const toggleSection = (key: string, checked: boolean) => {
    setSections(prev => checked ? [...prev, key] : prev.filter(s => s !== key))
  }

  const handleConfirmSections = async () => {
    if (sections.length === 0) return
    if (typeof window !== 'undefined') {
      localStorage.setItem('reportSections', JSON.stringify(sections))
    }
    try {
      fetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_sections: sections })
      }).catch(() => {})
    } catch {}
    await handleGenerateReport(sections)
    setSectionsModal(false)
  }

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!id) return
    const formData = new FormData(e.currentTarget)
    const file = formData.get('file') as File | null
    const providedType = (formData.get('document_type') as string) || (formData.get('type') as string)
    if (providedType) {
      formData.set('document_type', providedType)
    }
    if (formData.has('type')) {
      formData.delete('type')
    }
    if (!formData.get('title')) {
      formData.set('title', file?.name || 'מסמך')
    }
    setUploading(true)
    try {
      const res = await fetch(`/api/assets/${id}/documents`, {
        method: 'POST',
        body: formData,
      })
      if (res.ok) {
        const responseData = await res.json()
        const uploadedDoc = responseData.doc || responseData
        if (!uploadedDoc) {
          return
        }
        const normalizedDoc = {
          ...uploadedDoc,
          type: uploadedDoc.type || uploadedDoc.document_type || uploadedDoc.documentType || providedType || 'other'
        }
        setAsset((prev: any) => ({
          ...prev,
          documents: [...(prev.documents || []), normalizedDoc],
        }))
        if (normalizedDoc.type === 'tabu') {
          await loadRightsData()
        }
        await loadDocumentsTable()
        // Safe form reset - check if form element still exists
        if (e.currentTarget) {
          e.currentTarget.reset()
        }
      }
    } catch (err) {
      console.error('Upload failed:', err)
    } finally {
      setUploading(false)
    }
  }

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <Breadcrumb className="mb-4">
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="/" className="flex items-center gap-1">
                <Home className="h-4 w-4" />
                בית
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbLink href="/assets" className="flex items-center gap-1">
                <Building className="h-4 w-4" />
                נכסים
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>{asset.address}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        {isAuthenticated && getCompletionPct(onboardingState) < 100 && <OnboardingProgress state={onboardingState} />}
        {/* Header */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/assets">
                <ArrowLeft className="h-4 w-4 rtl:rotate-180" />
                חזרה לרשימה
              </Link>
            </Button>
            <div className="flex-1">
              <h1 className="text-3xl font-bold">{asset.address}</h1>
              <p className="text-muted-foreground">
                {asset.city}
                {asset.neighborhood ? ` · ${asset.neighborhood}` : ''} · {asset.type ?? '—'} ·{' '}
                {formatNumber(asset.area) ? `${formatNumber(asset.area)} מ״ר נטו` : '—'}
              </p>
            </div>
          </div>
          <div className="w-full text-start space-y-2 md:w-auto">
            <div className="text-3xl font-bold">{formatCurrency(asset.price) ?? '—'}</div>
            <div className="text-muted-foreground">
              {asset.pricePerSqm !== undefined && asset.pricePerSqm !== null
                ? `${formatCurrency(asset.pricePerSqm)}/מ״ר`
                : '—'}
            </div>
            {/* Attribution Information */}
            {asset.attribution && (
              <div className="text-xs text-muted-foreground mt-2 space-y-1 text-start">
                {asset.attribution.created_by && (
                  <div className="text-start">
                    <span className="font-medium">נוצר על ידי: </span>
                    <span>{asset.attribution.created_by.name}</span>
                  </div>
                )}
                {asset.attribution.last_updated_by && asset.attribution.last_updated_by.id !== asset.attribution.created_by?.id && (
                  <div className="text-start">
                    <span className="font-medium">עודכן לאחרונה על ידי: </span>
                    <span>{asset.attribution.last_updated_by.name}</span>
                  </div>
                )}
                {asset.recent_contributions && asset.recent_contributions.length > 0 && (
                  <div className="text-start">
                    <span className="font-medium">תרומות אחרונות: </span>
                    <span>{asset.recent_contributions.length}</span>
                  </div>
                )}
              </div>
            )}
            <div className="flex flex-wrap gap-2 items-center justify-end md:justify-start">
              <Button
                size="sm"
                variant="outline"
                onClick={handleSyncData}
                disabled={syncing}
              >
                {syncing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    מסנכרן נתונים...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4" />
                    סנכרן נתונים
                  </>
                )}
              </Button>
              <Button
                size="sm"
                onClick={() => setSectionsModal(true)}
                disabled={generatingReport}
              >
                {generatingReport ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    יוצר דוח...
                  </>
                ) : (
                  <>
                    <FileText className="h-4 w-4" />
                    צור דוח
                  </>
                )}
              </Button>
              <Dialog open={sectionsModal} onOpenChange={setSectionsModal}>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>בחירת חלקים לדוח</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-2">
                    {[
                      ['summary','סיכום'],
                      ['permits','היתרים'],
                      ['plans','תוכניות'],
                      ['environment','סביבה'],
                      ['comparables','השוואות'],
                      ['mortgage','תרחישי משכנתא'],
                      ['appendix','נספח'],
                    ].map(([key,label]) => (
                      <div key={key} className="flex items-center justify-between">
                        <Label htmlFor={key}>{label}</Label>
                        <Switch id={key} checked={sections.includes(key)} onCheckedChange={(c) => toggleSection(key, c)} />
                      </div>
                    ))}
                  </div>
                  <DialogFooter className="mt-4">
                    <Button variant="outline" onClick={() => setSectionsModal(false)}>בטל</Button>
                    <Button onClick={handleConfirmSections} disabled={generatingReport}>
                      {generatingReport ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          יוצר דוח...
                        </>
                      ) : (
                        'צור דוח'
                      )}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShareModal(true)}
              >
                {'צור הודעת פרסום'}
              </Button>
              <Dialog
                open={shareModal}
                onOpenChange={(open) => {
                  setShareModal(open)
                  if (!open) {
                    setShareMessage(null)
                    setShareUrl(null)
                  }
                }}
              >
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>הודעת פרסום</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label>שפה</Label>
                      <Select value={language} onValueChange={setLanguage}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="בחר שפה" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="he">עברית</SelectItem>
                          <SelectItem value="en">English</SelectItem>
                          <SelectItem value="ru">Русский</SelectItem>
                          <SelectItem value="fr">Français</SelectItem>
                          <SelectItem value="es">Español</SelectItem>
                          <SelectItem value="ar">العربية</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    {creatingMessage ? (
                      <div className="flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        יוצר הודעה...
                      </div>
                    ) : shareMessage ? (
                      <div className="space-y-2">
                        <textarea
                          className="w-full border rounded p-2 text-sm"
                          rows={4}
                          readOnly
                          value={shareMessage}
                        />
                        <DialogFooter className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => {
                              navigator.clipboard.writeText(shareMessage)
                              alert('Copied!')
                            }}
                          >
                            העתק הודעה
                          </Button>
                          {shareUrl && (
                            <Button
                              size="sm"
                              onClick={() => {
                                const fullUrl = `${window.location.origin}${shareUrl}`
                                navigator.clipboard.writeText(fullUrl)
                                alert('Copied!')
                              }}
                            >
                              העתק קישור
                            </Button>
                          )}
                          <Button size="sm" variant="outline" onClick={handleCreateMessage}>
                            צור מחדש
                          </Button>
                        </DialogFooter>
                      </div>
                    ) : (
                      <DialogFooter className="mt-4">
                        <Button onClick={handleCreateMessage}>צור הודעה</Button>
                      </DialogFooter>
                    )}
                  </div>
                </DialogContent>
              </Dialog>
            </div>
            {syncMessage && (
              <div className="text-sm text-muted-foreground">{syncMessage}</div>
            )}
          </div>
        </div>

        {/* Images Gallery */}
        {listingImages.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>תמונות הנכס</CardTitle>
            </CardHeader>
            <CardContent>
              <ImageGallery 
                images={listingImages} 
                size="lg" 
                maxDisplay={4}
                showThumbnails={true}
              />
            </CardContent>
          </Card>
        )}

        {/* Quick Stats */}
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
          <Card>
            <CardContent className="p-4">
                <div className="text-sm text-muted-foreground">רמת ביטחון</div>
              <div className="text-2xl font-bold">{formatPercent(asset.confidencePct) ?? '—'}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
                <div className="text-sm text-muted-foreground">תשואה</div>
              <div className="text-2xl font-bold">{formatPercent(asset.capRatePct, 1) ?? '—'}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-sm text-muted-foreground">יתרת זכויות</div>
              <div className="text-2xl font-bold">
                {!!remainingRightsDisplayValue
                  ? `+${formatNumber(remainingRightsDisplayValue)} מ״ר`
                  : '—'}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-sm text-muted-foreground">רמת רעש</div>
              <div className="text-2xl font-bold">
                {!!asset.noiseLevel
                  ? `${asset.noiseLevel}/5`
                  : '—'}
              </div>
            </CardContent>
          </Card>
        </div>

        {hasListingDetails && (
          <Card>
            <CardHeader className="space-y-1">
              <CardTitle>פרטי מודעה</CardTitle>
              {listingSourceValue && (
                <CardDescription>מקור: {formatListingSourceLabel(listingSourceValue)}</CardDescription>
              )}
              {listingTitleValue && (
                <div className="text-sm font-medium text-foreground">{listingTitleValue}</div>
              )}
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
                <div>
                  <div className="text-sm text-muted-foreground">מחיר מבוקש</div>
                  <div className="font-medium">
                    {renderValue(listingPriceDisplay || undefined, 'primaryListing.price')}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">סוג נכס</div>
                  <div className="font-medium">
                    {renderValue(listingPropertyTypeValue || undefined, 'primaryListing.propertyType')}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">סוג עסקה</div>
                  <div className="font-medium">
                    {renderValue(
                      listingTypeValue ? <Badge>{formatListingTypeLabel(listingTypeValue)}</Badge> : undefined,
                      'listingType'
                    )}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">סוג מפרסם</div>
                  <div className="font-medium">
                    {renderValue(
                      adTypeValue ? <Badge>{formatAdTypeLabel(adTypeValue)}</Badge> : undefined,
                      'adType'
                    )}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">חדרים</div>
                  <div className="font-medium">
                    {renderValue(listingRoomsDisplay || undefined, 'primaryListing.rooms')}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">גודל</div>
                  <div className="font-medium">
                    {renderValue(listingSizeDisplay || undefined, 'primaryListing.size')}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">קומה</div>
                  <div className="font-medium">
                    {renderValue(listingFloorDisplay || undefined, 'primaryListing.floor')}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">פורסם ב</div>
                  <div className="font-medium">
                    {renderValue(listingDatePostedDisplay || undefined, 'primaryListing.datePosted')}
                  </div>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
                <div>
                  <div className="text-sm text-muted-foreground">איש קשר</div>
                  <div className="font-medium">
                    {renderValue(contactNameValue || undefined, 'contactName')}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">טלפון</div>
                  <div className="font-medium">
                    {renderValue(
                      primaryPhoneValue ? (
                        <a
                          href={sanitizedPrimaryPhone ? `tel:${sanitizedPrimaryPhone}` : undefined}
                          className="inline-flex items-center gap-1 text-primary hover:underline"
                        >
                          <Phone className="h-3 w-3" />
                          <span dir="ltr">{primaryPhoneValue}</span>
                        </a>
                      ) : undefined,
                      'contactPhone'
                    )}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">טלפון נוסף</div>
                  <div className="font-medium">
                    {renderValue(
                      secondaryPhoneValue ? (
                        <a
                          href={sanitizedSecondaryPhone ? `tel:${sanitizedSecondaryPhone}` : undefined}
                          className="inline-flex items-center gap-1 text-primary hover:underline"
                        >
                          <Phone className="h-3 w-3" />
                          <span dir="ltr">{secondaryPhoneValue}</span>
                        </a>
                      ) : undefined,
                      'contactInfo.brokerPhone'
                    )}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">קישור למודעה</div>
                  <div className="font-medium">
                    {renderValue(
                      listingUrlValue ? (
                        <Link
                          href={listingUrlValue}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          צפייה במודעה
                        </Link>
                      ) : undefined,
                      'primaryListing.url'
                    )}
                  </div>
                </div>
              </div>

              {listingDescriptionValue && (
                <div>
                  <div className="text-sm text-muted-foreground mb-1">תיאור</div>
                  <p className="whitespace-pre-line leading-relaxed">{listingDescriptionValue}</p>
                </div>
              )}

              {listingFeatures.length > 0 && (
                <div>
                  <div className="text-sm text-muted-foreground mb-1">מאפיינים</div>
                  <div className="flex flex-wrap gap-2">
                    {listingFeatures.map((feature) => (
                      <Badge key={feature} variant="outline" className="bg-muted/40">
                        {feature}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Address Details */}
        <Card>
          <CardHeader>
            <CardTitle>פרטי כתובת</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
            <div>
              <div className="text-sm text-muted-foreground">עיר</div>
              <div className="font-medium">{renderValue(asset.city, 'city')}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">רחוב</div>
              <div className="font-medium">{renderValue(asset.street, 'street')}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">מס&apos;</div>
              <div className="font-medium">{renderValue(asset.number, 'number')}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">גוש</div>
              <div className="font-medium">{renderValue(asset.block, 'block')}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">חלקה</div>
              <div className="font-medium">{renderValue(asset.parcel, 'parcel')}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">תת חלקה</div>
              <div className="font-medium">{renderValue(asset.subparcel, 'subparcel')}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">מספר דירה</div>
              <div className="font-medium">{renderValue(asset.apartment, 'apartment')}</div>
            </div>
          </CardContent>
        </Card>

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-4">
          <TabsList className="flex flex-wrap gap-2 md:flex-nowrap md:gap-0">
            <TabsTrigger value="analysis">ניתוח כללי</TabsTrigger>
            <TabsTrigger value="listings">מודעות</TabsTrigger>
            <TabsTrigger value="transactions">עיסקאות השוואה</TabsTrigger>
            <TabsTrigger value="permits">היתרים</TabsTrigger>
            <TabsTrigger value="plans">תוכניות</TabsTrigger>
            <TabsTrigger value="rights">זכויות</TabsTrigger>
            <TabsTrigger value="environment">סביבה</TabsTrigger>
            {canViewCrm && <TabsTrigger value="crm">לקוחות</TabsTrigger>}
            <TabsTrigger value="appraisals">שומות באיזור</TabsTrigger>
            <TabsTrigger value="documents">מסמכים</TabsTrigger>
            {/* <TabsTrigger value="contributions">תרומות קהילה</TabsTrigger> */}
          </TabsList>

          <TabsContent value="analysis" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>פרטי הנכס</CardHeader>
                <CardBody className="space-y-2">
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">סוג:</span>
                    <span>{asset.type ?? '—'}</span>
                  </div>
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">מ״ר נטו:</span>
                    <span>{formatNumber(asset.area) ?? '—'}</span>
                  </div>
                  {asset.total_area && (
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">שטח חלקה כולל:</span>
                      <span>{formatNumber(asset.total_area)} מ״ר</span>
                    </div>
                  )}
                  {asset.subparcelArea && (
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">שטח מגרש:</span>
                      <span>{formatNumber(asset.subparcelArea)} מ״ר</span>
                    </div>
                  )}
                  {asset.builtArea && (
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">שטח בנוי:</span>
                      <span>{formatNumber(asset.builtArea)} מ״ר</span>
                    </div>
                  )}
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">חדרים:</span>
                    <span>{asset.rooms ?? '—'}</span>
                  </div>
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">ייעוד:</span>
                    <span>{asset.zoning ?? '—'}</span>
                  </div>
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">שכונה:</span>
                    <span>{asset.neighborhood ?? '—'}</span>
                  </div>
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">רמת ביטחון:</span>
                    <Badge variant={asset.confidencePct >= 80 ? 'success' : 'warning'}>
                      {asset.confidencePct}%
                    </Badge>
                  </div>
                </CardBody>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>אנליזה פיננסית</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">מחיר מודל:</span>
                    <span>{formatCurrency(asset.modelPrice) ?? '—'}</span>
                  </div>
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">פער למחיר:</span>
                    <Badge variant={asset.priceGapPct !== undefined && asset.priceGapPct !== null && asset.priceGapPct > 0 ? 'warning' : 'success'}>
                      {formatPercent(asset.priceGapPct, 1) ?? '—'}
                    </Badge>
                  </div>
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">הערכת שכירות:</span>
                    <span>{formatCurrency(asset.rentEstimate) ?? '—'}</span>
                  </div>
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">תשואה שנתית:</span>
                    <Badge variant={asset.capRatePct !== undefined && asset.capRatePct !== null && asset.capRatePct >= 3 ? 'success' : 'warning'}>
                      {formatPercent(asset.capRatePct, 1) ?? '—'}
                    </Badge>
                  </div>
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">תחרות 1 ק״מ:</span>
                    <span>{asset.competition1km ?? '—'}</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>ניתוח תכנוני ומשפטי</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between rtl:flex-row-reverse">
                  <span className="text-muted-foreground">רמת ניצול זכויות:</span>
                  <span>{asset.rightsUsagePct ? `${asset.rightsUsagePct}%` : '—'}</span>
                </div>
                <div className="flex justify-between rtl:flex-row-reverse">
                  <span className="text-muted-foreground">מגבלות משפטיות:</span>
                  <span>{asset.legalRestrictions ?? '—'}</span>
                </div>
                <div className="flex justify-between rtl:flex-row-reverse">
                  <span className="text-muted-foreground">פוטנציאל התחדשות:</span>
                  <span>{asset.urbanRenewalPotential ?? '—'}</span>
                </div>
                <div className="flex justify-between rtl:flex-row-reverse">
                  <span className="text-muted-foreground">היטל השבחה צפוי:</span>
                  <span>{asset.bettermentLevy ?? '—'}</span>
                </div>
                
                {/* Enhanced Planning Metrics */}
                <div className="flex justify-between rtl:flex-row-reverse">
                  <span className="text-muted-foreground">אחוז כיסוי בנייה:</span>
                  <span>{asset.buildingCoveragePct ? `${asset.buildingCoveragePct}%` : '—'}</span>
                </div>
                
                {/* Height Analysis */}
                {asset.heightAnalysis && (
                  <div className="space-y-1">
                    <div className="text-sm font-medium text-muted-foreground">ניתוח גובה:</div>
                    <div className="flex justify-between rtl:flex-row-reverse text-sm">
                      <span className="text-muted-foreground">קומות נוכחיות:</span>
                      <span>{asset.heightAnalysis.current_floors ?? '—'}</span>
                    </div>
                    <div className="flex justify-between rtl:flex-row-reverse text-sm">
                      <span className="text-muted-foreground">קומות מותרות:</span>
                      <span>{asset.heightAnalysis.allowed_floors ?? '—'}</span>
                    </div>
                    {asset.heightAnalysis.height_compliance && (
                      <div className="flex justify-between rtl:flex-row-reverse text-sm">
                        <span className="text-muted-foreground">עמידה בתקן:</span>
                        <span className={asset.heightAnalysis.height_compliance === 'compliant' ? 'text-green-600' : 'text-red-600'}>
                          {asset.heightAnalysis.height_compliance === 'compliant' ? 'עומד' : 'לא עומד'}
                        </span>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Setback Analysis */}
                {asset.setbackAnalysis && asset.setbackAnalysis.violations && asset.setbackAnalysis.violations.length > 0 && (
                  <div className="space-y-1">
                    <div className="text-sm font-medium text-muted-foreground">הפרות נסיגה:</div>
                    <div className="text-sm text-red-600">
                      {asset.setbackAnalysis.violations.join('; ')}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <Tooltip.Provider delayDuration={0}>
                  <Tooltip.Root>
                    <Tooltip.Trigger asChild>
                      <CardTitle>מדד אטרקטיביות</CardTitle>
                    </Tooltip.Trigger>
                    <Tooltip.Portal>
                      <Tooltip.Content
                        sideOffset={4}
                        dir="rtl"
                        className="rounded bg-gray-900 text-white px-2 py-1 text-xs max-w-xs text-center"
                      >
                        המדד מחושב כממוצע של רמת אמון הנתונים, תשואת ההון ופער המחיר מהשוק
                      </Tooltip.Content>
                    </Tooltip.Portal>
                  </Tooltip.Root>
                </Tooltip.Provider>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between rtl:flex-row-reverse">
                    <span>ציון כללי:</span>
                    <div className="flex items-center gap-2">
                      <div className="text-2xl font-bold">
                        {!!asset.confidencePct &&
                        !!asset.capRatePct &&
                        !!asset.priceGapPct
                          ? Math.round(
                              (asset.confidencePct + asset.capRatePct * 20 +
                                (asset.priceGapPct < 0
                                  ? 100 + asset.priceGapPct
                                  : 100 - asset.priceGapPct)) /
                                3
                            )
                          : '—'}
                      </div>
                      <div className="text-sm text-muted-foreground">/100</div>
                    </div>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {asset.priceGapPct < -10 ? "נכס במחיר אטרקטיביי מתחת לשוק" : 
                     asset.priceGapPct > 10 ? "נכס יקר יחסית לשוק" : 
                     "נכס במחיר הוגן יחסית לשוק"}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="plans" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>תוכניות מקומיות ומפורטות</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">תכנית נוכחית:</span>
                      {renderValue(asset.program ?? 'לא זמין', 'program')}
                    </div>
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">ייעוד:</span>
                      {renderValue(<Badge variant="neutral">{asset.zoning ?? 'לא צוין'}</Badge>, 'zoning')}
                    </div>
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">סטטוס תוכנית:</span>
                      {renderValue(asset.planStatus ?? 'לא ידוע', 'planStatus')}
                    </div>
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">מגבלות תכנוניות:</span>
                      {renderValue(asset.publicObligations ?? 'אין', 'publicObligations')}
                    </div>
                  </div>
                  <div className="pt-2 border-t">
                    <div className="text-sm text-muted-foreground">
                      נתונים מבוססים על תוכניות עדכניות ממערכת ה-GIS של עיריית תל אביב
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>תוכניות כלל עירוניות</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">סטטוס תכנוני:</span>
                      {renderValue(
                        <Badge variant={asset.planActive ? "success" : "neutral"}>
                          {asset.planActive ? "פעיל" : "לא פעיל"}
                        </Badge>, 
                        'planActive'
                      )}
                    </div>
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">הגבלות מיוחדות:</span>
                      {renderValue(asset.riskFlags?.length > 0 ? asset.riskFlags.join(', ') : 'אין', 'riskFlags')}
                    </div>
                  </div>
                  <div className="pt-2 border-t">
                    <div className="text-sm text-muted-foreground">
                      מידע נוסף על תוכניות עתידיות יתעדכן בהתאם לפרסומים חדשים
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>


            {/* Plans Table */}
            <PlansTable
              data={plansData.items}
              loading={plansLoading}
              searchValue={plansSearch}
              onSearchChange={setPlansSearch}
              filters={{
                source: {
                  value: plansSourceFilter,
                  onChange: setPlansSourceFilter,
                  options: [],
                },
                status: {
                  value: plansStatusFilter,
                  onChange: setPlansStatusFilter,
                  options: [],
                },
              }}
              manualPagination
              manualSorting
              pageCount={Math.max(1, Math.ceil((plansData.total || 0) / plansPagination.pageSize))}
              paginationState={plansPagination}
              onPaginationChange={setPlansPagination}
              sortingState={plansSorting}
              onSortingChange={setPlansSorting}
              totalCount={plansData.total}
              filterOptions={{
                source: plansData.filters.source,
                status: plansData.filters.status,
              }}
              advancedFilters={{
                planNumber: {
                  value: plansPlanNumberFilter,
                  onChange: setPlansPlanNumberFilter,
                },
                description: {
                  value: plansDescriptionFilter,
                  onChange: setPlansDescriptionFilter,
                },
              }}
              onRefresh={loadPlans}
            />
          </TabsContent>

          <TabsContent value="rights" className="space-y-4">
            {/* Summary Metrics */}
            <Card>
              <CardHeader>
                <CardTitle>סיכום זכויות בנייה</CardTitle>
                <CardDescription>מבט כללי על זכויות הבנייה של הנכס</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {summaryMetrics.remaining !== null
                        ? formatNumber(summaryMetrics.remaining) ?? '—'
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">מ״ר זכויות נותרות</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {summaryMetrics.additional !== null
                        ? formatPercent(
                            summaryMetrics.additional,
                            Number.isInteger(summaryMetrics.additional) ? 0 : 1
                          ) ?? '—'
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">אחוז זכויות נוספות</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {summaryMetrics.estimated !== null
                        ? `₪${summaryMetrics.estimated.toLocaleString('he-IL')}K`
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">ערך משוער זכויות</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Calculated Building Rights */}
            {calculatedRights && (
              <Card>
                <CardHeader>
                  <CardTitle>זכויות בנייה מחושבות</CardTitle>
                  <CardDescription>חישוב זכויות בנייה על בסיס דף הזכויות של עיריית תל אביב ונתונים נוכחיים</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <Card>
                      <CardContent className="p-4">
                        <div className="text-sm font-medium text-muted-foreground">שטח חלקה</div>
                        <div className="text-2xl font-bold">{calculatedRights.summary.parcel_area_sqm?.toFixed(1) || '—'} מ״ר</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <div className="text-sm font-medium text-muted-foreground">זכות בנייה כוללת</div>
                        <div className="text-2xl font-bold">{calculatedRights.summary.total_building_privilege_sqm?.toLocaleString() || '—'} מ״ר</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <div className="text-sm font-medium text-muted-foreground">שימוש נוכחי</div>
                        <div className="text-2xl font-bold">{calculatedRights.summary.current_usage_sqm?.toLocaleString() || '—'} מ״ר</div>
                        <div className="text-sm text-muted-foreground">{calculatedRights.summary.utilization_percentage?.toFixed(1) || '0'}% ניצול</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <div className="text-sm font-medium text-muted-foreground">זכויות נותרות</div>
                        <div className="text-2xl font-bold text-green-600">{calculatedRights.summary.remaining_rights_sqm?.toLocaleString() || '—'} מ״ר</div>
                        <div className="text-sm text-muted-foreground">{calculatedRights.remaining_rights?.remaining_percentage?.toFixed(1) || '0'}% זמין</div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Status */}
                  <div className="flex items-center gap-2">
                    <Badge variant={calculatedRights.remaining_rights?.can_expand ? "default" : "destructive"}>
                      {calculatedRights.summary.status === 'Can expand' ? 'ניתן להרחבה' : 'מנוצל במלואו'}
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                      מקור: {calculatedRights.summary.privilege_source}
                    </span>
                  </div>

                  {/* Floor Privileges */}
                  {calculatedRights.building_privileges?.floor_privileges && Object.keys(calculatedRights.building_privileges.floor_privileges).length > 0 && (
                    <div>
                      <h4 className="text-lg font-semibold mb-3">זכויות קומות</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(calculatedRights.building_privileges.floor_privileges).map(([floorType, details]: [string, any]) => (
                          <Card key={floorType}>
                            <CardContent className="p-4">
                              <div className="text-sm font-medium text-muted-foreground">קומה {floorType}</div>
                              <div className="text-xl font-bold">{details.percentage}%</div>
                              <div className="text-sm text-muted-foreground">{details.area_sqm?.toLocaleString()} מ״ר</div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Building Requirements */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Building Lines */}
                    {calculatedRights.building_privileges?.building_line_requirements && calculatedRights.building_privileges.building_line_requirements.length > 0 && (
                      <div>
                        <h4 className="text-lg font-semibold mb-3">קווי בניין</h4>
                        <div className="space-y-2">
                          {calculatedRights.building_privileges.building_line_requirements.map((line: any, index: number) => (
                            <div key={index} className="flex justify-between items-center p-3 border rounded-lg">
                              <span className="font-medium">קו {line.type}</span>
                              <span className="text-sm text-muted-foreground">{line.distance_meters} מטרים</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Additional Requirements */}
                    <div>
                      <h4 className="text-lg font-semibold mb-3">דרישות נוספות</h4>
                      <div className="space-y-2">
                        <div className="text-sm text-muted-foreground text-center py-4">
                          דרישות נוספות יוצגו כאן כאשר יהיו זמינות
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Service and Auxiliary Areas */}
                  <div>
                    <h4 className="text-lg font-semibold mb-3">שטחי שירות ועזר</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {/* Auxiliary Building */}
                      {calculatedRights.building_privileges?.auxiliary_building_area_sqm > 0 && (
                        <div className="p-3 border rounded-lg">
                          <div className="text-sm font-medium text-muted-foreground">בניין עזר</div>
                          <div className="text-xl font-bold">{calculatedRights.building_privileges.auxiliary_building_area_sqm}</div>
                          <div className="text-sm text-muted-foreground">מ״ר</div>
                        </div>
                      )}

                      {/* Parking */}
                      {parkingRequirements.length > 0 && (
                        <div className="p-3 border rounded-lg">
                          <div className="text-sm font-medium text-muted-foreground">חניה</div>
                          <div className="text-xl font-bold">{parkingValueDisplay}</div>
                          {parkingUnitLabel && (
                            <div className="text-sm text-muted-foreground">{parkingUnitLabel}</div>
                          )}
                        </div>
                      )}

                      {/* Roof Areas */}
                      {calculatedRights.building_privileges?.roof_percentages && calculatedRights.building_privileges.roof_percentages.length > 0 && (
                        <div className="p-3 border rounded-lg">
                          <div className="text-sm font-medium text-muted-foreground">שטחי גג</div>
                          <div className="text-xl font-bold">
                            {calculatedRights.building_privileges.roof_percentages.reduce((sum: number, roof: any) => sum + (roof.area_sqm || 0), 0)}
                          </div>
                          <div className="text-sm text-muted-foreground">מ״ר</div>
                        </div>
                      )}

                      {/* Basement Areas */}
                      {calculatedRights.building_privileges?.basement_area_sqm > 0 && (
                        <div className="p-3 border rounded-lg">
                          <div className="text-sm font-medium text-muted-foreground">שטחי מרתף</div>
                          <div className="text-xl font-bold">{calculatedRights.building_privileges.basement_area_sqm}</div>
                          <div className="text-sm text-muted-foreground">מ״ר</div>
                        </div>
                      )}

                      {/* Service Areas */}
                      {calculatedRights.building_privileges?.service_area_sqm > 0 && (
                        <div className="p-3 border rounded-lg">
                          <div className="text-sm font-medium text-muted-foreground">שטחי שירות</div>
                          <div className="text-xl font-bold">{calculatedRights.building_privileges.service_area_sqm}</div>
                          <div className="text-sm text-muted-foreground">מ״ר</div>
                        </div>
                      )}

                      {/* Storage Areas */}
                      {calculatedRights.building_privileges?.storage_area_sqm > 0 && (
                        <div className="p-3 border rounded-lg">
                          <div className="text-sm font-medium text-muted-foreground">מחסנים</div>
                          <div className="text-xl font-bold">{calculatedRights.building_privileges.storage_area_sqm}</div>
                          <div className="text-sm text-muted-foreground">מ״ר</div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Current Building Details */}
                  {calculatedRights.current_usage?.building_details && calculatedRights.current_usage.building_details.length > 0 && (
                    <div>
                      <h4 className="text-lg font-semibold mb-3">בניינים קיימים</h4>
                      <div className="space-y-2">
                        {calculatedRights.current_usage.building_details.map((building: any, index: number) => (
                          <div key={index} className="p-3 border rounded-lg">
                            <div className="flex justify-between items-start">
                              <div>
                                <div className="font-medium">
                                  {building.permit_number ? `היתר ${building.permit_number}` : `בניין ${building.building_number}`}
                                </div>
                                {building.housing_units > 0 && (
                                  <div className="text-sm text-muted-foreground">{building.housing_units} יחידות דיור</div>
                                )}
                              </div>
                              <div className="text-start text-sm">
                                {building.total_area_sqm > 0 && (
                                  <div className="font-medium">{building.total_area_sqm.toLocaleString()} מ״ר</div>
                                )}
                                {building.residential_area_sqm > 0 && (
                                  <div className="text-muted-foreground">מגורים: {building.residential_area_sqm.toLocaleString()} מ״ר</div>
                                )}
                                {building.commercial_area_sqm > 0 && (
                                  <div className="text-muted-foreground">מסחר: {building.commercial_area_sqm.toLocaleString()} מ״ר</div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

    
            {/* Ownership Summary */}
            {rightsRows.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>סיכום בעלויות</CardTitle>
                  <CardDescription>מידע על בעלי הנכס שהופק מהנסח טאבו</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Parcel Information */}
                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="text-center">
                        <div className="text-sm text-muted-foreground">גוש</div>
                        <div className="text-lg font-semibold">
                          {rightsRows.find(row => row.field?.includes('גוש'))?.value || '—'}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm text-muted-foreground">חלקה</div>
                        <div className="text-lg font-semibold">
                          {rightsRows.find(row => row.field?.includes('חלקה'))?.value || '—'}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm text-muted-foreground">תת חלקה</div>
                        <div className="text-lg font-semibold">
                          {rightsRows.find(row => row.field?.includes('תת חלקה'))?.value || '—'}
                        </div>
                      </div>
                    </div>

                    {/* Owners Table */}
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow className="rtl:flex-row-reverse">
                            <TableHead className="text-start">בעלים</TableHead>
                            <TableHead className="text-start">אחוז בעלות</TableHead>
                            <TableHead className="text-start">מספר זיהוי</TableHead>
                            <TableHead className="text-start">תאריך רכישה</TableHead>
                            <TableHead className="text-start">הערות</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {rightsRows
                            .filter(row => 
                              (row.field?.includes('בעלים') || row.field?.includes('owner')) &&
                              !row.field?.includes('משכנתה') && 
                              !row.field?.includes('בעלי המשכנתה')
                            )
                            .map((row, index) => {
                              const ownerName = row.value
                              
                              // Find ownership percentage - look for the specific field
                              const ownershipRow = rightsRows.find(r => 
                                r.field === 'החלק בנכס'
                              )
                              
                              // Convert fraction to percentage
                              const convertToPercentage = (value: string) => {
                                if (!value) return '—'
                                
                                // Handle "בשלמות" (full ownership) = 100%
                                if (value.includes('בשלמות')) return '100%'
                                
                                // Handle fractions like "1/2" = 50%
                                if (value.includes('/')) {
                                  const parts = value.split('/')
                                  if (parts.length === 2) {
                                    const numerator = parseFloat(parts[0])
                                    const denominator = parseFloat(parts[1])
                                    if (!isNaN(numerator) && !isNaN(denominator) && denominator !== 0) {
                                      const percentage = Math.round((numerator / denominator) * 100)
                                      return `${percentage}%`
                                    }
                                  }
                                }
                                
                                // Handle existing percentages
                                if (value.includes('%')) return value
                                
                                // Handle decimal numbers
                                const num = parseFloat(value)
                                if (!isNaN(num)) {
                                  if (num <= 1) {
                                    // Assume it's a decimal (0.5 = 50%)
                                    return `${Math.round(num * 100)}%`
                                  } else {
                                    // Assume it's already a percentage
                                    return `${Math.round(num)}%`
                                  }
                                }
                                
                                return value
                              }
                              
                              // Find ID number - look for the specific field
                              const idRow = rightsRows.find(r => 
                                r.field === 'מספר זיהוי' || r.field === 'ת.ז'
                              )
                              
                              // Find date - look for the specific field
                              const dateRow = rightsRows.find(r => 
                                r.field === 'תאריך רכישה' || r.field === 'תאריך'
                              )
                              
                              // Check for mortgages associated with this owner
                              const hasMortgage = rightsRows.some(r => 
                                r.field === 'בעלי המשכנתה' || 
                                (r.field === 'מהות פעולה' && r.value?.includes('משכנתה'))
                              )
                              
                              // Get mortgage details if available
                              const mortgageHolder = rightsRows.find(r => 
                                r.field === 'בעלי המשכנתה'
                              )
                              
                              const mortgageAmount = rightsRows.find(r => 
                                r.field === 'סכום'
                              )
                              
                              const getMortgageNotes = () => {
                                if (!hasMortgage) return '—'
                                
                                const notes = []
                                if (mortgageHolder?.value) {
                                  notes.push(`משכנתה: ${mortgageHolder.value}`)
                                }
                                if (mortgageAmount?.value) {
                                  notes.push(`סכום: ${mortgageAmount.value}`)
                                }
                                
                                return notes.length > 0 ? notes.join(', ') : 'יש משכנתה'
                              }
                              
                              return (
                                <TableRow key={index} className="rtl:flex-row-reverse">
                                  <TableCell className="text-start font-medium">
                                    {ownerName || '—'}
                                  </TableCell>
                                  <TableCell className="text-start">
                                    {convertToPercentage(ownershipRow?.value || '')}
                                  </TableCell>
                                  <TableCell className="text-start">
                                    {idRow?.value || '—'}
                                  </TableCell>
                                  <TableCell className="text-start">
                                    {dateRow?.value || '—'}
                                  </TableCell>
                                  <TableCell className="text-start text-sm">
                                    {getMortgageNotes()}
                                  </TableCell>
                                </TableRow>
                              )
                            })}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="environment" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>מידע סביבתי</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2" dir="rtl">
                {/* Environmental Measurements */}
                <div className="flex justify-between text-start">
                  <span className="text-muted-foreground">רמת רעש:</span>
                  {renderValue(asset.noiseLevel ? `${asset.noiseLevel}/5` : '—', 'noiseLevel')}
                </div>
                <div className="flex justify-between text-start">
                  <span className="text-muted-foreground">מרחק מאנטנה:</span>
                  {renderValue(asset.antennaDistanceM ? `${asset.antennaDistanceM} מ׳` : '—', 'antennaDistanceM')}
                </div>
                <div className="flex justify-between text-start">
                  <span className="text-muted-foreground">מרחק ממקלט:</span>
                  {renderValue(asset.shelterDistanceM ? `${asset.shelterDistanceM} מ׳` : '—', 'shelterDistanceM')}
                </div>
                
                {/* Environmental Features */}
                <div className="flex justify-between text-start">
                  <span className="text-muted-foreground">שטחים ירוקים:</span>
                  {renderValue(asset.greenWithin300m ? 'כן' : 'לא', 'greenWithin300m')}
                </div>
                <div className="flex justify-between text-start">
                  <span className="text-muted-foreground">תחבורה ציבורית:</span>
                  {renderValue(asset.publicTransport ?? '—', 'publicTransport')}
                </div>
                <div className="flex justify-between text-start">
                  <span className="text-muted-foreground">מבני ציבור:</span>
                  {renderValue(asset.publicBuildings ?? '—', 'publicBuildings')}
                </div>
                <div className="flex justify-between text-start">
                  <span className="text-muted-foreground">מצב חניה:</span>
                  {renderValue(asset.parking ?? '—', 'parking')}
                </div>
                <div className="flex justify-between text-start">
                  <span className="text-muted-foreground">פרויקטים סמוכים:</span>
                  {renderValue(asset.nearbyProjects ?? '—', 'nearbyProjects')}
                </div>
              </CardContent>
            </Card>

            {asset.riskFlags && asset.riskFlags.length > 0 && (
              <Card>
                <CardHeader>סיכונים</CardHeader>
                <CardBody className="flex flex-wrap gap-2">
                  {asset.riskFlags.map((flag: string, i: number) => (
                    <Badge key={i} variant={flag.includes('שימור') ? 'error' : 'warning'}>
                      {flag}
                    </Badge>
                  ))}
                </CardBody>
              </Card>
            )}

          </TabsContent>

          <TabsContent value="permits" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-start rtl:flex-row-reverse">
                  <div>
                    <CardTitle>היתרים</CardTitle>
                    <CardDescription>נתונים מעודכנים ממערכת ההיתרים של העירייה</CardDescription>
                  </div>
                  <div className="text-start">
                    <div className="text-2xl font-bold">{permitsData.total}</div>
                    <div className="text-sm text-muted-foreground">
                      בקשות פעילות ברדיוס {permitRadius} מטר
                    </div>
                  </div>
                </div>
              </CardHeader>
            </Card>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <Card>
                <CardHeader>נתוני גוש חלקה</CardHeader>
                <CardBody className="space-y-2" dir="rtl">
                  {/* Parcel Information */}
                  <div className="flex justify-between text-start">
                    <span className="text-muted-foreground">שטח חלקה:</span>
                    {renderValue(asset.parcelArea ? `${asset.parcelArea.toLocaleString()} מ״ר` : '—', 'parcelArea')}
                  </div>
                  <div className="flex justify-between text-start">
                    <span className="text-muted-foreground">סטטוס חלקה:</span>
                    {renderValue(asset.parcelStatus, 'parcelStatus')}
                  </div>
                  
                  {/* Block Information */}
                  <div className="flex justify-between text-start">
                    <span className="text-muted-foreground">שטח גוש:</span>
                    {renderValue(asset.blockArea ? `${asset.blockArea.toLocaleString()} מ״ר` : '—', 'blockArea')}
                  </div>
                  <div className="flex justify-between text-start">
                    <span className="text-muted-foreground">מספר חלקות בגוש:</span>
                    {renderValue(asset.blockTotalParcels, 'blockTotalParcels')}
                  </div>
                  
                  {/* Permit Information */}
                  <div className="flex justify-between text-start">
                    <span className="text-muted-foreground">מספר היתרים:</span>
                    {renderValue(asset.totalPermits, 'totalPermits')}
                  </div>
                  <div className="flex justify-between text-start">
                    <span className="text-muted-foreground">מספר בקשה:</span>
                    {renderValue(asset.permitRequestNum, 'permitRequestNum')}
                  </div>
                  <div className="flex justify-between text-start">
                    <span className="text-muted-foreground">יחידות דיור:</span>
                    {renderValue(asset.permitHousingUnits, 'permitHousingUnits')}
                  </div>
                  <div className="flex justify-between text-start">
                    <span className="text-muted-foreground">שטח מגורים:</span>
                    {renderValue(asset.permitResidentialArea ? `${asset.permitResidentialArea.toLocaleString()} מ״ר` : '—', 'permitResidentialArea')}
                  </div>
                  <div className="flex justify-between text-start">
                    <span className="text-muted-foreground">שטח חניה:</span>
                    {renderValue(asset.permitParkingArea ? `${asset.permitParkingArea.toLocaleString()} מ״ר` : '—', 'permitParkingArea')}
                  </div>
                  <div className="flex justify-between text-start">
                    <span className="text-muted-foreground">יחידות חניה:</span>
                    {renderValue(asset.permitParkingUnits, 'permitParkingUnits')}
                  </div>
                </CardBody>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>היתרי בנייה באזור</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4" dir="rtl">
                  <div className="space-y-2">
                    <div className="flex justify-between text-start">
                      <span className="text-muted-foreground">רבעון אחרון עם היתר:</span>
                      {renderValue(
                        <Badge variant={asset.lastPermitQ ? 'success' : 'neutral'}>
                          {asset.lastPermitQ ?? 'לא זמין'}
                        </Badge>,
                        'lastPermitQ'
                      )}
                    </div>
                    <div className="flex justify-between text-start">
                      <span className="text-muted-foreground">פעילות בנייה באזור:</span>
                      <span>{asset.lastPermitQ ? 'גבוהה' : 'נמוכה'}</span>
                    </div>
                  </div>
                  <div className="pt-2 border-t">
                    <div className="text-sm text-muted-foreground text-start">
                      נתונים מעודכנים ממערכת היתרי הבנייה של עיריית תל אביב
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>סטטוס היתרים</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4" dir="rtl">
                  <div className="space-y-2">
                    <div className="flex justify-between text-start">
                      <span className="text-muted-foreground">היתר בתוקף:</span>
                      {renderValue(<Badge variant="success">כן</Badge>, 'permitValid')}
                    </div>
                    <div className="flex justify-between text-start">
                      <span className="text-muted-foreground">סוג היתר:</span>
                      {renderValue('מגורים', 'permitType')}
                    </div>
                    <div className="flex justify-between text-start">
                      <span className="text-muted-foreground">אישורי חיבור:</span>
                      {renderValue(<Badge variant="success">מאושר</Badge>, 'utilityApprovals')}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <PermitsTable
              data={normalizedPermits}
              loading={permitsLoading}
              searchValue={permitsSearch}
              onSearchChange={setPermitsSearch}
              filters={{
                stage: {
                  value: permitsStageFilter,
                  onChange: setPermitsStageFilter,
                  options: [],
                },
                documentType: {
                  value: permitsTypeFilter,
                  onChange: setPermitsTypeFilter,
                  options: [],
                },
                source: {
                  value: permitsSourceFilter,
                  onChange: setPermitsSourceFilter,
                  options: [],
                },
              }}
              advancedFilters={{
                requestType: {
                  value: permitsRequestTypeFilter,
                  onChange: setPermitsRequestTypeFilter,
                },
                permitNumber: {
                  value: permitsPermitNumberFilter,
                  onChange: setPermitsPermitNumberFilter,
                },
                requestNumber: {
                  value: permitsRequestNumberFilter,
                  onChange: setPermitsRequestNumberFilter,
                },
                description: {
                  value: permitsDescriptionFilter,
                  onChange: setPermitsDescriptionFilter,
                },
                approvalDate: {
                  from: permitsApprovalDateFrom,
                  to: permitsApprovalDateTo,
                  onChange: ({ from, to }) => {
                    setPermitsApprovalDateFrom(from)
                    setPermitsApprovalDateTo(to)
                  },
                },
                expiryDate: {
                  from: permitsExpiryDateFrom,
                  to: permitsExpiryDateTo,
                  onChange: ({ from, to }) => {
                    setPermitsExpiryDateFrom(from)
                    setPermitsExpiryDateTo(to)
                  },
                },
              }}
              manualPagination
              manualSorting
              pageCount={Math.max(1, Math.ceil((permitsData.total || 0) / permitsPagination.pageSize))}
              paginationState={permitsPagination}
              onPaginationChange={setPermitsPagination}
              sortingState={permitsSorting}
              onSortingChange={setPermitsSorting}
              totalCount={permitsData.total}
              filterOptions={{
                stage: permitsData.filters.stage,
                documentType: permitsData.filters.document_type,
                source: permitsData.filters.source,
                requestType: permitsData.filters.request_type,
              }}
              onRefresh={loadPermits}
              radius={permitRadius}
            />
          </TabsContent>

          <TabsContent value="transactions" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>עיסקאות השוואה</CardTitle>
              </CardHeader>
              <CardBody className="space-y-4">
                <div className="grid gap-4 md:grid-cols-4">
                  <div className="text-center rtl:text-start">
                    <div className="text-2xl font-bold flex items-center justify-center gap-1">
                      {!!asset.pricePerSqm
                        ? formatCurrency(asset.pricePerSqm)
                        : '—'}
                      <DataBadge
                        source={asset?._meta?.pricePerSqm?.source}
                        fetchedAt={asset?._meta?.pricePerSqm?.fetched_at}
                      />
                    </div>
                    <div className="text-sm text-muted-foreground">מחיר למ״ר - נכס זה</div>
                  </div>
                  <div className="text-center rtl:text-start">
                    <div className="text-2xl font-bold">
                      {marketAnalysis?.avg_price_per_sqm !== null && marketAnalysis?.avg_price_per_sqm !== undefined
                        ? formatCurrency(marketAnalysis?.avg_price_per_sqm)
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">ממוצע מחיר למ״ר</div>
                  </div>
                  <div className="text-center rtl:text-start">
                    <div className="text-2xl font-bold">
                      {marketAnalysis?.min_price_per_sqm !== null && marketAnalysis?.max_price_per_sqm !== null
                        ? `${formatCurrency(marketAnalysis?.min_price_per_sqm)} - ${formatCurrency(marketAnalysis?.max_price_per_sqm)}`
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">טווח מחיר למ״ר</div>
                  </div>
                  <div className="text-center rtl:text-start">
                    <div className="text-2xl font-bold">
                      {!!asset.pricePerSqm && !!marketAnalysis?.avg_price_per_sqm
                        ? `${Math.round(((asset.pricePerSqm / marketAnalysis?.avg_price_per_sqm) - 1) * 100)}%`
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">פער מהממוצע</div>
                  </div>
                </div>
                </CardBody>
              </Card>

            {/* Transactions Table */}
            <TransactionsTable
              data={transactionsData.items}
              loading={transactionsLoading}
              searchValue={transactionsSearch}
              onSearchChange={setTransactionsSearch}
              filters={{
                source: {
                  value: transactionsSourceFilter,
                  onChange: setTransactionsSourceFilter,
                  options: transactionSourceOptions,
                },
              }}
              priceMin={transactionsPriceMin}
              onPriceMinChange={setTransactionsPriceMin}
              priceMax={transactionsPriceMax}
              onPriceMaxChange={setTransactionsPriceMax}
              pricePerSqmMin={transactionsPricePerSqmMin}
              onPricePerSqmMinChange={setTransactionsPricePerSqmMin}
              pricePerSqmMax={transactionsPricePerSqmMax}
              onPricePerSqmMaxChange={setTransactionsPricePerSqmMax}
              areaRange={{
                min: transactionsAreaMin,
                max: transactionsAreaMax,
                onChange: ({ min, max }) => {
                  setTransactionsAreaMin(min)
                  setTransactionsAreaMax(max)
                },
              }}
              addressFilter={{
                value: transactionsAddressFilter,
                onChange: setTransactionsAddressFilter,
              }}
              onRefresh={loadTransactions}
              manualPagination
              manualSorting
              pageCount={Math.max(1, Math.ceil((transactionsData.total || 0) / transactionsPagination.pageSize))}
              paginationState={transactionsPagination}
              onPaginationChange={(updater) => {
                setTransactionsPagination((prev) =>
                  typeof updater === 'function' ? updater(prev) : updater
                )
              }}
              sortingState={transactionsSorting}
              onSortingChange={(updater) => {
                setTransactionsSorting((prev) =>
                  typeof updater === 'function' ? updater(prev) : updater
                )
              }}
              totalCount={transactionsData.total}
              filterOptions={{
                source: transactionsData.filters.source,
              }}
            />
          </TabsContent>

          <TabsContent value="appraisals" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center rtl:flex-row-reverse">
                  <div>
                    <CardTitle>שומות באיזור - שומות מכריעות, רמ״י ועוד</CardTitle>
                    <CardDescription>
                      מידע מעודכן מרמ״י, שומות מכריעות ועסקאות השוואה באזור
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      fetch(`/api/assets/${id}/appraisal`)
                        .then(res => res.json())
                        .then(data => {
                          setAppraisal(data.appraisal || null)
                          setDecisiveAppraisals(data.decisive_appraisals || [])
                          setRamiAppraisals(data.rami_appraisals || [])
                        })
                        .catch(err => console.error('Error refreshing appraisal:', err))
                      
                      loadTransactions()
                    }}
                  >
                    🔄 רענן מידע
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {appraisal ? (
                  <>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <h3 className="font-medium mb-2">הכרעות שמאי</h3>
                        <div className="space-y-2">
                          <div className="p-3 border rounded rtl:text-start">
                            <div className="font-medium">{appraisal.appraiser}</div>
                            <div className="text-sm text-muted-foreground">
                              {appraisal.date && new Date(appraisal.date).toLocaleDateString('he-IL')}
                            </div>
                            <div className="text-sm">{formatCurrency(appraisal.appraisedValue)}</div>
                            {appraisal.source && (
                              <div className="text-xs text-blue-600 mt-1">
                                מקור: {appraisal.source === 'external_decisive' ? 'שומות מכריעות' : 'מאגר פנימי'}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      <div>
                        <h3 className="font-medium mb-2">שומות רמ״י</h3>
                        <div className="space-y-2">
                          <div className="p-3 border rounded rtl:text-start">
                            <div className="font-medium">
                              {appraisal.plan_number ? `תכנית ${appraisal.plan_number}` : 'שומת רמ״י מעודכנת'}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {appraisal.date && new Date(appraisal.date).toLocaleDateString('he-IL')}
                            </div>
                            <div className="text-sm">
                              {asset?.area
                                ? `${formatCurrency(Math.round(appraisal.marketValue / asset.area))}/מ״ר`
                                : formatCurrency(appraisal.marketValue)}
                            </div>
                            {appraisal.source && (
                              <div className="text-xs text-blue-600 mt-1">
                                מקור: {appraisal.source === 'external_rami' ? 'רמ״י' : 'מאגר פנימי'}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    <Card>
                      <CardHeader>
                        <CardTitle>השוואת שומות</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid gap-4 md:grid-cols-3">
                          <div className="text-center rtl:text-start">
                            <div className="text-2xl font-bold">
                              {formatCurrency(appraisal.appraisedValue)}
                            </div>
                            <div className="text-sm text-muted-foreground">הכרעת שמאי</div>
                          </div>
                          <div className="text-center rtl:text-start">
                            <div className="text-2xl font-bold">
                              {formatCurrency(appraisal.marketValue)}
                            </div>
                            <div className="text-sm text-muted-foreground">שומת רמ״י</div>
                          </div>
                          <div className="text-center rtl:text-start">
                            <div className="text-2xl font-bold">
                              {!!asset.price
                                ? `₪${(asset.price / 1000000).toFixed(1)}M`
                                : '—'}
                            </div>
                            <div className="text-sm text-muted-foreground">מחיר מבוקש</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </>
                ) : (
                  <div className="text-center text-muted-foreground">
                    <div className="py-8">
                      <div className="text-lg mb-2">אין נתוני שומה זמינים</div>
                      <div className="text-sm">
                        המידע יטען אוטומטית מרמ״י ושומות מכריעות
                      </div>
                    </div>
                  </div>
                )}

                <div className="space-y-4">
                  {normalizedDecisiveAppraisals.length > 0 && (
                    <DecisiveAppraisalsTable
                      data={normalizedDecisiveAppraisals}
                      searchValue={decisiveSearch}
                      onSearchChange={setDecisiveSearch}
                      filters={{
                        source: {
                          value: decisiveSourceFilter,
                          onChange: setDecisiveSourceFilter,
                        },
                      }}
                      onRefresh={() => {
                        fetch(`/api/assets/${id}/appraisal`)
                          .then(res => res.json())
                          .then(data => {
                            setDecisiveAppraisals(data.decisive_appraisals || [])
                            setRamiAppraisals(data.rami_appraisals || [])
                          })
                          .catch(err => console.error('Error refreshing appraisal tables:', err))
                      }}
                    />
                  )}

                  {normalizedRamiAppraisals.length > 0 && (
                    <RamiAppraisalsTable
                      data={normalizedRamiAppraisals}
                      searchValue={ramiSearch}
                      onSearchChange={setRamiSearch}
                      filters={{
                        source: {
                          value: ramiSourceFilter,
                          onChange: setRamiSourceFilter,
                        },
                        status: {
                          value: ramiStatusFilter,
                          onChange: setRamiStatusFilter,
                        },
                      }}
                      onRefresh={() => {
                        fetch(`/api/assets/${id}/appraisal`)
                          .then(res => res.json())
                          .then(data => {
                            setDecisiveAppraisals(data.decisive_appraisals || [])
                            setRamiAppraisals(data.rami_appraisals || [])
                          })
                          .catch(err => console.error('Error refreshing appraisal tables:', err))
                      }}
                    />
                  )}

                  {normalizedDecisiveAppraisals.length === 0 && normalizedRamiAppraisals.length === 0 && (
                    <div className="rounded-xl border border-dashed border-border p-6 text-center text-muted-foreground">
                      לא נמצאו שומות מכריעות או שומות רמ״י לנכס זה.
                    </div>
                  )}
                </div>

              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="documents" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center rtl:flex-row-reverse">
                  <CardTitle>מסמכים</CardTitle>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={loadDocumentsTable}
                      disabled={documentsLoading}
                    >
                      {documentsLoading ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin me-2" />
                          טוען...
                        </>
                      ) : (
                        <>
                          <RefreshCw className="h-4 w-4 me-2" />
                          רענן
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <form
                  onSubmit={handleUpload}
                  className="flex flex-col md:flex-row gap-2"
                  encType="multipart/form-data"
                >
                  <input type="file" name="file" required className="flex-1" />
                  <select
                    name="type"
                    className="border rounded p-2"
                    defaultValue="tabu"
                  >
                    <option value="tabu">נסח טאבו</option>
                    <option value="condo_plan">תשריט בית משותף</option>
                    <option value="appraisal_decisive">שומת מכרעת</option>
                    <option value="appraisal_rmi">שומת רמ״י</option>
                    <option value="permit">היתר</option>
                    <option value="rights">זכויות</option>
                  </select>
                  <Button type="submit" size="sm" disabled={uploading}>
                    {uploading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        מעלה...
                      </>
                    ) : (
                      'העלה'
                    )}
                  </Button>
                </form>
                {/* Error Display */}
                {documentsError && (
                  <div className="text-red-600 text-sm bg-red-50 p-3 rounded">
                    {documentsError}
                  </div>
                )}

                <DocumentsTable
                  data={documentsTableData}
                  loading={documentsLoading}
                  searchValue={documentsTableSearch}
                  onSearchChange={setDocumentsTableSearch}
                  filters={{
                    category: {
                      value: documentsCategoryFilter,
                      onChange: setDocumentsCategoryFilter,
                    },
                    type: {
                      value: documentsTypeFilter,
                      onChange: setDocumentsTypeFilter,
                    },
                    source: {
                      value: documentsSourceFilter,
                      onChange: setDocumentsSourceFilter,
                    },
                    status: {
                      value: documentsStatusFilter,
                      onChange: setDocumentsStatusFilter,
                    },
                  }}
                  onRefresh={loadDocumentsTable}
                  totalCount={documentsData.total}
                  paginationState={documentsPagination}
                  onPaginationChange={setDocumentsPagination}
                  sortingState={documentsSorting}
                  onSortingChange={setDocumentsSorting}
                  disableInternalFiltering
                  availableFilters={availableDocumentFilters}
                />
              </CardContent>
            </Card>
          </TabsContent>

          {canViewCrm && (
            <TabsContent value="crm" className="space-y-4">
              <AssetLeadsPanel
                assetId={parseInt(id)}
                assetAddress={asset.address}
              />
            </TabsContent>
          )}

          <TabsContent value="listings" className="space-y-4">
            <ListingsPanel 
              assetId={parseInt(id)} 
              assetAddress={asset.address}
            />
          </TabsContent>

          <TabsContent value="contributions" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-start">תרומות קהילה</CardTitle>
                <p className="text-sm text-muted-foreground text-start">
                  היסטוריית התרומות והעדכונים שנעשו על הנכס הזה על ידי חברי הקהילה
                </p>
              </CardHeader>
              <CardContent className="space-y-4 text-start">
                {/* Attribution Summary */}
                {asset.attribution && (
                  <div className="grid gap-3 lg:grid-cols-2">
                    {asset.attribution.created_by && (
                      <div className="p-3 border rounded-lg text-start">
                        <h3 className="font-medium mb-2 text-sm">יוצר הנכס</h3>
                        <div className="flex items-center gap-2 rtl:flex-row-reverse">
                          <div className="flex-1 text-start">
                            <p className="font-medium text-sm truncate">{asset.attribution.created_by.name}</p>
                            <p className="text-xs text-muted-foreground truncate">{asset.attribution.created_by.email}</p>
                          </div>
                          <div className="w-7 h-7 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                            <span className="text-xs font-medium">
                              {asset.attribution.created_by.name.charAt(0).toUpperCase()}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {asset.attribution.last_updated_by && asset.attribution.last_updated_by.id !== asset.attribution.created_by?.id && (
                      <div className="p-3 border rounded-lg text-start">
                        <h3 className="font-medium mb-2 text-sm">עודכן לאחרונה על ידי</h3>
                        <div className="flex items-center gap-2 rtl:flex-row-reverse">
                          <div className="flex-1 text-start">
                            <p className="font-medium text-sm truncate">{asset.attribution.last_updated_by.name}</p>
                            <p className="text-xs text-muted-foreground truncate">{asset.attribution.last_updated_by.email}</p>
                          </div>
                          <div className="w-7 h-7 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                            <span className="text-xs font-medium">
                              {asset.attribution.last_updated_by.name.charAt(0).toUpperCase()}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Recent Contributions */}
                <div className="text-start">
                  <h3 className="font-medium mb-3 text-sm">תרומות אחרונות</h3>
                  {asset.recent_contributions && asset.recent_contributions.length > 0 ? (
                    <div className="space-y-2">
                      {asset.recent_contributions.map((contrib: any, idx: number) => (
                        <div key={idx} className="flex items-start gap-2 p-2 border rounded-lg rtl:flex-row-reverse">
                          <div className="flex-1 text-start">
                            <div className="flex items-center justify-between rtl:flex-row-reverse mb-1">
                              <p className="font-medium text-sm">{contrib.user.name}</p>
                              <span className="text-xs text-muted-foreground">
                                {new Date(contrib.created_at).toLocaleDateString('he-IL')}
                              </span>
                            </div>
                            <p className="text-xs text-muted-foreground mb-1">
                              {getContributionTypeDisplay(contrib.type)}
                              {contrib.field_name && ` - ${contrib.field_name}`}
                            </p>
                            {contrib.description && (
                              <p className="text-xs text-start text-muted-foreground">{contrib.description}</p>
                            )}
                            {contrib.source && (
                              <span className="inline-block px-1.5 py-0.5 text-xs bg-secondary rounded-full mt-1">
                                {getSourceDisplay(contrib.source)}
                              </span>
                            )}
                          </div>
                          <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                            <span className="text-xs font-medium">
                              {contrib.user.name.charAt(0).toUpperCase()}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-6 text-muted-foreground">
                      <p className="text-sm">אין תרומות זמינות</p>
                      <p className="text-xs">היה הראשון לתרום מידע על הנכס הזה!</p>
                    </div>
                  )}
                </div>

                {/* Community Stats */}
                <div className="grid gap-2 grid-cols-3">
                  <div className="p-2 border rounded-lg text-center text-start">
                    <div className="text-lg font-bold text-primary">
                      {asset.recent_contributions?.length || 0}
                    </div>
                    <div className="text-xs text-muted-foreground">תרומות</div>
                  </div>
                  <div className="p-2 border rounded-lg text-center text-start">
                    <div className="text-lg font-bold text-primary">
                      {asset.attribution?.created_by ? 1 : 0}
                    </div>
                    <div className="text-xs text-muted-foreground">יוצר</div>
                  </div>
                  <div className="p-2 border rounded-lg text-center text-start">
                    <div className="text-lg font-bold text-primary">
                      {new Set(asset.recent_contributions?.map((c: any) => c.user.id) || []).size}
                    </div>
                    <div className="text-xs text-muted-foreground">תורמים</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  )
}
