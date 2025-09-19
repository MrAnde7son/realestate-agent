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
import DataBadge from '@/components/DataBadge'
import * as Tooltip from '@radix-ui/react-tooltip'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { PageLoader } from '@/components/ui/page-loader'
import { ArrowLeft, RefreshCw, FileText, Loader2, Home, Building } from 'lucide-react'
import ImageGallery from '@/components/ImageGallery'
import { useAuth } from '@/lib/auth-context'
import OnboardingProgress from '@/components/OnboardingProgress'
import { selectOnboardingState, getCompletionPct } from '@/onboarding/selectors'
import { AssetLeadsPanel } from '@/components/crm/asset-leads-panel'
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
  const [permits, setPermits] = useState<any[]>([])
  const [plans, setPlans] = useState<{local: any[], mavat: any[]}>({local: [], mavat: []})
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
  const router = useRouter()
  const searchParams = useSearchParams()
  const { id } = params
  const { user, isAuthenticated } = useAuth()
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

  const formatPercent = (value?: number, digits = 0) =>
    value !== undefined && value !== null
      ? `${value.toFixed(digits)}%`
      : null

  const avgCompPricePerSqm = comparables.length
    ? Math.round(
        comparables.reduce(
          (sum, c) => sum + (c.pricePerSqm || 0),
          0
        ) / comparables.length
      )
    : null

  const permitRadius = asset?._meta?.radius ?? 50

  useEffect(() => {
    setLoading(true)
    fetch(`/api/assets/${id}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to load asset')
        return res.json()
      })
      .then(data => setAsset(data.asset || data))
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
        setComparableTransactions(data.comparable_transactions || [])
      })
      .catch(err => console.error('Error loading appraisal:', err))
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
      .then(data => setPlans(data.plans || {local: [], mavat: []}))
      .catch(err => console.error('Error loading plans:', err))
  }, [id])

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
    if (tabFromUrl && ['analysis', 'permits', 'plans', 'transactions', 'appraisals', 'environment', 'documents', 'contributions'].includes(tabFromUrl)) {
      setActiveTab(tabFromUrl)
    }
  }, [searchParams])

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
      const res = await fetch(`/api/assets/${id}/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address: asset.address })
      })
      
      if (res.ok) {
        const result = await res.json()
        setSyncMessage(result.message || 'סנכרון נתונים התחיל בהצלחה')
        
        // Refresh the asset data after a short delay to show updated status
        setTimeout(async () => {
          const assetRes = await fetch(`/api/assets/${id}`)
          if (assetRes.ok) {
            const data = await assetRes.json()
            setAsset(data.asset || data)
          }
        }, 2000)
        
        // Clear message after 10 seconds
        setTimeout(() => setSyncMessage(''), 10000)
      } else {
        const errorData = await res.json().catch(() => ({}))
        setSyncMessage(errorData.error || 'שגיאה בסנכרון הנתונים')
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
    setUploading(true)
    try {
      const res = await fetch(`/api/assets/${id}/documents`, {
        method: 'POST',
        body: formData,
      })
      if (res.ok) {
        const { doc } = await res.json()
        setAsset((prev: any) => ({
          ...prev,
          documents: [...(prev.documents || []), doc],
        }))
        e.currentTarget.reset()
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
            <TabsTrigger value="permits">היתרים</TabsTrigger>
            <TabsTrigger value="plans">תוכניות</TabsTrigger>
            <TabsTrigger value="transactions">עיסקאות השוואה</TabsTrigger>
            <TabsTrigger value="appraisals">שומות באיזור</TabsTrigger>
            <TabsTrigger value="environment">סביבה</TabsTrigger>
            <TabsTrigger value="documents">מסמכים</TabsTrigger>
            <TabsTrigger value="crm">לקוחות</TabsTrigger>
            <TabsTrigger value="listings">מודעות</TabsTrigger>
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
                    <span>{asset.bedrooms ?? '—'}</span>
                  </div>
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">ייעוד:</span>
                    <span>{asset.zoning ?? '—'}</span>
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
                      <span className="text-muted-foreground">יתרת זכויות:</span>
                      {renderValue(
                        <Badge variant={!!asset.remainingRightsSqm && asset.remainingRightsSqm > 0 ? 'success' : 'neutral'}>
                          {!!asset.remainingRightsSqm ? `+${asset.remainingRightsSqm} מ״ר` : '—'}
                        </Badge>,
                        'remainingRightsSqm'
                      )}
                    </div>
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">זכויות בנייה עיקריות:</span>
                      {renderValue(asset.mainRightsSqm ? `${asset.mainRightsSqm} מ״ר` : 'לא זמין', 'mainRightsSqm')}
                    </div>
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">שטחי שירות:</span>
                      {renderValue(asset.serviceRightsSqm ? `${asset.serviceRightsSqm} מ״ר` : 'לא זמין', 'serviceRightsSqm')}
                    </div>
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">זכויות משלימות:</span>
                      {renderValue(asset.additionalPlanRights ?? 'אין', 'additionalPlanRights')}
                    </div>
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">מגבלות/חובות ציבוריות:</span>
                      {renderValue(asset.publicObligations ?? 'אין', 'publicObligations')}
                    </div>
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">סטטוס תוכנית:</span>
                      {renderValue(asset.planStatus ?? 'לא ידוע', 'planStatus')}
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

            <Card>
              <CardHeader>
                <CardTitle>זכויות בנייה מפורטות</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="text-center">
                    <div className="text-2xl font-bold">{formatNumber(asset.remainingRightsSqm) ?? '—'}</div>
                    <div className="text-sm text-muted-foreground">מ״ר זכויות נותרות</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {!!asset.remainingRightsSqm && !!asset.area
                        ? `${Math.round((asset.remainingRightsSqm / asset.area) * 100)}%`
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">אחוז זכויות נוספות</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {!!asset.pricePerSqm && !!asset.remainingRightsSqm
                        ? `₪${Math.round((asset.pricePerSqm * asset.remainingRightsSqm * 0.7) / 1000)}K`
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">ערך משוער זכויות</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Mavat Plans */}
            {plans.mavat && plans.mavat.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>תוכניות מ-mavat</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    תוכניות תכנון רלוונטיות מהמערכת הממשלתית
                  </p>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {plans.mavat.map((plan: any, idx: number) => (
                      <div key={idx} className="p-3 border rounded-lg">
                        <div className="flex justify-between items-start rtl:flex-row-reverse mb-2">
                          <div className="flex-1">
                            <h4 className="font-medium text-sm">{plan.title}</h4>
                            <p className="text-xs text-muted-foreground">
                              תוכנית מס׳ {plan.plan_id}
                            </p>
                          </div>
                          <Badge variant={plan.status === 'מאושר' ? 'success' : 'neutral'}>
                            {plan.status}
                          </Badge>
                        </div>
                        <div className="grid gap-2 text-xs text-muted-foreground">
                          {plan.authority && (
                            <div className="flex justify-between rtl:flex-row-reverse">
                              <span>רשות:</span>
                              <span>{plan.authority}</span>
                            </div>
                          )}
                          {plan.jurisdiction && (
                            <div className="flex justify-between rtl:flex-row-reverse">
                              <span>תחום שיפוט:</span>
                              <span>{plan.jurisdiction}</span>
                            </div>
                          )}
                          {plan.approval_date && (
                            <div className="flex justify-between rtl:flex-row-reverse">
                              <span>תאריך אישור:</span>
                              <span>{new Date(plan.approval_date).toLocaleDateString('he-IL')}</span>
                            </div>
                          )}
                          {plan.status_date && (
                            <div className="flex justify-between rtl:flex-row-reverse">
                              <span>תאריך סטטוס:</span>
                              <span>{new Date(plan.status_date).toLocaleDateString('he-IL')}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="pt-2 border-t mt-4">
                    <div className="text-sm text-muted-foreground text-center">
                      מקור: מערכת mavat - מידע תכנוני ממשלתי
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Local Plans */}
            {plans.local && plans.local.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>תוכניות מקומיות</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    תוכניות שמורות במערכת המקומית
                  </p>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {plans.local.map((plan: any, idx: number) => (
                      <div key={idx} className="p-3 border rounded-lg">
                        <div className="flex justify-between items-start rtl:flex-row-reverse mb-2">
                          <div className="flex-1">
                            <h4 className="font-medium text-sm">{plan.description || plan.plan_number}</h4>
                            <p className="text-xs text-muted-foreground">
                              תוכנית מס׳ {plan.plan_number}
                            </p>
                          </div>
                          <Badge variant={plan.status === 'מאושר' ? 'success' : 'neutral'}>
                            {plan.status}
                          </Badge>
                        </div>
                        {plan.effective_date && (
                          <div className="text-xs text-muted-foreground">
                            <span>תאריך תוקף: </span>
                            <span>{new Date(plan.effective_date).toLocaleDateString('he-IL')}</span>
                          </div>
                        )}
                        {plan.file_url && (
                          <div className="mt-2">
                            <a 
                              href={plan.file_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-blue-500 text-xs underline"
                            >
                              צפה במסמך
                            </a>
                          </div>
                        )}
                      </div>
                    ))}
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
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="text-center">
                    <div className="text-2xl font-bold flex items-center justify-center gap-1">
                      {!!asset.noiseLevel ? `${asset.noiseLevel}/5` : '—'}
                      <DataBadge source={asset?._meta?.noiseLevel?.source} fetchedAt={asset?._meta?.noiseLevel?.fetched_at} />
                    </div>
                    <div className="text-sm text-muted-foreground">רמת רעש</div>
                  </div>

                  <div className="text-center">
                    <div className="text-2xl font-bold flex items-center justify-center gap-1">
                      {!!asset.greenWithin300m ? (
                        <>
                          <Badge variant={asset.greenWithin300m ? 'success' : 'error'}>
                            {asset.greenWithin300m ? 'כן' : 'לא'}
                          </Badge>
                          <DataBadge
                            source={asset?._meta?.greenWithin300m?.source}
                            fetchedAt={asset?._meta?.greenWithin300m?.fetched_at}
                          />
                        </>
                      ) : (
                        '—'
                      )}
                    </div>
                    <div className="text-sm text-muted-foreground">שטחי ציבור ≤300מ׳</div>
                  </div>

                  <div className="text-center">
                    <div className="text-2xl font-bold flex items-center justify-center gap-1">
                      {!!asset.antennaDistanceM ? `${asset.antennaDistanceM}מ׳` : '—'}
                      <DataBadge source={asset?._meta?.antennaDistanceM?.source} fetchedAt={asset?._meta?.antennaDistanceM?.fetched_at} />
                    </div>
                    <div className="text-sm text-muted-foreground">מרחק מאנטנה</div>
                  </div>
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

            <Card>
              <CardHeader>
                <CardTitle>סביבת הנכס</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between rtl:flex-row-reverse">
                  <span className="text-muted-foreground">תחבורה ציבורית:</span>
                  {renderValue(asset.publicTransport ?? '—', 'publicTransport')}
                </div>
                <div className="flex justify-between rtl:flex-row-reverse">
                  <span className="text-muted-foreground">שטחים פתוחים בקרבת מקום:</span>
                  {renderValue(asset.openSpacesNearby ?? '—', 'openSpacesNearby')}
                </div>
                <div className="flex justify-between rtl:flex-row-reverse">
                  <span className="text-muted-foreground">מבני ציבור:</span>
                  {renderValue(asset.publicBuildings ?? '—', 'publicBuildings')}
                </div>
                <div className="flex justify-between rtl:flex-row-reverse">
                  <span className="text-muted-foreground">מצב חניה:</span>
                  {renderValue(asset.parking ?? '—', 'parking')}
                </div>
                <div className="flex justify-between rtl:flex-row-reverse">
                  <span className="text-muted-foreground">פרויקטים סמוכים:</span>
                  {renderValue(asset.nearbyProjects ?? '—', 'nearbyProjects')}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="permits" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <Card>
                <CardHeader>פרטי היתר</CardHeader>
                <CardBody className="space-y-2">
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">תאריך היתר:</span>
                    {renderValue(asset.permitDate, 'permitDate')}
                  </div>
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">סטטוס:</span>
                    {renderValue(asset.permitStatus, 'permitStatus')}
                  </div>
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">פירוט:</span>
                    {renderValue(asset.permitDetails, 'permitDetails')}
                  </div>
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">שטח עיקרי:</span>
                    {renderValue(asset.permitMainArea ? `${asset.permitMainArea} מ״ר` : '—', 'permitMainArea')}
                  </div>
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">שטחי שירות:</span>
                    {renderValue(asset.permitServiceArea ? `${asset.permitServiceArea} מ״ר` : '—', 'permitServiceArea')}
                  </div>
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">מבקש:</span>
                    {renderValue(asset.permitApplicant, 'permitApplicant')}
                  </div>
                  <div className="flex justify-between rtl:flex-row-reverse">
                    <span className="text-muted-foreground">מסמך:</span>
                    {renderValue(
                      asset.permitDocUrl ? (
                        <a href={asset.permitDocUrl} target="_blank" className="text-blue-500 underline">צפה</a>
                      ) : (
                        '—'
                      ),
                      'permitDocUrl'
                    )}
                  </div>
                </CardBody>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>היתרי בנייה באזור</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">רבעון אחרון עם היתר:</span>
                      {renderValue(
                        <Badge variant={asset.lastPermitQ ? 'success' : 'neutral'}>
                          {asset.lastPermitQ ?? 'לא זמין'}
                        </Badge>,
                        'lastPermitQ'
                      )}
                    </div>
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">פעילות בנייה באזור:</span>
                      <span>{asset.lastPermitQ ? 'גבוהה' : 'נמוכה'}</span>
                    </div>
                  </div>
                  <div className="pt-2 border-t">
                    <div className="text-sm text-muted-foreground">
                      נתונים מעודכנים ממערכת היתרי הבנייה של עיריית תל אביב
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>סטטוס היתרים</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">היתר בתוקף:</span>
                      {renderValue(<Badge variant="success">כן</Badge>, 'permitValid')}
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">סוג היתר:</span>
                      {renderValue('מגורים', 'permitType')}
                    </div>
                    <div className="flex justify-between rtl:flex-row-reverse">
                      <span className="text-muted-foreground">אישורי חיבור:</span>
                      {renderValue(<Badge variant="success">מאושר</Badge>, 'utilityApprovals')}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>היתרים פעילים ברדיוס {permitRadius} מטר</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="text-center py-4 rtl:text-right">
                    <div className="text-2xl font-bold">{permits.length}</div>
                    <div className="text-muted-foreground">בקשות היתר פעילות</div>
                  </div>
                  {permits.length > 0 && (
                    <div className="grid gap-2 md:grid-cols-2">
                      {permits.map((p: any) => (
                        <div key={p.id || p.permit_number} className="p-3 border rounded rtl:text-right">
                          <div className="font-medium">{p.description || p.permit_number || '—'}</div>
                          <div className="text-sm text-muted-foreground">{p.status || p.issued_date || ''}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="transactions" className="space-y-4">
            <Card>
              <CardHeader>עיסקאות השוואה</CardHeader>
              <CardBody className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
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
                      {avgCompPricePerSqm !== null
                        ? formatCurrency(avgCompPricePerSqm)
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">ממוצע באזור</div>
                  </div>
                  <div className="text-center rtl:text-right">
                    <div className="text-2xl font-bold">
                      {!!asset.pricePerSqm && !!avgCompPricePerSqm
                        ? `${Math.round(((asset.pricePerSqm / avgCompPricePerSqm) - 1) * 100)}%`
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">פער מהאזור</div>
                  </div>
                </div>
                </CardBody>
              </Card>

            <Card>
              <CardHeader>
                <CardTitle>עסקאות אחרונות ברדיוס 500 מטר</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="grid gap-3">
                    {comparables.map((comp: any, idx: number) => (
                      <div
                        key={idx}
                        className="flex justify-between items-center p-3 border rounded rtl:flex-row-reverse"
                      >
                        <div>
                          <div className="font-medium">{comp.address}</div>
                          <div className="text-sm text-muted-foreground">
                            {!!comp.area ? `${comp.area} מ״ר` : ''}
                            {comp.rooms ? ` • ${comp.rooms} חדרים` : ''}
                            {comp.date ? ` • ${new Date(comp.date).toLocaleDateString('he-IL')}` : ''}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold">{formatCurrency(comp.price)}</div>
                          <div className="text-sm text-muted-foreground">
                            {formatCurrency(comp.pricePerSqm)}/מ״ר
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="pt-2 border-t text-center">
                    <div className="text-sm text-muted-foreground">
                      מקור: נתוני עסקאות ממשרד השיכון ומ-data.gov.il
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
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
                      // Refresh appraisal data
                      fetch(`/api/assets/${id}/appraisal`)
                        .then(res => res.json())
                        .then(data => {
                          setAppraisal(data.appraisal || null)
                          setDecisiveAppraisals(data.decisive_appraisals || [])
                          setRamiAppraisals(data.rami_appraisals || [])
                          setComparableTransactions(data.comparable_transactions || [])
                        })
                        .catch(err => console.error('Error refreshing appraisal:', err))
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
                            {decisiveAppraisals.map((app, idx) => (
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
                            {ramiAppraisals.map((app, idx) => (
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

                {/* Comparable Transactions Section */}
                {comparableTransactions.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>עסקאות השוואה באזור</CardTitle>
                      <CardDescription>
                        {comparableTransactions.length} עסקאות נמצאו
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {comparableTransactions.map((trans, idx) => (
                          <div key={idx} className="flex justify-between items-center p-3 border rounded rtl:flex-row-reverse">
                            <div>
                              <div className="font-medium">{trans.address}</div>
                              <div className="text-sm text-muted-foreground">
                                {!!trans.area ? `${trans.area} מ״ר` : ''}
                                {trans.rooms ? ` • ${trans.rooms} חדרים` : ''}
                                {trans.date ? ` • ${new Date(trans.date).toLocaleDateString('he-IL')}` : ''}
                              </div>
                              {trans.source && (
                                <div className="text-xs text-blue-600 mt-1">
                                  מקור: {trans.source === 'external_nadlan' ? 'נדלן' : 'מאגר פנימי'}
                                </div>
                              )}
                            </div>
                            <div className="text-right">
                              <div className="font-bold">{formatCurrency(trans.price)}</div>
                              <div className="text-sm text-muted-foreground">
                                {formatCurrency(trans.price_per_sqm)}/מ״ר
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="documents" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>מסמכים</CardTitle>
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

                <div>
                  <h3 className="font-medium mb-2">מסמכים ידניים</h3>
                  {manualDocs.length ? (
                        <div className="space-y-2">
                          {manualDocs.map((doc: any, idx: number) => (
                            <div
                              key={idx}
                              className="flex justify-between items-center p-2 border rounded rtl:flex-row-reverse"
                            >
                              <span>{doc.name || doc.title}</span>
                              <Button variant="outline" size="sm" asChild>
                                <a 
                                  href={doc.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  onClick={(e) => {
                                    if (!doc.url || !doc.url.startsWith('http')) {
                                      e.preventDefault()
                                      alert('קישור לא זמין')
                                    }
                                  }}
                                >
                                  {doc.url && doc.url.startsWith('http') ? 'פתח' : 'לא זמין'}
                                </a>
                              </Button>
                            </div>
                          ))}
                        </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">
                      לא הועלו מסמכים
                    </div>
                  )}
                </div>

                <div>
                  <h3 className="font-medium mb-2">היתרים</h3>
                  {permitDocs.length ? (
                    <div className="space-y-2">
                      {permitDocs.map((doc: any, idx: number) => (
                        <div
                          key={idx}
                          className="flex justify-between items-center p-2 border rounded rtl:flex-row-reverse"
                        >
                          <span>{doc.name || doc.title}</span>
                          <Button variant="outline" size="sm" asChild>
                            <a 
                              href={doc.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              onClick={(e) => {
                                if (!doc.url || !doc.url.startsWith('http')) {
                                  e.preventDefault()
                                  alert('קישור לא זמין')
                                }
                              }}
                            >
                              {doc.url && doc.url.startsWith('http') ? 'פתח' : 'לא זמין'}
                            </a>
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">אין היתרים</div>
                  )}
                </div>

                <div>
                  <h3 className="font-medium mb-2">תוכניות</h3>
                  {rightsDocs.length ? (
                    <div className="space-y-2">
                      {rightsDocs.map((doc: any, idx: number) => (
                        <div
                          key={idx}
                          className="flex justify-between items-center p-2 border rounded rtl:flex-row-reverse"
                        >
                          <span>{doc.name || doc.title}</span>
                          <Button variant="outline" size="sm" asChild>
                            <a 
                              href={doc.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              onClick={(e) => {
                                if (!doc.url || !doc.url.startsWith('http')) {
                                  e.preventDefault()
                                  alert('קישור לא זמין')
                                }
                              }}
                            >
                              {doc.url && doc.url.startsWith('http') ? 'פתח' : 'לא זמין'}
                            </a>
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">אין זכויות</div>
                  )}
                </div>

                <div>
                  <h3 className="font-medium mb-2">שומות מכריעות</h3>
                  {decisiveDocs.length ? (
                    <div className="space-y-2">
                      {decisiveDocs.map((doc: any, idx: number) => (
                        <div
                          key={idx}
                          className="flex justify-between items-center p-2 border rounded rtl:flex-row-reverse"
                        >
                          <span>{doc.name || doc.title}</span>
                          <Button variant="outline" size="sm" asChild>
                            <a 
                              href={doc.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              onClick={(e) => {
                                if (!doc.url || !doc.url.startsWith('http')) {
                                  e.preventDefault()
                                  alert('קישור לא זמין')
                                }
                              }}
                            >
                              {doc.url && doc.url.startsWith('http') ? 'פתח' : 'לא זמין'}
                            </a>
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">אין שומות</div>
                  )}
                </div>

                <div>
                  <h3 className="font-medium mb-2">שומות רמ״י</h3>
                  {rmiDocs.length ? (
                    <div className="space-y-2">
                      {rmiDocs.map((doc: any, idx: number) => (
                        <div
                          key={idx}
                          className="flex justify-between items-center p-2 border rounded rtl:flex-row-reverse"
                        >
                          <span>{doc.name || doc.title}</span>
                          <Button variant="outline" size="sm" asChild>
                            <a 
                              href={doc.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              onClick={(e) => {
                                if (!doc.url || !doc.url.startsWith('http')) {
                                  e.preventDefault()
                                  alert('קישור לא זמין')
                                }
                              }}
                            >
                              {doc.url && doc.url.startsWith('http') ? 'פתח' : 'לא זמין'}
                            </a>
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">אין שומות</div>
                  )}
                </div>

                {/* Fallback section for uncategorized documents */}
                {(() => {
                  const categorizedTypes = ['tabu', 'condo_plan', 'contract', 'deed', 'other', 'permit', 'rights', 'plan', 'appraisal_decisive', 'appraisal_rmi', 'appraisal']
                  const uncategorizedDocs = asset?.documents?.filter((d: any) => !categorizedTypes.includes(d.type)) ?? []
                  
                  if (uncategorizedDocs.length > 0) {
                    return (
                      <div>
                        <h3 className="font-medium mb-2">מסמכים נוספים</h3>
                        <div className="space-y-2">
                          {uncategorizedDocs.map((doc: any, idx: number) => (
                            <div
                              key={idx}
                              className="flex justify-between items-center p-2 border rounded rtl:flex-row-reverse"
                            >
                              <div className="flex flex-col rtl:items-end">
                                <span>{doc.title || doc.name || `מסמך ${doc.type}`}</span>
                                {doc.type && (
                                  <span className="text-xs text-muted-foreground">סוג: {doc.type}</span>
                                )}
                              </div>
                              <Button variant="outline" size="sm" asChild>
                                <a 
                                  href={doc.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  onClick={(e) => {
                                    if (!doc.url || !doc.url.startsWith('http')) {
                                      e.preventDefault()
                                      alert('קישור לא זמין')
                                    }
                                  }}
                                >
                                  {doc.url && doc.url.startsWith('http') ? 'פתח' : 'לא זמין'}
                                </a>
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )
                  }
                  return null
                })()}

                <div className="pt-4 text-center text-sm text-muted-foreground">
                  סה״כ {asset.documents?.length ?? 0} מסמכים זמינים
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="crm" className="space-y-4">
            <AssetLeadsPanel 
              assetId={parseInt(id)} 
              assetAddress={asset.address}
            />
          </TabsContent>

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
