'use client'
import React, { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Link from 'next/link'
import { Listing } from '@/lib/data'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger, SheetFooter, SheetDescription } from '@/components/ui/sheet'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { fmtCurrency, fmtNumber } from '@/lib/utils'
import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'

export default function ListingsPage() {
  const [listings, setListings] = useState<Listing[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const { isAuthenticated } = useAuth()
  const router = useRouter()

  const handleProtectedAction = (action: string) => {
    if (!isAuthenticated) {
      router.push('/auth?redirect=' + encodeURIComponent(window.location.pathname))
    }
  }

  const newListingSchema = z.object({
    address: z.string().min(1, 'חובה להזין כתובת'),
  })
  type NewListing = z.infer<typeof newListingSchema>

  const form = useForm<NewListing>({
    resolver: zodResolver(newListingSchema),
    defaultValues: {
      address: '',
    },
  })

  useEffect(() => {
    fetch('/api/listings')
      .then(res => res.json())
      .then(data => {
        setListings(data.rows)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error loading listings:', err)
        setLoading(false)
      })
  }, [])

  const [search, setSearch] = useState('')
  const [city, setCity] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [priceMin, setPriceMin] = useState('')
  const [priceMax, setPriceMax] = useState('')

  const cityOptions = React.useMemo(
    () => Array.from(new Set(listings.map(l => l.city).filter(Boolean))) as string[],
    [listings]
  )
  const typeOptions = React.useMemo(
    () => Array.from(new Set(listings.map(l => l.type).filter(Boolean))) as string[],
    [listings]
  )

  const filteredListings = React.useMemo(
    () =>
      listings.filter(l => {
        if (
          search &&
          !`${l.address} ${l.city ?? ''} ${l.neighborhood ?? ''}`
            .toLowerCase()
            .includes(search.toLowerCase())
        )
          return false
        if (city && l.city !== city) return false
        if (typeFilter && l.type !== typeFilter) return false
        if (priceMin && l.price < Number(priceMin)) return false
        if (priceMax && l.price > Number(priceMax)) return false
        return true
      }),
    [listings, search, city, typeFilter, priceMin, priceMax]
  )

  if (loading) {
    return (
      <DashboardLayout>
        <div className="p-6">
          <h1 className="text-3xl font-bold">רשימת נכסים</h1>
          <p className="text-muted-foreground">טוען נתונים...</p>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        {/* Login Prompt for Guests */}
        {!isAuthenticated && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium text-blue-900">התחבר כדי להוסיף נכסים חדשים</h3>
                <p className="text-sm text-blue-700 mt-1">
                  צור חשבון או התחבר כדי להוסיף נכסים חדשים למערכת
                </p>
              </div>
              <Button onClick={() => router.push('/auth')} className="bg-blue-600 hover:bg-blue-700">
                התחבר עכשיו
              </Button>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">רשימת נכסים</h1>
            <p className="text-muted-foreground">
              {listings.length} נכסים עם נתוני שמאות ותכנון מלאים
            </p>
          </div>
        <div className="flex items-center space-x-2">
          {isAuthenticated ? (
            <Sheet open={open} onOpenChange={setOpen}>
              <SheetTrigger asChild>
                <Button variant="default">הוסף נכס</Button>
              </SheetTrigger>
              <SheetContent>
                <SheetHeader>
                  <SheetTitle>הוסף נכס חדש</SheetTitle>
                  <SheetDescription>
                    הזן כתובת והמערכת תאסוף אוטומטית מידע מיד 2, GIS, רמ״י וממשלה
                  </SheetDescription>
                </SheetHeader>
                <form
                  onSubmit={form.handleSubmit(async (values) => {
                    try {
                      // Show loading state
                      const submitButton = document.querySelector('button[type="submit"]') as HTMLButtonElement
                      if (submitButton) {
                        submitButton.disabled = true
                        submitButton.innerHTML = '<div class="flex items-center gap-2"><div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>אוסף מידע...</div>'
                      }

                      // Trigger backend sync for this address
                      const syncResponse = await fetch('/api/sync', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ address: values.address }),
                      })
                      
                      if (!syncResponse.ok) {
                        throw new Error('שגיאה באיסוף המידע מהמערכות החיצוניות')
                      }

                      const syncData = await syncResponse.json()
                      console.log('Collected data:', syncData)

                      // Create listing with collected data
                      const res = await fetch('/api/listings', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                          address: values.address,
                          ...syncData // Include all collected data
                        }),
                      })
                      
                      const data = await res.json()
                      if (res.ok) {
                        setListings((prev) => [...prev, data.listing])
                        form.reset()
                        setOpen(false)
                      } else {
                        throw new Error(data.error || 'שגיאה ביצירת הנכס')
                      }
                    } catch (error) {
                      console.error('Error adding listing:', error)
                      alert(`שגיאה: ${error instanceof Error ? error.message : 'שגיאה לא ידועה'}`)
                    } finally {
                      // Reset button state
                      const submitButton = document.querySelector('button[type="submit"]') as HTMLButtonElement
                      if (submitButton) {
                        submitButton.disabled = false
                        submitButton.innerHTML = 'שמור'
                      }
                    }
                  })}
                  className="space-y-4"
                >
                  <div className="space-y-2">
                    <Label htmlFor="address">כתובת הנכס</Label>
                    <Input 
                      id="address" 
                      placeholder="לדוגמה: הגולן 1, תל אביב"
                      {...form.register('address')} 
                    />
                    {form.formState.errors.address && (
                      <p className="text-sm text-destructive">
                        {form.formState.errors.address.message}
                      </p>
                    )}
                  </div>

                  {/* Info about automatic data collection */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="flex items-start gap-2">
                      <div className="w-5 h-5 bg-blue-100 rounded-full flex items-center justify-center mt-0.5">
                        <span className="text-blue-600 text-xs">ℹ</span>
                      </div>
                      <div className="text-sm text-blue-800">
                        <p className="font-medium mb-1">המערכת תאסוף אוטומטית:</p>
                        <ul className="space-y-1 text-xs">
                          <li>• <strong>יד 2:</strong> מחיר, שטח, חדרים ומקלחות</li>
                          <li>• <strong>GIS:</strong> מידע תכנוני וזכויות בנייה</li>
                          <li>• <strong>רמ״י:</strong> שומות ומסמכים רשמיים</li>
                          <li>• <strong>ממשלה:</strong> היתרי בנייה, עיסקאות השוואה ותוכניות</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  <SheetFooter>
                    <Button type="submit">שמור</Button>
                  </SheetFooter>
                </form>
              </SheetContent>
            </Sheet>
          ) : (
            <Button 
              variant="outline" 
              onClick={() => handleProtectedAction('add-listing')}
              className="bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100"
            >
              התחבר להוספת נכס
            </Button>
          )}
        </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-end gap-4">
          <Input
            placeholder="חיפוש"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-40 sm:w-64"
          />
          <Select value={city} onValueChange={setCity}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="עיר" />
            </SelectTrigger>
            <SelectContent>
              {cityOptions.map(c => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="סוג" />
            </SelectTrigger>
            <SelectContent>
              {typeOptions.map(t => (
                <SelectItem key={t} value={t}>
                  {t}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="flex items-center gap-2">
            <Input
              type="number"
              placeholder="מינ ₪"
              value={priceMin}
              onChange={e => setPriceMin(e.target.value)}
              className="w-24"
            />
            <Input
              type="number"
              placeholder="מקס ₪"
              value={priceMax}
              onChange={e => setPriceMax(e.target.value)}
              className="w-24"
            />
          </div>
          {(search || city || typeFilter || priceMin || priceMax) && (
            <Button
              variant="ghost"
              onClick={() => {
                setSearch('')
                setCity('')
                setTypeFilter('')
                setPriceMin('')
                setPriceMax('')
              }}
            >
              נקה
            </Button>
          )}
        </div>

        {/* Main Table */}
        <Card>
          <CardHeader>
            <CardTitle>נכסים זמינים</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="w-full overflow-x-auto">
              <Table className="min-w-full">
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right whitespace-nowrap">נכס</TableHead>
                    <TableHead className="text-right whitespace-nowrap">מחיר</TableHead>
                    <TableHead className="text-right whitespace-nowrap">₪/מ״ר</TableHead>
                    <TableHead className="text-right whitespace-nowrap">Δ איזור</TableHead>
                    <TableHead className="text-right whitespace-nowrap">ימי שוק (אחוזון)</TableHead>
                    <TableHead className="text-right whitespace-nowrap">תחרות</TableHead>
                    <TableHead className="text-right whitespace-nowrap">ייעוד</TableHead>
                    <TableHead className="text-right whitespace-nowrap">יתרת זכ׳</TableHead>
                    <TableHead className="text-right whitespace-nowrap">תכנית</TableHead>
                    <TableHead className="text-right whitespace-nowrap">היתר</TableHead>
                    <TableHead className="text-right whitespace-nowrap">רעש</TableHead>
                    <TableHead className="text-right whitespace-nowrap">שטחי ציבור</TableHead>
                    <TableHead className="text-right whitespace-nowrap">סיכון</TableHead>
                    <TableHead className="text-right whitespace-nowrap">מחיר מודל</TableHead>
                    <TableHead className="text-right whitespace-nowrap">פער</TableHead>
                    <TableHead className="text-right whitespace-nowrap">רמת ביטחון</TableHead>
                    <TableHead className="text-right whitespace-nowrap">תשואה</TableHead>
                    <TableHead className="text-right whitespace-nowrap">פעולות</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredListings.map((listing) => (
                    <TableRow 
                      key={listing.id} 
                      className="hover:bg-muted/50 cursor-pointer group clickable-row"
                      onClick={() => window.open(`/listings/${listing.id}`, '_self')}
                    >
                      <TableCell>
                        <div>
                          <div className="font-semibold group-hover:text-primary transition-colors">
                            {listing.address}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {listing.city}{listing.neighborhood ? ` · ${listing.neighborhood}` : ''} · {listing.type === 'house' ? 'בית' : 'דירה'} · {listing.netSqm} מ״ר
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="font-mono">{fmtCurrency(listing.price)}</TableCell>
                      <TableCell className="font-mono">{listing.pricePerSqm ? fmtNumber(listing.pricePerSqm) : '—'}</TableCell>
                      <TableCell>
                        <Badge variant={listing.deltaVsAreaPct && listing.deltaVsAreaPct >= 0 ? 'default' : 'destructive'}>
                          {listing.deltaVsAreaPct ? `${listing.deltaVsAreaPct > 0 ? '+' : ''}${listing.deltaVsAreaPct}%` : '—'}
                        </Badge>
                      </TableCell>
                      <TableCell><Badge>P{listing.domPercentile || '—'}</Badge></TableCell>
                      <TableCell><Badge variant="secondary">{listing.competition1km || '—'}</Badge></TableCell>
                      <TableCell><Badge variant="outline">{listing.zoning || '—'}</Badge></TableCell>
                      <TableCell><Badge>+{listing.remainingRightsSqm ? fmtNumber(listing.remainingRightsSqm) : '—'} מ״ר</Badge></TableCell>
                      <TableCell><Badge variant="secondary">{listing.program || '—'}</Badge></TableCell>
                      <TableCell><Badge>{listing.lastPermitQ || '—'}</Badge></TableCell>
                      <TableCell><Badge>{listing.noiseLevel}/5</Badge></TableCell>
                      <TableCell>
                        <Badge variant={listing.greenWithin300m ? 'good' : 'bad'}>
                          {listing.greenWithin300m ? 'כן' : 'לא'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {listing.riskFlags && listing.riskFlags.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {listing.riskFlags.map((flag, i) => (
                              <Badge 
                                key={i} 
                                variant={flag.includes('שימור') ? 'bad' : flag.includes('אנטנה') ? 'warn' : 'default'}
                              >
                                {flag}
                              </Badge>
                            ))}
                          </div>
                        ) : (
                          <Badge variant="good">ללא</Badge>
                        )}
                      </TableCell>
                      <TableCell className="font-mono">{listing.modelPrice ? fmtCurrency(listing.modelPrice) : '—'}</TableCell>
                      <TableCell>
                        <Badge variant={listing.priceGapPct && listing.priceGapPct > 0 ? 'warn' : 'good'}>
                          {listing.priceGapPct ? `${listing.priceGapPct > 0 ? '+' : ''}${listing.priceGapPct.toFixed(1)}%` : '—'}
                        </Badge>
                      </TableCell>
                      <TableCell><Badge>{listing.confidencePct}%</Badge></TableCell>
                      <TableCell><Badge>{listing.capRatePct?.toFixed(1)}%</Badge></TableCell>
                      <TableCell onClick={(e) => e.stopPropagation()}>
                        <Button variant="ghost" size="sm" asChild>
                          <Link href={`/listings/${listing.id}`}>
                            צפה
                          </Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            מציג {filteredListings.length} מתוך {listings.length} נכסים עם נתוני שמאות מלאים
          </p>
        </div>
      </div>
    </DashboardLayout>
  )
}
