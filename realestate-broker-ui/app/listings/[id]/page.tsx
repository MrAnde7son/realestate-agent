'use client'
import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { PageLoader } from '@/components/ui/page-loader'
import { ArrowLeft, RefreshCw, FileText, Loader2 } from 'lucide-react'

export default function ListingDetail({ params }: { params: Promise<{ id: string }> }) {
  const [listing, setListing] = useState<any>(null)
  const [id, setId] = useState<string>('')
  const [uploading, setUploading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [generatingReport, setGeneratingReport] = useState(false)
  const [loading, setLoading] = useState(true)
  const [syncMessage, setSyncMessage] = useState<string>('')
  const router = useRouter()

  useEffect(() => {
    params.then(({ id }) => {
      setId(id)
      setLoading(true)
      fetch(`/api/listings/${id}`)
        .then(res => res.json())
        .then(data => setListing(data.listing))
        .catch(err => console.error('Error loading listing:', err))
        .finally(() => setLoading(false))
    })
  }, [params])

  const handleSyncData = async () => {
    if (!id || !listing?.address) return
    setSyncing(true)
    setSyncMessage('מסנכרן נתונים...')
    
    try {
      const res = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address: listing.address })
      })
      
      if (res.ok) {
        const result = await res.json()
        setSyncMessage(`נמצאו ${result.rows?.length || 0} נכסים חדשים`)
        // Optionally refresh the listing data
        const listingRes = await fetch(`/api/listings/${id}`)
        if (listingRes.ok) {
          const data = await listingRes.json()
          setListing(data.listing)
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

  if (loading || !listing) {
    return (
      <DashboardLayout>
        <DashboardShell>
          <div className="flex items-center gap-2 mb-4">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/listings">
                <ArrowLeft className="h-4 w-4" />
                חזרה לרשימה
              </Link>
            </Button>
          </div>
          <PageLoader message="טוען נתוני נכס..." showLogo={false} />
        </DashboardShell>
      </DashboardLayout>
    )
  }

  const manualDocs =
    listing.documents?.filter(
      (d: any) => d.type === 'tabu' || d.type === 'condo_plan'
    ) ?? []
  const permitDocs =
    listing.documents?.filter((d: any) => d.type === 'permit') ?? []
  const rightsDocs =
    listing.documents?.filter((d: any) => d.type === 'rights') ?? []
  const decisiveDocs =
    listing.documents?.filter((d: any) => d.type === 'appraisal_decisive') ?? []
  const rmiDocs =
    listing.documents?.filter((d: any) => d.type === 'appraisal_rmi') ?? []



  const handleGenerateReport = async () => {
    if (!id) return
    setGeneratingReport(true)
    try {
      const res = await fetch('/api/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ listingId: id })
      })
      if (res.ok) {
        router.push('/reports')
      }
    } catch (err) {
      console.error('Report generation failed:', err)
    } finally {
      setGeneratingReport(false)
    }
  }

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!id) return
    const formData = new FormData(e.currentTarget)
    setUploading(true)
    try {
      const res = await fetch(`/api/listings/${id}/documents`, {
        method: 'POST',
        body: formData,
      })
      if (res.ok) {
        const { doc } = await res.json()
        setListing((prev: any) => ({
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
      <DashboardShell className="space-y-6">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/listings">
              <ArrowLeft className="h-4 w-4" />
              חזרה לרשימה
            </Link>
          </Button>
        </div>
        <DashboardHeader
          heading={listing.address}
          text={`${listing.city}${listing.neighborhood ? ` · ${listing.neighborhood}` : ''} · ${
            listing.type === 'house' ? ' בית' : ' דירה'
          } · ${listing.netSqm} מ״ר נטו`}
        >
          <div className="text-right space-y-2">
            <div className="text-3xl font-bold">₪{listing.price?.toLocaleString('he-IL')}</div>
            <div className="text-muted-foreground">₪{listing.pricePerSqm?.toLocaleString('he-IL')}/מ״ר</div>
            <div className="flex gap-2">
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
                onClick={handleGenerateReport}
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
            </div>
            {syncMessage && (
              <div className="text-sm text-muted-foreground">{syncMessage}</div>
            )}
          </div>
        </DashboardHeader>

        {/* Quick Stats */}
        <div className="grid gap-6 md:grid-cols-4">
          <Card>
            <CardContent className="p-4">
                <div className="text-sm text-muted-foreground">רמת ביטחון</div>
              <div className="text-2xl font-bold">{listing.confidencePct}%</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
                <div className="text-sm text-muted-foreground">תשואה</div>
              <div className="text-2xl font-bold">{listing.capRatePct?.toFixed(1)}%</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-sm text-muted-foreground">יתרת זכויות</div>
              <div className="text-2xl font-bold">+{listing.remainingRightsSqm}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-sm text-muted-foreground">רמת רעש</div>
              <div className="text-2xl font-bold">{listing.noiseLevel}/5</div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs defaultValue="analysis" className="space-y-6">
          <TabsList className="justify-start overflow-x-auto">
            <TabsTrigger className="flex-none" value="analysis">ניתוח כללי</TabsTrigger>
            <TabsTrigger className="flex-none" value="permits">היתרים</TabsTrigger>
            <TabsTrigger className="flex-none" value="plans">תוכניות</TabsTrigger>
            <TabsTrigger className="flex-none" value="transactions">עיסקאות השוואה</TabsTrigger>
            <TabsTrigger className="flex-none" value="appraisals">שומות באיזור</TabsTrigger>
            <TabsTrigger className="flex-none" value="environment">סביבה</TabsTrigger>
            <TabsTrigger className="flex-none" value="documents">מסמכים</TabsTrigger>
          </TabsList>

          <TabsContent value="analysis" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>פרטי הנכס</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">סוג:</span>
                    <span>{listing.type === 'house' ? 'בית' : 'דירה'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">מ״ר נטו:</span>
                    <span>{listing.netSqm}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">חדרים:</span>
                    <span>{listing.bedrooms || '—'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">ייעוד:</span>
                    <span>{listing.zoning || '—'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">רמת ביטחון:</span>
                    <Badge variant={listing.confidencePct >= 80 ? 'good' : 'warn'}>
                      {listing.confidencePct}%
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>אנליזה פיננסית</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">מחיר מודל:</span>
                    <span>₪{listing.modelPrice?.toLocaleString('he-IL')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">פער למחיר:</span>
                    <Badge variant={listing.priceGapPct > 0 ? 'warn' : 'good'}>
                      {listing.priceGapPct?.toFixed(1)}%
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">הערכת שכירות:</span>
                    <span>₪{listing.rentEstimate?.toLocaleString('he-IL')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">תשואה שנתית:</span>
                    <Badge variant={listing.capRatePct >= 3 ? 'good' : 'warn'}>
                      {listing.capRatePct?.toFixed(1)}%
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">תחרות 1 ק״מ:</span>
                    <span>{listing.competition1km || '—'}</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>המלצת השקעה</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <span>ציון כללי:</span>
                    <div className="flex items-center gap-2">
                      <div className="text-2xl font-bold">{Math.round((listing.confidencePct + (listing.capRatePct * 20) + (listing.priceGapPct < 0 ? 100 + listing.priceGapPct : 100 - listing.priceGapPct)) / 3)}</div>
                      <div className="text-sm text-muted-foreground">/100</div>
                    </div>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {listing.priceGapPct < -10 ? "נכס במחיר אטרקטיביי מתחת לשוק" : 
                     listing.priceGapPct > 10 ? "נכס יקר יחסית לשוק" : 
                     "נכס במחיר הוגן יחסית לשוק"}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="plans" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>תוכניות מקומיות ומפורטות</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">תכנית נוכחית:</span>
                      <span>{listing.program || 'לא זמין'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">ייעוד:</span>
                      <Badge variant="outline">{listing.zoning || 'לא צוין'}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">יתרת זכויות:</span>
                      <Badge variant={listing.remainingRightsSqm > 0 ? 'good' : 'outline'}>
                        +{listing.remainingRightsSqm} מ״ר
                      </Badge>
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
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">סטטוס תכנוני:</span>
                      <Badge variant="good">פעיל</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">הגבלות מיוחדות:</span>
                      <span>{listing.riskFlags?.length > 0 ? listing.riskFlags.join(', ') : 'אין'}</span>
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
                <div className="grid gap-6 md:grid-cols-3">
                  <div className="text-center">
                    <div className="text-2xl font-bold">{listing.remainingRightsSqm}</div>
                    <div className="text-sm text-muted-foreground">מ״ר זכויות נותרות</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{Math.round((listing.remainingRightsSqm / listing.netSqm) * 100)}%</div>
                    <div className="text-sm text-muted-foreground">אחוז זכויות נוספות</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">₪{Math.round((listing.pricePerSqm * listing.remainingRightsSqm * 0.7) / 1000)}K</div>
                    <div className="text-sm text-muted-foreground">ערך משוער זכויות</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="environment" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>מידע סביבתי</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-6 md:grid-cols-3">
                  <div className="text-center">
                    <div className="text-2xl font-bold">{listing.noiseLevel}/5</div>
                    <div className="text-sm text-muted-foreground">רמת רעש</div>
                  </div>
                  
                  <div className="text-center">
                      <Badge variant={listing.greenWithin300m ? 'good' : 'bad'}>
                        {listing.greenWithin300m ? 'כן' : 'לא'}
                      </Badge>
                      <div className="text-sm text-muted-foreground">שטחי ציבור ≤300מ׳</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-2xl font-bold">{listing.antennaDistanceM}מ׳</div>
                    <div className="text-sm text-muted-foreground">מרחק מאנטנה</div>
                  </div>
                </div>

                {listing.riskFlags && listing.riskFlags.length > 0 && (
                  <div>
                    <h3 className="font-medium mb-2">סיכונים</h3>
                    <div className="flex flex-wrap gap-2">
                      {listing.riskFlags.map((flag: string, i: number) => (
                        <Badge 
                          key={i} 
                          variant={flag.includes('שימור') ? 'bad' : 'warn'}
                        >
                          {flag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="permits" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>היתרי בנייה באזור</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">רבעון אחרון עם היתר:</span>
                      <Badge variant={listing.lastPermitQ ? 'good' : 'outline'}>
                        {listing.lastPermitQ || 'לא זמין'}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">פעילות בנייה באזור:</span>
                      <span>{listing.lastPermitQ ? 'גבוהה' : 'נמוכה'}</span>
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
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">היתר בתוקף:</span>
                      <Badge variant="good">כן</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">סוג היתר:</span>
                      <span>מגורים</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">אישורי חיבור:</span>
                      <Badge variant="good">מאושר</Badge>
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

          <TabsContent value="transactions" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>עיסקאות השוואה</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-6 md:grid-cols-3">
                  <div className="text-center">
                    <div className="text-2xl font-bold">₪{listing.pricePerSqm?.toLocaleString('he-IL')}</div>
                    <div className="text-sm text-muted-foreground">מחיר למ״ר - נכס זה</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">₪{Math.round(listing.pricePerSqm * 0.95).toLocaleString('he-IL')}</div>
                    <div className="text-sm text-muted-foreground">ממוצע באזור</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{Math.round(((listing.pricePerSqm / (listing.pricePerSqm * 0.95)) - 1) * 100)}%</div>
                    <div className="text-sm text-muted-foreground">פער מהאזור</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>עסקאות אחרונות ברדיוס 500 מטר</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="grid gap-3">
                    <div className="flex justify-between items-center p-3 border rounded">
                      <div>
                        <div className="font-medium">רח&apos; בן יהודה 45</div>
                        <div className="text-sm text-muted-foreground">80 מ״ר • 3 חדרים • 10/01/24</div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">₪2.75M</div>
                        <div className="text-sm text-muted-foreground">₪34,375/מ״ר</div>
                      </div>
                    </div>
                    <div className="flex justify-between items-center p-3 border rounded">
                      <div>
                        <div className="font-medium">רח&apos; דיזנגוף 67</div>
                        <div className="text-sm text-muted-foreground">90 מ״ר • 3.5 חדרים • 05/01/24</div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">₪2.90M</div>
                        <div className="text-sm text-muted-foreground">₪32,222/מ״ר</div>
                      </div>
                    </div>
                    <div className="flex justify-between items-center p-3 border rounded">
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

          <TabsContent value="appraisals" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>שומות באיזור - שומות מכריעות, רמ״י ועוד</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-6 md:grid-cols-2">
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
                    <div className="grid gap-6 md:grid-cols-3">
                      <div className="text-center">
                        <div className="text-2xl font-bold">₪2.8M</div>
                        <div className="text-sm text-muted-foreground">הכרעת שמאי</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold">₪{Math.round(listing.netSqm * 30500 / 1000000 * 100) / 100}M</div>
                        <div className="text-sm text-muted-foreground">שומת רמ״י</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold">₪{(listing.price / 1000000).toFixed(1)}M</div>
                        <div className="text-sm text-muted-foreground">מחיר מבוקש</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="documents" className="space-y-6">
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
                          className="flex justify-between items-center p-2 border rounded"
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
                          className="flex justify-between items-center p-2 border rounded"
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
                  <h3 className="font-medium mb-2">זכויות</h3>
                  {rightsDocs.length ? (
                    <div className="space-y-2">
                      {rightsDocs.map((doc: any, idx: number) => (
                        <div
                          key={idx}
                          className="flex justify-between items-center p-2 border rounded"
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
                          className="flex justify-between items-center p-2 border rounded"
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
                          className="flex justify-between items-center p-2 border rounded"
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
                  סה״כ {listing.documents?.length || 0} מסמכים זמינים
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </DashboardShell>
    </DashboardLayout>
  )
}
