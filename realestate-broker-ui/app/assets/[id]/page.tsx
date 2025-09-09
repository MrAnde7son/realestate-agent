'use client'
import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAnalytics } from '@/hooks/useAnalytics'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
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
import { useAuth } from '@/lib/auth-context'
import OnboardingProgress from '@/components/OnboardingProgress'
import { selectOnboardingState, getCompletionPct } from '@/onboarding/selectors'
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
  const router = useRouter()
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

  const handleSyncData = async () => {
    if (!id || !asset?.address) return
    setSyncing(true)
    setSyncMessage('מסנכרן נתונים...')
    
    try {
      const res = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address: asset.address })
      })
      
      if (res.ok) {
        const result = await res.json()
        setSyncMessage(`נמצאו ${result.rows?.length || 0} נכסים חדשים`)
        // Optionally refresh the asset data
        const assetRes = await fetch(`/api/assets/${id}`)
        if (assetRes.ok) {
          const data = await assetRes.json()
          setAsset(data.asset || data)
        }
        // Clear message after 5 seconds
        setTimeout(() => setSyncMessage(''), 5000)
      } else {
        setSyncMessage('שגיאה בסנכרון הנתונים')
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
    asset.documents?.filter(
      (d: any) => d.type === 'tabu' || d.type === 'condo_plan'
    ) ?? []
  const permitDocs =
    asset.documents?.filter((d: any) => d.type === 'permit') ?? []
  const rightsDocs =
    asset.documents?.filter((d: any) => d.type === 'rights') ?? []
  const decisiveDocs =
    asset.documents?.filter((d: any) => d.type === 'appraisal_decisive') ?? []
  const rmiDocs =
    asset.documents?.filter((d: any) => d.type === 'appraisal_rmi') ?? []

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
            <div>
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
              <div className="text-xs text-muted-foreground mt-2 space-y-1 rtl:text-right">
                {asset.attribution.created_by && (
                  <div className="rtl:flex rtl:flex-row-reverse rtl:justify-end">
                    <span className="font-medium">נוצר על ידי:</span> 
                    <span className="rtl:mr-1">{asset.attribution.created_by.name}</span>
                  </div>
                )}
                {asset.attribution.last_updated_by && asset.attribution.last_updated_by.id !== asset.attribution.created_by?.id && (
                  <div className="rtl:flex rtl:flex-row-reverse rtl:justify-end">
                    <span className="font-medium">עודכן לאחרונה על ידי:</span> 
                    <span className="rtl:mr-1">{asset.attribution.last_updated_by.name}</span>
                  </div>
                )}
                {asset.recent_contributions && asset.recent_contributions.length > 0 && (
                  <div className="rtl:flex rtl:flex-row-reverse rtl:justify-end">
                    <span className="font-medium">תרומות אחרונות:</span> 
                    <span className="rtl:mr-1">{asset.recent_contributions.length}</span>
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
              <div className="font-medium">{renderValue(asset.gush, 'gush')}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">חלקה</div>
              <div className="font-medium">{renderValue(asset.helka, 'helka')}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">תת חלקה</div>
              <div className="font-medium">{renderValue(asset.subhelka, 'subhelka')}</div>
            </div>
          </CardContent>
        </Card>

        {/* Main Content Tabs */}
        <Tabs defaultValue="analysis" className="space-y-4">
          <TabsList className="flex flex-wrap md:flex-nowrap">
            <TabsTrigger value="analysis">ניתוח כללי</TabsTrigger>
            <TabsTrigger value="permits">היתרים</TabsTrigger>
            <TabsTrigger value="plans">תוכניות</TabsTrigger>
            <TabsTrigger value="transactions">עיסקאות השוואה</TabsTrigger>
            <TabsTrigger value="appraisals">שומות באיזור</TabsTrigger>
            <TabsTrigger value="environment">סביבה</TabsTrigger>
            <TabsTrigger value="documents">מסמכים</TabsTrigger>
            <TabsTrigger value="contributions">תרומות קהילה</TabsTrigger>
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
                        {asset.confidencePct !== undefined && asset.confidencePct !== null &&
                        asset.capRatePct !== undefined && asset.capRatePct !== null &&
                        asset.priceGapPct !== undefined && asset.priceGapPct !== null
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
                        <Badge variant={asset.remainingRightsSqm !== undefined && asset.remainingRightsSqm !== null && asset.remainingRightsSqm > 0 ? 'success' : 'neutral'}>
                          {asset.remainingRightsSqm !== undefined && asset.remainingRightsSqm !== null ? `+${asset.remainingRightsSqm} מ״ר` : '—'}
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
                      {renderValue(<Badge variant="success">פעיל</Badge>, 'planActive')}
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
                      {asset.remainingRightsSqm !== undefined && asset.remainingRightsSqm !== null && asset.area !== undefined && asset.area !== null
                        ? `${Math.round((asset.remainingRightsSqm / asset.area) * 100)}%`
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">אחוז זכויות נוספות</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {asset.pricePerSqm !== undefined && asset.pricePerSqm !== null && asset.remainingRightsSqm !== undefined && asset.remainingRightsSqm !== null
                        ? `₪${Math.round((asset.pricePerSqm * asset.remainingRightsSqm * 0.7) / 1000)}K`
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">ערך משוער זכויות</div>
                  </div>
                </div>
              </CardContent>
            </Card>
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
                      {asset.noiseLevel !== undefined && asset.noiseLevel !== null ? `${asset.noiseLevel}/5` : '—'}
                      <DataBadge source={asset?._meta?.noiseLevel?.source} fetchedAt={asset?._meta?.noiseLevel?.fetched_at} />
                    </div>
                    <div className="text-sm text-muted-foreground">רמת רעש</div>
                  </div>

                  <div className="text-center">
                    <div className="text-2xl font-bold flex items-center justify-center gap-1">
                      {asset.greenWithin300m !== undefined && asset.greenWithin300m !== null ? (
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
                      {asset.antennaDistanceM !== undefined && asset.antennaDistanceM !== null ? `${asset.antennaDistanceM}מ׳` : '—'}
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
                <CardTitle>היתרים פעילים ברדיוס 50 מטר</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="text-center py-4">
                    <div className="text-2xl font-bold">3</div>
                    <div className="text-muted-foreground">בקשות היתר פעילות</div>
                  </div>
                  <div className="grid gap-2 md:grid-cols-2">
                    <div className="p-3 border rounded">
                      <div className="font-medium">רח&apos; הרצל 125</div>
                      <div className="text-sm text-muted-foreground">שיפוץ כללי • Q1/24</div>
                    </div>
                    <div className="p-3 border rounded">
                      <div className="font-medium">רח&apos; הרצל 121</div>
                      <div className="text-sm text-muted-foreground">הוספת יחידה • Q2/24</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="transactions" className="space-y-4">
            <Card>
              <CardHeader>עיסקאות השוואה</CardHeader>
              <CardBody className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="text-center">
                    <div className="text-2xl font-bold flex items-center justify-center gap-1">
                      {asset.pricePerSqm !== undefined && asset.pricePerSqm !== null
                        ? formatCurrency(asset.pricePerSqm)
                        : '—'}
                      <DataBadge source={asset?._meta?.pricePerSqm?.source} fetchedAt={asset?._meta?.pricePerSqm?.fetched_at} />
                    </div>
                    <div className="text-sm text-muted-foreground">מחיר למ״ר - נכס זה</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {asset.pricePerSqm !== undefined && asset.pricePerSqm !== null
                        ? formatCurrency(Math.round(asset.pricePerSqm * 0.95))
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">ממוצע באזור</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {asset.pricePerSqm !== undefined && asset.pricePerSqm !== null
                        ? `${Math.round(((asset.pricePerSqm / (asset.pricePerSqm * 0.95)) - 1) * 100)}%`
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
                    <div className="flex justify-between items-center p-3 border rounded rtl:flex-row-reverse">
                      <div>
                        <div className="font-medium">רח&apos; בן יהודה 45</div>
                        <div className="text-sm text-muted-foreground">80 מ״ר • 3 חדרים • 10/01/24</div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">₪2.75M</div>
                        <div className="text-sm text-muted-foreground">₪34,375/מ״ר</div>
                      </div>
                    </div>
                    <div className="flex justify-between items-center p-3 border rounded rtl:flex-row-reverse">
                      <div>
                        <div className="font-medium">רח&apos; דיזנגוף 67</div>
                        <div className="text-sm text-muted-foreground">90 מ״ר • 3.5 חדרים • 05/01/24</div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">₪2.90M</div>
                        <div className="text-sm text-muted-foreground">₪32,222/מ״ר</div>
                      </div>
                    </div>
                    <div className="flex justify-between items-center p-3 border rounded rtl:flex-row-reverse">
                      <div>
                        <div className="font-medium">רח&apos; הרצל 130</div>
                        <div className="text-sm text-muted-foreground">85 מ״ר • 3 חדרים • 28/12/23</div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">₪2.65M</div>
                        <div className="text-sm text-muted-foreground">₪31,176/מ״ר</div>
                      </div>
                    </div>
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
                <CardTitle>שומות באיזור - שומות מכריעות, רמ״י ועוד</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h3 className="font-medium mb-2">הכרעות שמאי</h3>
                    <div className="space-y-2">
                      <div className="p-3 border rounded">
                        <div className="font-medium">הכרעת שמאי מייעץ</div>
                        <div className="text-sm text-muted-foreground">
                          גוש 6638, חלקה 96 • 20/07/2025
                        </div>
                        <div className="text-sm">₪2.8M לדירת 85 מ״ר</div>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-medium mb-2">שומות רמ״י</h3>
                    <div className="space-y-2">
                      <div className="p-3 border rounded">
                        <div className="font-medium">שומת רמ״י מעודכנת</div>
                        <div className="text-sm text-muted-foreground">Q4/2024</div>
                        <div className="text-sm">₪30,500/מ״ר</div>
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
                      <div className="text-center">
                        <div className="text-2xl font-bold">₪2.8M</div>
                        <div className="text-sm text-muted-foreground">הכרעת שמאי</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold">
                          {asset.area !== undefined && asset.area !== null
                            ? `₪${Math.round(asset.area * 30500 / 1000000 * 100) / 100}M`
                            : '—'}
                        </div>
                        <div className="text-sm text-muted-foreground">שומת רמ״י</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold">
                          {asset.price !== undefined && asset.price !== null
                            ? `₪${(asset.price / 1000000).toFixed(1)}M`
                            : '—'}
                        </div>
                        <div className="text-sm text-muted-foreground">מחיר מבוקש</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
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
                          <span>{doc.name}</span>
                          <Button variant="outline" size="sm" asChild>
                            <a href={doc.url} download>
                              הורד
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
                          <span>{doc.name}</span>
                          <Button variant="outline" size="sm" asChild>
                            <a href={doc.url} download>
                              הורד
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
                          <span>{doc.name}</span>
                          <Button variant="outline" size="sm" asChild>
                            <a href={doc.url} download>
                              הורד
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
                          <span>{doc.name}</span>
                          <Button variant="outline" size="sm" asChild>
                            <a href={doc.url} download>
                              הורד
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
                          <span>{doc.name}</span>
                          <Button variant="outline" size="sm" asChild>
                            <a href={doc.url} download>
                              הורד
                            </a>
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">אין שומות</div>
                  )}
                </div>

                <div className="pt-4 text-center text-sm text-muted-foreground">
                  סה״כ {asset.documents?.length ?? 0} מסמכים זמינים
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="contributions" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>תרומות קהילה</CardTitle>
                <p className="text-sm text-muted-foreground">
                  היסטוריית התרומות והעדכונים שנעשו על הנכס הזה על ידי חברי הקהילה
                </p>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Attribution Summary */}
                {asset.attribution && (
                  <div className="grid gap-4 md:grid-cols-2">
                    {asset.attribution.created_by && (
                      <div className="p-4 border rounded-lg">
                        <h3 className="font-medium mb-2 rtl:text-right">יוצר הנכס</h3>
                        <div className="flex items-center space-x-2 rtl:space-x-reverse rtl:flex-row-reverse">
                          <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                            <span className="text-sm font-medium">
                              {asset.attribution.created_by.name.charAt(0).toUpperCase()}
                            </span>
                          </div>
                          <div className="rtl:text-right flex-1 min-w-0">
                            <p className="font-medium truncate">{asset.attribution.created_by.name}</p>
                            <p className="text-sm text-muted-foreground truncate">{asset.attribution.created_by.email}</p>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {asset.attribution.last_updated_by && asset.attribution.last_updated_by.id !== asset.attribution.created_by?.id && (
                      <div className="p-4 border rounded-lg">
                        <h3 className="font-medium mb-2 rtl:text-right">עודכן לאחרונה על ידי</h3>
                        <div className="flex items-center space-x-2 rtl:space-x-reverse rtl:flex-row-reverse">
                          <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                            <span className="text-sm font-medium">
                              {asset.attribution.last_updated_by.name.charAt(0).toUpperCase()}
                            </span>
                          </div>
                          <div className="rtl:text-right flex-1 min-w-0">
                            <p className="font-medium truncate">{asset.attribution.last_updated_by.name}</p>
                            <p className="text-sm text-muted-foreground truncate">{asset.attribution.last_updated_by.email}</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Recent Contributions */}
                <div>
                  <h3 className="font-medium mb-4">תרומות אחרונות</h3>
                  {asset.recent_contributions && asset.recent_contributions.length > 0 ? (
                    <div className="space-y-3">
                      {asset.recent_contributions.map((contrib: any, idx: number) => (
                        <div key={idx} className="flex items-start space-x-3 rtl:space-x-reverse p-3 border rounded-lg rtl:flex-row-reverse">
                          <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                            <span className="text-sm font-medium">
                              {contrib.user.name.charAt(0).toUpperCase()}
                            </span>
                          </div>
                          <div className="flex-1 min-w-0 rtl:text-right">
                            <div className="flex items-center justify-between rtl:flex-row-reverse">
                              <p className="font-medium text-sm">{contrib.user.name}</p>
                              <span className="text-xs text-muted-foreground">
                                {new Date(contrib.created_at).toLocaleDateString('he-IL')}
                              </span>
                            </div>
                            <p className="text-sm text-muted-foreground mb-1">
                              {getContributionTypeDisplay(contrib.type)}
                              {contrib.field_name && ` - ${contrib.field_name}`}
                            </p>
                            {contrib.description && (
                              <p className="text-sm">{contrib.description}</p>
                            )}
                            {contrib.source && (
                              <span className="inline-block px-2 py-1 text-xs bg-secondary rounded-full mt-1">
                                {getSourceDisplay(contrib.source)}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <p>אין תרומות זמינות</p>
                      <p className="text-sm">היה הראשון לתרום מידע על הנכס הזה!</p>
                    </div>
                  )}
                </div>

                {/* Community Stats */}
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="p-4 border rounded-lg text-center rtl:text-right">
                    <div className="text-2xl font-bold text-primary">
                      {asset.recent_contributions?.length || 0}
                    </div>
                    <div className="text-sm text-muted-foreground">תרומות</div>
                  </div>
                  <div className="p-4 border rounded-lg text-center rtl:text-right">
                    <div className="text-2xl font-bold text-primary">
                      {asset.attribution?.created_by ? 1 : 0}
                    </div>
                    <div className="text-sm text-muted-foreground">יוצר</div>
                  </div>
                  <div className="p-4 border rounded-lg text-center rtl:text-right">
                    <div className="text-2xl font-bold text-primary">
                      {new Set(asset.recent_contributions?.map((c: any) => c.user.id) || []).size}
                    </div>
                    <div className="text-sm text-muted-foreground">תורמים</div>
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
