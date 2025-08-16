'use client'
import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { ArrowLeft } from 'lucide-react'

export default function ListingDetail({ params }: { params: Promise<{ id: string }> }) {
  const [listing, setListing] = useState<any>(null)
  const [id, setId] = useState<string>('')

  useEffect(() => {
    params.then(({ id }) => {
      setId(id)
      fetch(`/api/listings/${id}`)
        .then(res => res.json())
        .then(data => setListing(data.listing))
        .catch(err => console.error('Error loading listing:', err))
    })
  }, [])

  if (!listing) {
    return (
      <DashboardLayout>
        <div className="p-6">
          <div className="flex items-center space-x-2 mb-4">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/listings">
                <ArrowLeft className="h-4 w-4" />
                חזרה לרשימה
              </Link>
            </Button>
          </div>
          <div>טוען נתוני נכס...</div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/listings">
                <ArrowLeft className="h-4 w-4" />
                חזרה לרשימה
              </Link>
            </Button>
            <div>
              <h1 className="text-3xl font-bold">{listing.address}</h1>
              <p className="text-muted-foreground">
                {listing.city}{listing.neighborhood ? ` · ${listing.neighborhood}` : ''} · 
                {listing.type === 'house' ? ' בית' : ' דירה'} · {listing.netSqm} מ״ר נטו
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold">₪{listing.price?.toLocaleString('he-IL')}</div>
            <div className="text-muted-foreground">₪{listing.pricePerSqm?.toLocaleString('he-IL')}/מ״ר</div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <div className="text-sm text-muted-foreground">Confidence</div>
              <div className="text-2xl font-bold">{listing.confidencePct}%</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-sm text-muted-foreground">Cap Rate</div>
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
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList className="grid w-full grid-cols-7">
            <TabsTrigger value="overview">סקירה</TabsTrigger>
            <TabsTrigger value="planning">תכנון וזכויות</TabsTrigger>
            <TabsTrigger value="permits">היתרים</TabsTrigger>
            <TabsTrigger value="environment">סביבה</TabsTrigger>
            <TabsTrigger value="comps">עסקאות דומות</TabsTrigger>
            <TabsTrigger value="mortgage">משכנתא</TabsTrigger>
            <TabsTrigger value="docs">מסמכים</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
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
                    <span>{listing.beds || '—'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">זונינג:</span>
                    <span>{listing.zoning || '—'}</span>
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
                    <span className="text-muted-foreground">תחרות 1 ק״מ:</span>
                    <span>{listing.competition1km || '—'}</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="planning" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>מידע תכנוני</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h3 className="font-medium mb-2">זכויות בנייה</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">יתרת זכויות:</span>
                        <span>+{listing.remainingRightsSqm} מ״ר</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">תכנית:</span>
                        <span>{listing.program || 'לא זמין'}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-medium mb-2">סטטוס תכנוני</h3>
                    <div className="space-y-2">
                      <Badge variant="outline">{listing.zoning || 'לא צוין'}</Badge>
                      {listing.zoningCode && (
                        <div className="text-sm text-muted-foreground">
                          קוד: {listing.zoningCode}
                        </div>
                      )}
                    </div>
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
                    <div className="text-2xl font-bold">{listing.noiseLevel}/5</div>
                    <div className="text-sm text-muted-foreground">רמת רעש</div>
                  </div>
                  
                  <div className="text-center">
                    <Badge variant={listing.greenWithin300m ? 'good' : 'bad'}>
                      {listing.greenWithin300m ? 'כן' : 'לא'}
                    </Badge>
                    <div className="text-sm text-muted-foreground">ירוק ≤300מ׳</div>
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

          <TabsContent value="permits">
            <Card>
              <CardHeader>
                <CardTitle>היתרי בנייה</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <div className="text-2xl font-bold">{listing.lastPermitQ || 'לא זמין'}</div>
                  <div className="text-muted-foreground">רבעון אחרון עם היתר</div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="comps">
            <Card>
              <CardHeader>
                <CardTitle>עסקאות דומות</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-muted-foreground">
                  נתוני עסקאות יתווספו בקרוב
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="mortgage">
            <Card>
              <CardHeader>
                <CardTitle>חישוב משכנתא</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <Button asChild>
                    <Link href="/mortgage/analyze">
                      פתח אנליזת משכנתא מלאה
                    </Link>
                  </Button>
    </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="docs">
            <Card>
              <CardHeader>
                <CardTitle>מסמכים</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <div className="text-2xl font-bold">{listing.docsCount || 0}</div>
                  <div className="text-muted-foreground">מסמכים זמינים</div>
    </div>
              </CardContent>
            </Card>
          </TabsContent>
    </Tabs>
      </div>
    </DashboardLayout>
  )
}