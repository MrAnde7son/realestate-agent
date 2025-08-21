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

  // Function to fetch assets (listings)
  const fetchListings = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/assets')
      if (response.ok) {
        const data = await response.json()
        setListings(data.rows)
      } else {
        console.error('Failed to fetch assets')
      }
    } catch (error) {
      console.error('Error fetching assets:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleProtectedAction = (action: string) => {
    if (!isAuthenticated) {
      router.push('/auth?redirect=' + encodeURIComponent(window.location.pathname))
    }
  }

  const newListingSchema = z.object({
    scopeType: z.enum(['address', 'neighborhood', 'street', 'city', 'parcel']),
    // Common fields
    city: z.string().min(1, 'עיר נדרשת'),
    radius: z.number().min(50).max(1000).default(150),
    // Address-specific fields
    address: z.string().optional(),
    street: z.string().optional(),
    number: z.number().optional(),
    // Neighborhood-specific fields
    neighborhood: z.string().optional(),
    // Parcel-specific fields
    gush: z.string().optional(),
    helka: z.string().optional(),
  }).refine((data) => {
    // Validate required fields based on scope type
    if (data.scopeType === 'address') {
      return data.address && data.address.length > 0
    }
    if (data.scopeType === 'neighborhood') {
      return data.neighborhood && data.neighborhood.length > 0
    }
    if (data.scopeType === 'street') {
      return data.street && data.street.length > 0
    }
    if (data.scopeType === 'parcel') {
      return data.gush && data.helka
    }
    if (data.scopeType === 'city') {
      return data.city && data.city.length > 0
    }
    return true
  }, {
    message: 'Please fill in all required fields for the selected scope type'
  })

  type NewListing = z.infer<typeof newListingSchema>

  const form = useForm<NewListing>({
    resolver: zodResolver(newListingSchema),
    defaultValues: {
      scopeType: 'address',
      city: 'תל אביב',
      radius: 150,
      address: '',
      street: '',
      number: undefined,
      neighborhood: '',
      gush: '',
      helka: '',
    },
  })

  const [assetId, setAssetId] = useState<number | null>(null)
  const [assetStatus, setAssetStatus] = useState<string>('')
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null)

  // Poll asset status when assetId is set
  useEffect(() => {
    if (assetId && assetStatus !== 'ready' && assetStatus !== 'error') {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(`/api/listings/${assetId}`)
          if (response.ok) {
            const data = await response.json()
            setAssetStatus(data.status)
            
            if (data.status === 'ready' || data.status === 'error') {
              clearInterval(interval)
              setPollingInterval(null)
            }
          }
        } catch (error) {
          console.error('Error polling asset status:', error)
        }
      }, 3000)
      
      setPollingInterval(interval)
      
      return () => {
        clearInterval(interval)
        setPollingInterval(null)
      }
    }
  }, [assetId, assetStatus])

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
      }
    }
  }, [pollingInterval])

  useEffect(() => {
    fetchListings()
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
            <Button 
              onClick={fetchListings} 
              variant="outline" 
              disabled={loading}
              className="flex items-center gap-2"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              )}
              רענן
            </Button>
            {isAuthenticated ? (
              <Sheet open={open} onOpenChange={setOpen}>
                <SheetTrigger asChild>
                  <Button variant="default">הוסף נכס</Button>
                </SheetTrigger>
                <SheetContent>
                  <SheetHeader>
                    <SheetTitle>הוסף נכס חדש</SheetTitle>
                    <SheetDescription>
                      בחר סוג היקף והמערכת תאסוף אוטומטית מידע מיד 2, GIS, רמ״י וממשלה
                    </SheetDescription>
                  </SheetHeader>
                  <form
                    onSubmit={form.handleSubmit(async (values) => {
                      try {
                        // Show loading state
                        const submitButton = document.querySelector('button[type="submit"]') as HTMLButtonElement
                        if (submitButton) {
                          submitButton.disabled = true
                          submitButton.innerHTML = '<div class="flex items-center gap-2"><div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>יוצר נכס...</div>'
                        }

                        // Build payload based on scope type
                        const payload = {
                          scope: {
                            type: values.scopeType,
                            value: values.scopeType === 'address' ? values.address : 
                                   values.scopeType === 'neighborhood' ? values.neighborhood :
                                   values.scopeType === 'street' ? values.street :
                                   values.scopeType === 'parcel' ? `${values.gush}/${values.helka}` : values.city,
                            city: values.city
                          },
                          city: values.city,
                          radius: values.radius,
                          ...(values.address && { address: values.address }),
                          ...(values.street && { street: values.street }),
                          ...(values.number && { number: values.number }),
                          ...(values.neighborhood && { neighborhood: values.neighborhood }),
                          ...(values.gush && { gush: values.gush }),
                          ...(values.helka && { helka: values.helka }),
                        }

                        // Create asset using new API
                        const response = await fetch('/api/assets', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify(payload),
                        })
                        
                        if (response.ok) {
                          const result = await response.json()
                          setAssetId(result.id)
                          setAssetStatus(result.status)
                          alert('נכס נוצר בהצלחה! תהליך העשרת המידע התחיל.')
                          form.reset()
                          setOpen(false)
                          // Refresh listings to show the new asset
                          await fetchListings()
                        } else {
                          const errorData = await response.json()
                          throw new Error(errorData.error || 'שגיאה ביצירת הנכס')
                        }
                      } catch (error) {
                        console.error('Error creating asset:', error)
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
                    {/* Scope Type Selection */}
                    <div className="space-y-2">
                      <Label htmlFor="scopeType">סוג היקף</Label>
                      <select
                        id="scopeType"
                        {...form.register('scopeType')}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      >
                        <option value="address">כתובת ספציפית</option>
                        <option value="neighborhood">שכונה</option>
                        <option value="street">רחוב</option>
                        <option value="city">עיר</option>
                        <option value="parcel">גוש/חלקה</option>
                      </select>
                    </div>

                    {/* Common Fields */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="city">עיר</Label>
                        <Input 
                          id="city" 
                          placeholder="תל אביב"
                          {...form.register('city')} 
                        />
                        {form.formState.errors.city && (
                          <p className="text-sm text-destructive">
                            {form.formState.errors.city.message}
                          </p>
                        )}
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="radius">רדיוס (מטרים)</Label>
                        <Input 
                          id="radius" 
                          type="number"
                          min="50"
                          max="1000"
                          placeholder="150"
                          {...form.register('radius', { valueAsNumber: true })} 
                        />
                      </div>
                    </div>

                    {/* Address-specific fields */}
                    {form.watch('scopeType') === 'address' && (
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
                    )}

                    {/* Neighborhood-specific fields */}
                    {form.watch('scopeType') === 'neighborhood' && (
                      <div className="space-y-2">
                        <Label htmlFor="neighborhood">שם השכונה</Label>
                        <Input 
                          id="neighborhood" 
                          placeholder="לדוגמה: רמת החייל"
                          {...form.register('neighborhood')} 
                        />
                      </div>
                    )}

                    {/* Street-specific fields */}
                    {form.watch('scopeType') === 'street' && (
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="street">שם הרחוב</Label>
                          <Input 
                            id="street" 
                            placeholder="לדוגמה: הגולן"
                            {...form.register('street')} 
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="number">מספר בית</Label>
                          <Input 
                            id="number" 
                            type="number"
                            placeholder="לדוגמה: 32"
                            {...form.register('number', { valueAsNumber: true })} 
                          />
                        </div>
                      </div>
                    )}

                    {/* Parcel-specific fields */}
                    {form.watch('scopeType') === 'parcel' && (
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="gush">מספר גוש</Label>
                          <Input 
                            id="gush" 
                            placeholder="לדוגמה: 1234"
                            {...form.register('gush')} 
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="helka">מספר חלקה</Label>
                          <Input 
                            id="helka" 
                            placeholder="לדוגמה: 56"
                            {...form.register('helka')} 
                          />
                        </div>
                      </div>
                    )}

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
                    <TableHead className="text-right whitespace-nowrap">סטטוס נכס</TableHead>
                    <TableHead className="text-right whitespace-nowrap">מקורות</TableHead>
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
                      onClick={() => window.open(`/listings/${listing.asset_id}`, '_self')}
                    >
                      <TableCell>
                        <div>
                          <div className="font-semibold group-hover:text-primary transition-colors flex items-center gap-2">
                            {listing.address}
                            {listing.asset_status && listing.asset_status !== 'ready' && (
                              <div className="flex items-center gap-1">
                                {listing.asset_status === 'enriching' && (
                                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600"></div>
                                )}
                                {listing.asset_status === 'pending' && (
                                  <div className="h-3 w-3 rounded-full bg-yellow-500"></div>
                                )}
                                {listing.asset_status === 'error' && (
                                  <div className="h-3 w-3 rounded-full bg-red-500"></div>
                                )}
                              </div>
                            )}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {listing.city}{listing.neighborhood ? ` · ${listing.neighborhood}` : ''} · {listing.type === 'house' ? 'בית' : 'דירה'} · {listing.netSqm} מ״ר
                            {listing.sources && listing.sources.length > 0 && (
                              <span className="text-blue-600">
                                · מקורות: {listing.sources.map(source => {
                                  const sourceLabels = {
                                    'yad2': 'יד2',
                                    'madlan': 'מדלן',
                                    'gis': 'GIS',
                                    'rami': 'רמ״י',
                                    'nadlan': 'נדלן',
                                    'asset': 'נכס חדש'
                                  }
                                  return sourceLabels[source as keyof typeof sourceLabels] || source
                                }).join(', ')}
                              </span>
                            )}
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
                      <TableCell>
                        {listing.asset_status ? (
                          <Badge 
                            variant={
                              listing.asset_status === 'ready' ? 'good' : 
                              listing.asset_status === 'error' ? 'bad' : 
                              listing.asset_status === 'enriching' ? 'warn' : 'default'
                            }
                          >
                            {listing.asset_status === 'ready' ? 'מוכן' : 
                             listing.asset_status === 'error' ? 'שגיאה' : 
                             listing.asset_status === 'enriching' ? 'מתעשר' : 'ממתין'}
                          </Badge>
                        ) : (
                          <Badge variant="default">—</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {listing.sources && listing.sources.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {listing.sources.map((source, i) => {
                              const sourceLabels = {
                                'yad2': 'יד2',
                                'madlan': 'מדלן',
                                'gis': 'GIS',
                                'rami': 'רמ״י',
                                'nadlan': 'נדלן',
                                'asset': 'נכס'
                              }
                              const label = sourceLabels[source as keyof typeof sourceLabels] || source
                              return (
                                <Badge key={i} variant="outline" className="text-xs">
                                  {label}
                                </Badge>
                              )
                            })}
                          </div>
                        ) : (
                          <Badge variant="default">—</Badge>
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
                          <Link href={`/listings/${listing.asset_id}`}>
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
