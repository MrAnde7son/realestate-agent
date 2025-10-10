'use client'
import React, { useState, useEffect } from 'react'
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
  CardFooter,
} from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import DataBadge from '@/components/DataBadge'
import * as Tooltip from '@radix-ui/react-tooltip'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { PageLoader } from '@/components/ui/page-loader'
import { ArrowLeft, RefreshCw, FileText, Loader2, Home, Building } from 'lucide-react'
import ImageGallery from '@/components/ImageGallery'
import DocumentSearch from '@/components/DocumentSearch'
import DocumentCategory from '@/components/DocumentCategory'
import { useAuth } from '@/lib/auth-context'
import { apiClient } from '@/lib/api-client'
import OnboardingProgress from '@/components/OnboardingProgress'
import { selectOnboardingState, getCompletionPct } from '@/onboarding/selectors'
import { AssetLeadsPanel } from '@/components/crm/asset-leads-panel'
import PlansTable from '@/components/PlansTable'
import TransactionsTable from '@/components/TransactionsTable'
import { ListingsPanel } from '@/components/crm/listings-panel'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'

const ALL_SECTIONS = ['summary','permits','plans','environment','comparables','mortgage','appendix']

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

export default function AssetDetail({ params }: { params: { id: string } }) {
  const { trackFeatureUsage } = useAnalytics()
  const [asset, setAsset] = useState<any>(null)
  const [comparables, setComparables] = useState<any[]>([])
  const [appraisal, setAppraisal] = useState<any | null>(null)
  const [decisiveAppraisals, setDecisiveAppraisals] = useState<any[]>([])
  const [ramiAppraisals, setRamiAppraisals] = useState<any[]>([])
  const [comparableTransactions, setComparableTransactions] = useState<any[]>([])
  const [marketAnalysis, setMarketAnalysis] = useState<any>(null)
  const [permits, setPermits] = useState<any[]>([])
  const [plans, setPlans] = useState<any[]>([])
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
  const [documentsSearch, setDocumentsSearch] = useState('')
  const [documentsByCategory, setDocumentsByCategory] = useState<any>({})
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [documentsError, setDocumentsError] = useState<string | null>(null)
  const [rightsSearch, setRightsSearch] = useState('')
  const [rightsDocFilter, setRightsDocFilter] = useState('all')
  const [calculatedRights, setCalculatedRights] = useState<any>(null)
  const [transactionsSearch, setTransactionsSearch] = useState('')
  const [appraisalsSearch, setAppraisalsSearch] = useState('')
  const [plansSearch, setPlansSearch] = useState('')
  const [plansSourceFilter, setPlansSourceFilter] = useState('all')
  const [plansStatusFilter, setPlansStatusFilter] = useState('all')
  const [transactionsSourceFilter, setTransactionsSourceFilter] = useState('all')
  const [transactionsAreaFilter, setTransactionsAreaFilter] = useState('all')
  const [permitsSearch, setPermitsSearch] = useState('')
  const router = useRouter()
  const searchParams = useSearchParams()
  const { id } = params
  const { user, isAuthenticated } = useAuth()
  const canViewCrm = ['broker', 'appraiser', 'admin'].includes(user?.role || '')
  const onboardingState = React.useMemo(() => selectOnboardingState(user), [user])
  const renderValue = (value: React.ReactNode, key: string) => (
    <span className="flex items-center gap-1">
      {value ?? '—'}
      <DataBadge source={asset?._meta?.[key]?.source} fetchedAt={asset?._meta?.[key]?.fetched_at} url={asset?._meta?.[key]?.url} />
    </span>
  )

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

  // Combine all document sources into a unified list
  const getAllDocuments = () => {
    const allDocs: any[] = []
    
    // Helper function to translate document types to Hebrew
    const translateDocumentType = (type: string) => {
      const translations: Record<string, string> = {
        'tabu': 'נסח טאבו',
        'condo_plan': 'תשריט בית משותף',
        'appraisal_decisive': 'שומה החלטית',
        'appraisal_rmi': 'שומת רמ״י',
        'permit': 'היתר בנייה',
        'rights': 'זכויות',
        'plan': 'תכנית',
        'other': 'אחר'
      }
      return translations[type] || type
    }
    
    // Helper function to translate sources to Hebrew
    const translateSource = (source: string) => {
      const translations: Record<string, string> = {
        'user_upload': 'העלאה ידנית',
        'GIS': 'מערכת מידע גיאוגרפית',
        'gis_permit': 'מערכת מידע גיאוגרפית',
        'gis_rights': 'מערכת מידע גיאוגרפית',
        'RAMI': 'רמ״י',
        'rami_plan': 'רמ״י',
        'Mavat': 'מבת',
        'Gov': 'ממשלתי',
        'tabu': 'טאבו',
        'tabu_upload': 'טאבו',
        'meta_migration': 'העברה מנתונים קיימים',
        'yad2': 'יד2',
        'nadlan': 'נדלן',
        'pipeline': 'צינור נתונים',
        'external': 'מקור חיצוני'
      }
      return translations[source] || source
    }
    
    // 1. User-uploaded documents from asset.documents
    console.log('🔍 getAllDocuments - asset:', asset)
    console.log('🔍 getAllDocuments - asset.documents:', asset?.documents)
    if (asset?.documents) {
      console.log('📄 Processing', asset.documents.length, 'user-uploaded documents')
      allDocs.push(...asset.documents.map((doc: any) => ({
        ...doc,
        type: translateDocumentType(doc.type || doc.document_type),
        source: translateSource(doc.source || 'user_upload'),
        category: 'מסמכים שהועלו ידנית'
      })))
    } else {
      console.log('❌ No asset.documents found')
    }
    
    // 2. Permits from GIS
    if (permits && permits.length > 0) {
      allDocs.push(...permits.map((permit: any) => ({
        id: `permit_${permit.permission_num}`,
        title: permit.koteret || `היתר בנייה ${permit.permission_num}`,
        type: translateDocumentType('permit'),
        url: permit.url_hadmaya,
        source: translateSource('GIS'),
        category: 'היתרי בנייה',
        date: permit.permission_date,
        description: permit.sug_bakasha,
        external_id: permit.permission_num
      })))
    }
    
    // 3. Plans
    if (plans && plans.length > 0) {
      allDocs.push(...plans.map((plan: any) => ({
        id: `plan_${plan.id}`,
        title: plan.description || `תכנית ${plan.plan_number}`,
        type: translateDocumentType('plan'),
        url: plan.file_url,
        source: translateSource(plan.source === 'rami' ? 'RAMI' : plan.source === 'mavat' ? 'Mavat' : 'Local'),
        category: plan.source === 'rami' ? 'תכניות רמ״י' : plan.source === 'mavat' ? 'תכניות מנהל התיכנון' : 'תכניות מקומיות',
        status: plan.status,
        external_id: plan.plan_number
      })))
    }
    
    // 5. Decisive appraisals
    if (decisiveAppraisals && decisiveAppraisals.length > 0) {
      allDocs.push(...decisiveAppraisals.map((appraisal: any) => ({
        id: `decisive_${appraisal.id}`,
        title: `שומה החלטית ${appraisal.id}`,
        type: translateDocumentType('appraisal_decisive'),
        url: appraisal.url,
        source: translateSource('Gov'),
        category: 'שומות מכריעות',
        date: appraisal.date,
        external_id: appraisal.id
      })))
    }
    
    // 6. RAMI appraisals
    if (ramiAppraisals && ramiAppraisals.length > 0) {
      allDocs.push(...ramiAppraisals.map((appraisal: any) => ({
        id: `rami_appraisal_${appraisal.id}`,
        title: `שומת רמ״י ${appraisal.id}`,
        type: translateDocumentType('appraisal_rmi'),
        url: appraisal.url,
        source: translateSource('RAMI'),
        category: 'שומות רמ״י',
        date: appraisal.date,
        external_id: appraisal.id
      })))
    }
    
    return allDocs
  }

  const formatPercent = (value?: number, digits = 0) =>
    value !== undefined && value !== null
      ? `${value.toFixed(digits)}%`
      : null

  const avgCompPricePerSqm = comparableTransactions.length
    ? Math.round(
        comparableTransactions.reduce(
          (sum, c) => sum + (c.price_per_sqm || 0),
          0
        ) / comparableTransactions.length
      )
    : null

  const permitRadius = asset?._meta?.radius ?? 50

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
      setCalculatedRights(() => data.calculated_rights || null)
      
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

  const rightsDocOptions = React.useMemo(() => {
    const entries = new Map<string, { title: string; url?: string }>()
    rightsRows.forEach(row => {
      const docId = row?.document_id ? String(row.document_id) : null
      if (!docId) return
      if (!entries.has(docId)) {
        entries.set(docId, {
          title: row.document_title || `מסמך ${docId}`,
          url: row.document_url
        })
      }
    })
    return Array.from(entries.entries()).map(([value, info]) => ({ value, ...info }))
  }, [rightsRows])

  const filteredRights = React.useMemo(() => {
    const searchTerm = rightsSearch.trim().toLowerCase()
    return rightsRows.filter(row => {
      const docId = row?.document_id ? String(row.document_id) : ''
      const matchesDoc = rightsDocFilter === 'all' || rightsDocFilter === docId
      if (!matchesDoc) return false
      if (!searchTerm) return true
      const field = (row?.field || '').toLowerCase()
      const value = (row?.value || '').toLowerCase()
      return field.includes(searchTerm) || value.includes(searchTerm)
    })
  }, [rightsRows, rightsDocFilter, rightsSearch])

  // Load documents organized by category
  const loadDocumentsByCategory = React.useCallback(async () => {
    if (!id) return
    
    setDocumentsLoading(true)
    setDocumentsError(null)
    
    try {
      const response = await apiClient.get(`/api/documents/by_category/?asset_id=${id}`)
      
      if (response.ok) {
        setDocumentsByCategory(response.data)
      } else {
        console.error('Failed to load documents by category:', response.error)
        setDocumentsError('שגיאה בטעינת מסמכים')
        setDocumentsByCategory({})
      }
    } catch (error) {
      console.error('Error loading documents by category:', error)
      setDocumentsError('שגיאה בטעינת מסמכים')
      setDocumentsByCategory({})
    } finally {
      setDocumentsLoading(false)
    }
  }, [id])

  // Handle document search results
  const handleDocumentResults = React.useCallback((results: any) => {
    if (results.type === 'category') {
      setDocumentsByCategory(results.data)
    } else if (results.type === 'search') {
      // Convert search results to category format for display
      const searchResultsByCategory: any = {}
      results.data.forEach((doc: any) => {
        const category = doc.hebrew_category || 'אחר'
        if (!searchResultsByCategory[category]) {
          searchResultsByCategory[category] = []
        }
        searchResultsByCategory[category].push(doc)
      })
      setDocumentsByCategory(searchResultsByCategory)
    } else if (results.type === 'error') {
      setDocumentsError('שגיאה בחיפוש מסמכים')
      setDocumentsByCategory({})
    }
  }, [])

  // Load documents when component mounts
  React.useEffect(() => {
    loadDocumentsByCategory()
  }, [loadDocumentsByCategory])

  useEffect(() => {
    setLoading(true)
    apiClient.get(`/api/assets/${id}`)
      .then(response => {
        if (!response.ok) throw new Error(response.error || 'Failed to load asset')
        const assetData = response.data?.asset || response.data
        console.log('🔍 Asset data received:', assetData)
        console.log('📄 Documents in asset:', assetData.documents)
        console.log('📄 Documents count:', assetData.documents?.length || 0)
        setAsset(assetData)
      })
      .catch(err => {
        console.error('Error loading asset:', err)
        setError('שגיאה בטעינת הנכס')
      })
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
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
  }, [id])

  useEffect(() => {
    fetch(`/api/assets/${id}/transactions`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to load transactions')
        return res.json()
      })
      .then(data => {
        setComparableTransactions(data.transactions || [])
        setMarketAnalysis(data.market_analysis || null)
      })
      .catch(err => console.error('Error loading transactions:', err))
  }, [id])

  useEffect(() => {
    fetch(`/api/assets/${id}/permits`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to load permits')
        return res.json()
      })
      .then(data => setPermits(data.permits || []))
      .catch(err => console.error('Error loading permits:', err))
  }, [id])

  useEffect(() => {
    fetch(`/api/assets/${id}/plans`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to load plans')
        return res.json()
      })
      .then(data => {
        setPlans(data.plans || [])
      })
      .catch(err => console.error('Error loading plans:', err))
  }, [id])

  useEffect(() => {
    loadRightsData()
  }, [loadRightsData])

  useEffect(() => {
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
                <ArrowLeft className="h-4 w-4" />
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
                <ArrowLeft className="h-4 w-4" />
                חזרה לרשימה
              </Link>
            </Button>
          </div>
          <p>{error || 'לא הצלחנו לטעון את פרטי הנכס המבוקש.'}</p>
        </div>
      </DashboardLayout>
    )
  }

  const manualDocs =
    asset?.documents?.filter(
      (d: any) => d.type === 'tabu' || d.type === 'condo_plan' || d.type === 'contract' || d.type === 'deed' || d.type === 'other'
    ) ?? []
  const permitDocs =
    asset?.documents?.filter((d: any) => d.type === 'permit') ?? []
  const rightsDocs =
    asset?.documents?.filter((d: any) => d.type === 'rights' || d.type === 'plan') ?? []
  const decisiveDocs =
    asset?.documents?.filter((d: any) => d.type === 'appraisal_decisive' || (d.type === 'appraisal' && d.source === 'מנהל התכנון')) ?? []
  const rmiDocs =
    asset?.documents?.filter((d: any) => d.type === 'appraisal_rmi' || (d.type === 'appraisal' && d.source === 'RAMI')) ?? []

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
        body: JSON.stringify({ language })
      })
      if (res.ok) {
        const data = await res.json()
        setShareMessage(data.text)
        setShareUrl(data.share_url)
        
        // Track marketing message creation
        trackFeatureUsage('marketing_message', parseInt(id), {
          message_type: 'share_message',
          language: language
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
                <ArrowLeft className="h-4 w-4" />
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
          <div className="w-full text-right space-y-2 md:w-auto">
            <div className="text-3xl font-bold">{formatCurrency(asset.price) ?? '—'}</div>
            <div className="text-muted-foreground">
              {asset.pricePerSqm !== undefined && asset.pricePerSqm !== null
                ? `${formatCurrency(asset.pricePerSqm)}/מ״ר`
                : '—'}
            </div>
            {/* Attribution Information */}
            {asset.attribution && (
              <div className="text-xs text-muted-foreground mt-2 space-y-1 text-right">
                {asset.attribution.created_by && (
                  <div className="text-right">
                    <span className="font-medium">נוצר על ידי: </span>
                    <span>{asset.attribution.created_by.name}</span>
                  </div>
                )}
                {asset.attribution.last_updated_by && asset.attribution.last_updated_by.id !== asset.attribution.created_by?.id && (
                  <div className="text-right">
                    <span className="font-medium">עודכן לאחרונה על ידי: </span>
                    <span>{asset.attribution.last_updated_by.name}</span>
                  </div>
                )}
                {asset.recent_contributions && asset.recent_contributions.length > 0 && (
                  <div className="text-right">
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
        {asset.images && asset.images.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>תמונות הנכס</CardTitle>
            </CardHeader>
            <CardContent>
              <ImageGallery 
                images={asset.images} 
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
                {asset.remainingRightsSqm !== undefined && asset.remainingRightsSqm !== null
                  ? `+${formatNumber(asset.remainingRightsSqm)} מ״ר`
                  : '—'}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-sm text-muted-foreground">רמת רעש</div>
              <div className="text-2xl font-bold">
                {asset.noiseLevel !== undefined && asset.noiseLevel !== null
                  ? `${asset.noiseLevel}/5`
                  : '—'}
              </div>
            </CardContent>
          </Card>
        </div>

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
          <TabsList className="flex flex-wrap md:flex-nowrap">
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
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">חדרים:</span>
                    <span>{asset.rooms ?? '—'}</span>
                  </div>
                  <div className="flex justify-between">
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
              data={plans}
              loading={false}
              searchValue={plansSearch}
              onSearchChange={setPlansSearch}
              filters={{
                source: {
                  value: plansSourceFilter,
                  onChange: setPlansSourceFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'rami', label: 'רמ״י' },
                    { value: 'mavat', label: 'מנהל התיכנון' },
                    { value: 'unknown', label: 'מקומי' }
                  ]
                },
                status: {
                  value: plansStatusFilter,
                  onChange: setPlansStatusFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    ...Array.from(new Set((plans || []).map(p => p.status).filter(Boolean))).map(status => ({
                      value: status,
                      label: status
                    }))
                  ]
                }
              }}
              onRefresh={() => {
                // Refresh plans data
                fetch(`/api/assets/${id}/plans`)
                  .then(res => {
                    if (!res.ok) throw new Error('Failed to load plans')
                    return res.json()
                  })
                  .then(data => {
                    setPlans(data.plans || [])
                  })
                  .catch(err => console.error('Error loading plans:', err))
              }}
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
                      {calculatedRights?.summary?.remaining_rights_sqm 
                        ? formatNumber(calculatedRights.summary.remaining_rights_sqm)
                        : formatNumber(asset.remainingRightsSqm) ?? '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">מ״ר זכויות נותרות</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {calculatedRights?.summary?.additional_rights_percentage 
                        ? `${calculatedRights.summary.additional_rights_percentage}%`
                        : (!!asset.remainingRightsSqm && !!asset.area
                            ? `${Math.round((asset.remainingRightsSqm / asset.area) * 100)}%`
                            : '—')}
                    </div>
                    <div className="text-sm text-muted-foreground">אחוז זכויות נוספות</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {calculatedRights?.summary?.estimated_rights_value_k 
                        ? `₪${calculatedRights.summary.estimated_rights_value_k}K`
                        : (!!asset.pricePerSqm && !!asset.remainingRightsSqm
                            ? `₪${Math.round((asset.pricePerSqm * asset.remainingRightsSqm * 0.7) / 1000)}K`
                            : '—')}
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
                      {calculatedRights.building_privileges?.parking_requirements && calculatedRights.building_privileges.parking_requirements.length > 0 && (
                        <div className="p-3 border rounded-lg">
                          <div className="text-sm font-medium text-muted-foreground">חניה</div>
                          <div className="text-xl font-bold">{calculatedRights.building_privileges.parking_requirements[0]?.area_sqm || '—'}</div>
                          <div className="text-sm text-muted-foreground">מ״ר</div>
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
                              <div className="text-right text-sm">
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

    
            {/* Privilege Page Data */}
            {rightsRows.some(row => row.source === 'privilege_page') && (
              <Card>
                <CardHeader>
                  <CardTitle>דף זכויות בנייה</CardTitle>
                  <CardDescription>נתונים מדף הזכויות של עיריית תל אביב</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {/* Building Lines */}
                    {rightsRows.some(row => row.type === 'building_line') && (
                      <div>
                        <h4 className="text-lg font-semibold mb-3">קווי בניין</h4>
                        <div className="space-y-2">
                          {rightsRows
                            .filter(row => row.type === 'building_line')
                            .map((row: any) => (
                              <div key={row.id} className="p-3 border rounded-lg bg-blue-50">
                                <div className="text-sm text-muted-foreground">קו בניין</div>
                                <div className="text-lg font-medium">{row.description}</div>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* Floor Details */}
                    {rightsRows.some(row => row.type === 'floor_details') && (
                      <div>
                        <h4 className="text-lg font-semibold mb-3">פרטי קומות</h4>
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                          {rightsRows
                            .filter(row => row.type === 'floor_details')
                            .map((row: any) => (
                              <div key={row.id} className="p-3 border rounded-lg">
                                <div className="text-sm text-muted-foreground">{row.type}</div>
                                <div className="text-lg font-medium">
                                  {row.percentage ? `${row.percentage}%` : row.area_sqm ? `${row.area_sqm} מ״ר` : '—'}
                                </div>
                                <div className="text-xs text-muted-foreground mt-1">קומה</div>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* Specific Rights */}
                    {rightsRows.some(row => row.type === 'specific_right') && (
                      <div>
                        <h4 className="text-lg font-semibold mb-3">זכויות ספציפיות</h4>
                        <div className="space-y-2">
                          {rightsRows
                            .filter(row => row.type === 'specific_right')
                            .map((row: any) => (
                              <div key={row.id} className="p-3 border rounded-lg bg-green-50">
                                <div className="text-sm text-muted-foreground">זכות בנייה</div>
                                <div className="text-lg font-medium">{row.description}</div>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* General Notes */}
                    {rightsRows.some(row => row.source === 'privilege_page' && row.type === 'general') && (
                      <div>
                        <h4 className="text-lg font-semibold mb-3">הערות כלליות</h4>
                        <div className="space-y-2">
                          {rightsRows
                            .filter(row => row.source === 'privilege_page' && row.type === 'general')
                            .map((row: any) => (
                              <div key={row.id} className="p-3 border rounded-lg bg-gray-50">
                                <div className="text-sm text-muted-foreground">הערה</div>
                                <div className="text-lg font-medium">{row.text}</div>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                  </div>
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
                            <TableHead className="text-right">בעלים</TableHead>
                            <TableHead className="text-right">אחוז בעלות</TableHead>
                            <TableHead className="text-right">מספר זיהוי</TableHead>
                            <TableHead className="text-right">תאריך רכישה</TableHead>
                            <TableHead className="text-right">הערות</TableHead>
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
                                  <TableCell className="text-right font-medium">
                                    {ownerName || '—'}
                                  </TableCell>
                                  <TableCell className="text-right">
                                    {convertToPercentage(ownershipRow?.value || '')}
                                  </TableCell>
                                  <TableCell className="text-right">
                                    {idRow?.value || '—'}
                                  </TableCell>
                                  <TableCell className="text-right">
                                    {dateRow?.value || '—'}
                                  </TableCell>
                                  <TableCell className="text-right text-sm">
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
                <div className="flex justify-between text-right">
                  <span className="text-muted-foreground">רמת רעש:</span>
                  {renderValue(asset.noiseLevel ? `${asset.noiseLevel}/5` : '—', 'noiseLevel')}
                </div>
                <div className="flex justify-between text-right">
                  <span className="text-muted-foreground">מרחק מאנטנה:</span>
                  {renderValue(asset.antennaDistanceM ? `${asset.antennaDistanceM} מ׳` : '—', 'antennaDistanceM')}
                </div>
                <div className="flex justify-between text-right">
                  <span className="text-muted-foreground">מרחק ממקלט:</span>
                  {renderValue(asset.shelterDistanceM ? `${asset.shelterDistanceM} מ׳` : '—', 'shelterDistanceM')}
                </div>
                
                {/* Environmental Features */}
                <div className="flex justify-between text-right">
                  <span className="text-muted-foreground">שטחים ירוקים:</span>
                  {renderValue(asset.greenWithin300m ? 'כן' : 'לא', 'greenWithin300m')}
                </div>
                <div className="flex justify-between text-right">
                  <span className="text-muted-foreground">תחבורה ציבורית:</span>
                  {renderValue(asset.publicTransport ?? '—', 'publicTransport')}
                </div>
                <div className="flex justify-between text-right">
                  <span className="text-muted-foreground">מבני ציבור:</span>
                  {renderValue(asset.publicBuildings ?? '—', 'publicBuildings')}
                </div>
                <div className="flex justify-between text-right">
                  <span className="text-muted-foreground">מצב חניה:</span>
                  {renderValue(asset.parking ?? '—', 'parking')}
                </div>
                <div className="flex justify-between text-right">
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
                <div className="flex justify-between items-center rtl:flex-row-reverse">
                  <CardTitle>היתרים</CardTitle>
                  <Input
                    placeholder="חפש היתרים..."
                    value={permitsSearch}
                    onChange={(e) => setPermitsSearch(e.target.value)}
                    className="w-64"
                  />
                </div>
              </CardHeader>
            </Card>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <Card>
                <CardHeader>נתוני גוש חלקה</CardHeader>
                <CardBody className="space-y-2" dir="rtl">
                  {/* Parcel Information */}
                  <div className="flex justify-between text-right">
                    <span className="text-muted-foreground">שטח חלקה:</span>
                    {renderValue(asset.parcelArea ? `${asset.parcelArea.toLocaleString()} מ״ר` : '—', 'parcelArea')}
                  </div>
                  <div className="flex justify-between text-right">
                    <span className="text-muted-foreground">סטטוס חלקה:</span>
                    {renderValue(asset.parcelStatus, 'parcelStatus')}
                  </div>
                  
                  {/* Block Information */}
                  <div className="flex justify-between text-right">
                    <span className="text-muted-foreground">שטח גוש:</span>
                    {renderValue(asset.blockArea ? `${asset.blockArea.toLocaleString()} מ״ר` : '—', 'blockArea')}
                  </div>
                  <div className="flex justify-between text-right">
                    <span className="text-muted-foreground">מספר חלקות בגוש:</span>
                    {renderValue(asset.blockTotalParcels, 'blockTotalParcels')}
                  </div>
                  
                  {/* Permit Information */}
                  <div className="flex justify-between text-right">
                    <span className="text-muted-foreground">מספר היתרים:</span>
                    {renderValue(asset.totalPermits, 'totalPermits')}
                  </div>
                  <div className="flex justify-between text-right">
                    <span className="text-muted-foreground">מספר בקשה:</span>
                    {renderValue(asset.permitRequestNum, 'permitRequestNum')}
                  </div>
                  <div className="flex justify-between text-right">
                    <span className="text-muted-foreground">יחידות דיור:</span>
                    {renderValue(asset.permitHousingUnits, 'permitHousingUnits')}
                  </div>
                  <div className="flex justify-between text-right">
                    <span className="text-muted-foreground">שטח מגורים:</span>
                    {renderValue(asset.permitResidentialArea ? `${asset.permitResidentialArea.toLocaleString()} מ״ר` : '—', 'permitResidentialArea')}
                  </div>
                  <div className="flex justify-between text-right">
                    <span className="text-muted-foreground">שטח חניה:</span>
                    {renderValue(asset.permitParkingArea ? `${asset.permitParkingArea.toLocaleString()} מ״ר` : '—', 'permitParkingArea')}
                  </div>
                  <div className="flex justify-between text-right">
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
                    <div className="flex justify-between text-right">
                      <span className="text-muted-foreground">רבעון אחרון עם היתר:</span>
                      {renderValue(
                        <Badge variant={asset.lastPermitQ ? 'success' : 'neutral'}>
                          {asset.lastPermitQ ?? 'לא זמין'}
                        </Badge>,
                        'lastPermitQ'
                      )}
                    </div>
                    <div className="flex justify-between text-right">
                      <span className="text-muted-foreground">פעילות בנייה באזור:</span>
                      <span>{asset.lastPermitQ ? 'גבוהה' : 'נמוכה'}</span>
                    </div>
                  </div>
                  <div className="pt-2 border-t">
                    <div className="text-sm text-muted-foreground text-right">
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
                    <div className="flex justify-between text-right">
                      <span className="text-muted-foreground">היתר בתוקף:</span>
                      {renderValue(<Badge variant="success">כן</Badge>, 'permitValid')}
                    </div>
                    <div className="flex justify-between text-right">
                      <span className="text-muted-foreground">סוג היתר:</span>
                      {renderValue('מגורים', 'permitType')}
                    </div>
                    <div className="flex justify-between text-right">
                      <span className="text-muted-foreground">אישורי חיבור:</span>
                      {renderValue(<Badge variant="success">מאושר</Badge>, 'utilityApprovals')}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-right"> היתרים פעילים ברדיוס {permitRadius} מטר </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-right" dir="rtl">
                <div className="text-center py-4">
                  <div className="text-2xl font-bold">{permits.length}</div>
                  <div className="text-muted-foreground">בקשות היתר פעילות</div>
                </div>
                {permits.length > 0 && (
                  <div className="grid gap-3 md:grid-cols-1 lg:grid-cols-2 text-right">
                    {permits
                      .filter((p: any) => {
                        if (!permitsSearch) return true
                        const searchLower = permitsSearch.toLowerCase()
                        return (
                          p.title?.toLowerCase().includes(searchLower) ||
                          p.status?.toLowerCase().includes(searchLower) ||
                          p.meta?.permit_number?.toLowerCase().includes(searchLower) ||
                          p.meta?.tochen_bakasha?.toLowerCase().includes(searchLower) ||
                          p.meta?.request_num?.toLowerCase().includes(searchLower) ||
                          p.meta?.addresses?.toLowerCase().includes(searchLower) ||
                          p.meta?.building_stage?.toLowerCase().includes(searchLower)
                        )
                      })
                      .map((p: any) => (
                      <div key={p.external_id || p.meta.request_num} className="p-4 border rounded-lg text-right space-y-3">
                        {/* Header with permit type/description */}
                        <div className="flex justify-between items-start rtl:flex-row-reverse">
                          <div className="flex-1">
                            <h4 className="font-medium text-sm">
                              {p.title || 'היתר בנייה'}
                            </h4>
                            {p.meta.addresses && (
                              <p className="text-xs text-muted-foreground mt-1">
                                {p.meta.addresses}
                              </p>
                            )}
                          </div>
                          {p.status && (
                            <Badge variant={
                              p.status.includes('בניה') ? 'success' :
                              p.status.includes('הריסה') ? 'warning' :
                              'neutral'
                            }>
                              {p.status}
                            </Badge>
                          )}
                        </div>

                        {/* Permit details grid */}
                        <div className="grid gap-2 text-xs">
                          {p.meta.permit_number && (
                            <div className="flex justify-between rtl:flex-row-reverse">
                              <span className="text-muted-foreground">מספר היתר:</span>
                              <span className="font-medium">{p.meta.permit_number}</span>
                            </div>
                          )}
                          {p.meta.tochen_bakasha && (
                            <div className="flex justify-between rtl:flex-row-reverse">
                              <span className="text-muted-foreground">תיאור:</span>
                              <span className="font-medium">{p.meta.tochen_bakasha}</span>
                            </div>
                          )}
                          {p.meta.request_num && (
                            <div className="flex justify-between rtl:flex-row-reverse">
                              <span className="text-muted-foreground">מספר בקשה:</span>
                              <span className="font-medium">{p.meta.request_num}</span>
                            </div>
                          )}
                          {p.meta.permission_date && (
                            <div className="flex justify-between rtl:flex-row-reverse">
                              <span className="text-muted-foreground">תאריך אישור:</span>
                              <span>
                                {new Date(p.meta.permission_date).toLocaleDateString('he-IL')}
                              </span>
                            </div>
                          )}
                          {p.meta.expiry_date && (
                            <div className="flex justify-between rtl:flex-row-reverse">
                              <span className="text-muted-foreground">תוקף:</span>
                              <span>
                                {new Date(p.meta.expiry_date).toLocaleDateString('he-IL')}
                              </span>
                            </div>
                          )}
                          {p.meta.open_request && (
                            <div className="flex justify-between rtl:flex-row-reverse">
                              <span className="text-muted-foreground">תאריך הנפקה:</span>
                              <span>
                                {new Date(p.meta.open_request).toLocaleDateString('he-IL')}
                              </span>
                            </div>
                          )}
                          {p.meta.building_stage && (
                            <div className="flex justify-between rtl:flex-row-reverse">
                              <span className="text-muted-foreground">סטטוס:</span>
                              <span>{p.meta.building_stage}</span>
                            </div>
                          )}
                        </div>

                        {/* Actions/Links */}
                        <div className="pt-2 border-t">
                          <div className="flex gap-2 justify-end">
                            {p.meta.url_hadmaya && (
                              <Button
                                variant="outline"
                                size="sm"
                                asChild
                                className="text-xs"
                              >
                                <a
                                  href={p.meta.url_hadmaya}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                חפש באתר העירייה
                                </a>
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* No permits state */}
                {permits.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <div className="text-sm">לא נמצאו היתרים פעילים ברדיוס {permitRadius} מטר</div>
                    <div className="text-xs mt-1">
                      ייתכן שיש היתרים ברדיוס רחב יותר או שהמידע טרם עודכן
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="transactions" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>עיסקאות השוואה</CardTitle>
              </CardHeader>
              <CardBody className="space-y-4">
                <div className="grid gap-4 md:grid-cols-4">
                  <div className="text-center rtl:text-right">
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
                  <div className="text-center rtl:text-right">
                    <div className="text-2xl font-bold">
                      {marketAnalysis?.avg_price_per_sqm !== null && marketAnalysis?.avg_price_per_sqm !== undefined
                        ? formatCurrency(marketAnalysis?.avg_price_per_sqm)
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">ממוצע מחיר למ״ר</div>
                  </div>
                  <div className="text-center rtl:text-right">
                    <div className="text-2xl font-bold">
                      {marketAnalysis?.min_price_per_sqm !== null && marketAnalysis?.max_price_per_sqm !== null
                        ? `${formatCurrency(marketAnalysis?.min_price_per_sqm)} - ${formatCurrency(marketAnalysis?.max_price_per_sqm)}`
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">טווח מחיר למ״ר</div>
                  </div>
                  <div className="text-center rtl:text-right">
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
              data={comparableTransactions}
              loading={false}
              searchValue={transactionsSearch}
              onSearchChange={setTransactionsSearch}
              filters={{
                source: {
                  value: transactionsSourceFilter,
                  onChange: setTransactionsSourceFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'collected_government', label: 'ממשלתי' },
                    { value: 'internal', label: 'מאגר פנימי' }
                  ]
                },
                area: {
                  value: transactionsAreaFilter,
                  onChange: setTransactionsAreaFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: '0-50', label: '0-50 מ״ר' },
                    { value: '50-100', label: '50-100 מ״ר' },
                    { value: '100-150', label: '100-150 מ״ר' },
                    { value: '150-200', label: '150-200 מ״ר' },
                    { value: '200+', label: '200+ מ״ר' }
                  ]
                }
              }}
              onRefresh={() => {
                // Refresh transactions data
                fetch(`/api/assets/${id}/transactions`)
                  .then(res => {
                    if (!res.ok) throw new Error('Failed to load transactions')
                    return res.json()
                  })
                  .then(data => {
                    setComparableTransactions(data.transactions || [])
                  })
                  .catch(err => console.error('Error loading transactions:', err))
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
                  <div className="flex gap-2">
                    <Input
                      placeholder="חפש שומות..."
                      value={appraisalsSearch}
                      onChange={(e) => setAppraisalsSearch(e.target.value)}
                      className="w-64"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        // Refresh appraisal data
                        fetch(`/api/assets/${id}/appraisal`)
                          .then(res => res.json())
                          .then(data => {
                            setAppraisal(data.appraisal || null)
                            setDecisiveAppraisals(data.decisive_appraisals || [])
                            setRamiAppraisals(data.rami_appraisals || [])
                          })
                          .catch(err => console.error('Error refreshing appraisal:', err))
                        
                        // Refresh transaction data
                        fetch(`/api/assets/${id}/transactions`)
                          .then(res => res.json())
                          .then(data => {
                            setComparableTransactions(data.transactions || [])
                          })
                          .catch(err => console.error('Error refreshing transactions:', err))
                      }}
                    >
                      🔄 רענן מידע
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {appraisal ? (
                  <>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <h3 className="font-medium mb-2">הכרעות שמאי</h3>
                        <div className="space-y-2">
                          <div className="p-3 border rounded rtl:text-right">
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
                          <div className="p-3 border rounded rtl:text-right">
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
                          <div className="text-center rtl:text-right">
                            <div className="text-2xl font-bold">
                              {formatCurrency(appraisal.appraisedValue)}
                            </div>
                            <div className="text-sm text-muted-foreground">הכרעת שמאי</div>
                          </div>
                          <div className="text-center rtl:text-right">
                            <div className="text-2xl font-bold">
                              {formatCurrency(appraisal.marketValue)}
                            </div>
                            <div className="text-sm text-muted-foreground">שומת רמ״י</div>
                          </div>
                          <div className="text-center rtl:text-right">
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

                {/* Additional Appraisals Section */}
                {(decisiveAppraisals.length > 0 || ramiAppraisals.length > 0) && (
                  <div className="grid gap-4 md:grid-cols-2">
                    {decisiveAppraisals.length > 0 && (
                      <Card>
                        <CardHeader>
                          <CardTitle>כל השומות המכריעות</CardTitle>
                          <CardDescription>
                            {decisiveAppraisals.length} שומות נמצאו
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            {decisiveAppraisals
                              .filter((app: any) => {
                                if (!appraisalsSearch) return true
                                const searchLower = appraisalsSearch.toLowerCase()
                                return (
                                  app.appraiser?.toLowerCase().includes(searchLower) ||
                                  app.appraisedValue?.toString().includes(searchLower) ||
                                  app.date?.toLowerCase().includes(searchLower) ||
                                  app.source?.toLowerCase().includes(searchLower)
                                )
                              })
                              .map((app, idx) => (
                              <div key={idx} className="p-3 border rounded rtl:text-right">
                                <div className="font-medium">{app.appraiser}</div>
                                <div className="text-sm text-muted-foreground">
                                  {app.date && new Date(app.date).toLocaleDateString('he-IL')}
                                </div>
                                <div className="text-sm font-bold">{formatCurrency(app.appraisedValue)}</div>
                                {app.source && (
                                  <div className="text-xs text-blue-600 mt-1">
                                    מקור: {app.source === 'external_decisive' ? 'שומות מכריעות' : 'מאגר פנימי'}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {ramiAppraisals.length > 0 && (
                      <Card>
                        <CardHeader>
                          <CardTitle>תכניות רמ״י</CardTitle>
                          <CardDescription>
                            {ramiAppraisals.length} תכניות נמצאו
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            {ramiAppraisals
                              .filter((app: any) => {
                                if (!appraisalsSearch) return true
                                const searchLower = appraisalsSearch.toLowerCase()
                                return (
                                  app.plan_number?.toLowerCase().includes(searchLower) ||
                                  app.marketValue?.toString().includes(searchLower) ||
                                  app.date?.toLowerCase().includes(searchLower) ||
                                  app.status?.toLowerCase().includes(searchLower) ||
                                  app.source?.toLowerCase().includes(searchLower)
                                )
                              })
                              .map((app, idx) => (
                              <div key={idx} className="p-3 border rounded rtl:text-right">
                                <div className="font-medium">
                                  {app.plan_number ? `תכנית ${app.plan_number}` : 'תכנית רמ״י'}
                                </div>
                                <div className="text-sm text-muted-foreground">
                                  {app.date && new Date(app.date).toLocaleDateString('he-IL')}
                                </div>
                                <div className="text-sm font-bold">{formatCurrency(app.marketValue)}</div>
                                {app.status && (
                                  <div className="text-xs text-muted-foreground">סטטוס: {app.status}</div>
                                )}
                                {app.source && (
                                  <div className="text-xs text-blue-600 mt-1">
                                    מקור: {app.source === 'external_rami' ? 'רמ״י' : 'מאגר פנימי'}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                )}

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
                      onClick={loadDocumentsByCategory}
                      disabled={documentsLoading}
                    >
                      {documentsLoading ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin mr-2" />
                          טוען...
                        </>
                      ) : (
                        <>
                          <RefreshCw className="h-4 w-4 mr-2" />
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

                {/* Document Search and Filter */}
                <DocumentSearch
                  assetId={parseInt(id)}
                  onResultsChange={handleDocumentResults}
                  onLoadingChange={setDocumentsLoading}
                />

                {/* Error Display */}
                {documentsError && (
                  <div className="text-red-600 text-sm bg-red-50 p-3 rounded">
                    {documentsError}
                  </div>
                )}

                {/* Documents by Category */}
                {documentsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin mr-2" />
                    טוען מסמכים...
                  </div>
                ) : Object.keys(documentsByCategory).length > 0 ? (
                  <div className="space-y-6">
                    {Object.entries(documentsByCategory).map(([category, documents]: [string, any]) => (
                      <DocumentCategory
                        key={category}
                        category={category}
                        documents={documents}
                        onDocumentClick={(document) => {
                          if (document.file_url) {
                            window.open(document.file_url, '_blank')
                          } else if (document.external_url) {
                            window.open(document.external_url, '_blank')
                          }
                        }}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>אין מסמכים זמינים</p>
                    <p className="text-sm">העלה מסמכים או רענן את הנתונים</p>
                  </div>
                )}
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
                <CardTitle className="text-right">תרומות קהילה</CardTitle>
                <p className="text-sm text-muted-foreground text-right">
                  היסטוריית התרומות והעדכונים שנעשו על הנכס הזה על ידי חברי הקהילה
                </p>
              </CardHeader>
              <CardContent className="space-y-4 text-right">
                {/* Attribution Summary */}
                {asset.attribution && (
                  <div className="grid gap-3 lg:grid-cols-2">
                    {asset.attribution.created_by && (
                      <div className="p-3 border rounded-lg text-right">
                        <h3 className="font-medium mb-2 text-sm">יוצר הנכס</h3>
                        <div className="flex items-center gap-2 rtl:flex-row-reverse">
                          <div className="flex-1 text-right">
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
                      <div className="p-3 border rounded-lg text-right">
                        <h3 className="font-medium mb-2 text-sm">עודכן לאחרונה על ידי</h3>
                        <div className="flex items-center gap-2 rtl:flex-row-reverse">
                          <div className="flex-1 text-right">
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
                <div className="text-right">
                  <h3 className="font-medium mb-3 text-sm">תרומות אחרונות</h3>
                  {asset.recent_contributions && asset.recent_contributions.length > 0 ? (
                    <div className="space-y-2">
                      {asset.recent_contributions.map((contrib: any, idx: number) => (
                        <div key={idx} className="flex items-start gap-2 p-2 border rounded-lg rtl:flex-row-reverse">
                          <div className="flex-1 text-right">
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
                              <p className="text-xs text-right text-muted-foreground">{contrib.description}</p>
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
                  <div className="p-2 border rounded-lg text-center text-right">
                    <div className="text-lg font-bold text-primary">
                      {asset.recent_contributions?.length || 0}
                    </div>
                    <div className="text-xs text-muted-foreground">תרומות</div>
                  </div>
                  <div className="p-2 border rounded-lg text-center text-right">
                    <div className="text-lg font-bold text-primary">
                      {asset.attribution?.created_by ? 1 : 0}
                    </div>
                    <div className="text-xs text-muted-foreground">יוצר</div>
                  </div>
                  <div className="p-2 border rounded-lg text-center text-right">
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

