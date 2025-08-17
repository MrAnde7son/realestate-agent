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
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger, SheetFooter, SheetDescription } from '@/components/ui/sheet'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { fmtCurrency, fmtNumber } from '@/lib/utils'

export default function ListingsPage() {
  const [listings, setListings] = useState<Listing[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)

  const newListingSchema = z.object({
    address: z.string().min(1, 'חובה להזין כתובת'),
    price: z.preprocess((v) => Number(v), z.number().gt(0, 'חובה להזין מחיר')), 
    bedrooms: z.preprocess((v) => Number(v), z.number().int().gte(0, 'חובה להזין חדרים')),
    bathrooms: z.preprocess((v) => Number(v), z.number().int().gte(0, 'חובה להזין מקלחות')),
    area: z.preprocess((v) => Number(v), z.number().gt(0, 'חובה להזין שטח')),
  })
  type NewListing = z.infer<typeof newListingSchema>

  const form = useForm<NewListing>({
    resolver: zodResolver(newListingSchema),
    defaultValues: {
      address: '',
      price: undefined,
      bedrooms: undefined,
      bathrooms: undefined,
      area: undefined,
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
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">רשימת נכסים</h1>
            <p className="text-muted-foreground">
              {listings.length} נכסים עם נתוני שמאות ותכנון מלאים
            </p>
          </div>
        <div className="flex items-center space-x-2">
          <Input placeholder="עיר" className="w-32" />
          <Input placeholder="₪/מ״ר 45,000–80,000" className="w-40" />
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button variant="default">הוסף נכס</Button>
            </SheetTrigger>
            <SheetContent>
              <SheetHeader>
                <SheetTitle>הוסף נכס</SheetTitle>
                <SheetDescription>מלא את הפרטים של הנכס החדש.</SheetDescription>
              </SheetHeader>
              <form
                onSubmit={form.handleSubmit(async (values) => {
                  const res = await fetch('/api/listings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(values),
                  })
                  const data = await res.json()
                  if (res.ok) {
                    setListings((prev) => [...prev, data.listing])
                    form.reset()
                    setOpen(false)
                  }
                })}
                className="space-y-4"
              >
                <div className="space-y-2">
                  <Label htmlFor="address">כתובת</Label>
                  <Input id="address" {...form.register('address')} />
                  {form.formState.errors.address && (
                    <p className="text-sm text-destructive">
                      {form.formState.errors.address.message}
                    </p>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="price">מחיר</Label>
                    <Input id="price" type="number" {...form.register('price')} />
                    {form.formState.errors.price && (
                      <p className="text-sm text-destructive">
                        {form.formState.errors.price.message}
                      </p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="area">מ״ר</Label>
                    <Input id="area" type="number" {...form.register('area')} />
                    {form.formState.errors.area && (
                      <p className="text-sm text-destructive">
                        {form.formState.errors.area.message}
                      </p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bedrooms">חדרים</Label>
                    <Input id="bedrooms" type="number" {...form.register('bedrooms')} />
                    {form.formState.errors.bedrooms && (
                      <p className="text-sm text-destructive">
                        {form.formState.errors.bedrooms.message}
                      </p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bathrooms">מקלחות</Label>
                    <Input id="bathrooms" type="number" {...form.register('bathrooms')} />
                    {form.formState.errors.bathrooms && (
                      <p className="text-sm text-destructive">
                        {form.formState.errors.bathrooms.message}
                      </p>
                    )}
                  </div>
                </div>
                <SheetFooter>
                  <Button type="submit">שמור</Button>
                </SheetFooter>
              </form>
            </SheetContent>
          </Sheet>
          <Button variant="default">שמור תצוגה</Button>
        </div>
      </div>

        {/* Main Table */}
        <Card>
          <CardHeader>
            <CardTitle>נכסים זמינים</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right">נכס</TableHead>
                    <TableHead className="text-right">מחיר</TableHead>
                    <TableHead className="text-right">₪/מ״ר</TableHead>
                    <TableHead className="text-right">Δ איזור</TableHead>
                    <TableHead className="text-right">ימי שוק (אחוזון)</TableHead>
                    <TableHead className="text-right">תחרות</TableHead>
                    <TableHead className="text-right">ייעוד</TableHead>
                    <TableHead className="text-right">יתרת זכ׳</TableHead>
                    <TableHead className="text-right">תכנית</TableHead>
                    <TableHead className="text-right">היתר</TableHead>
                    <TableHead className="text-right">רעש</TableHead>
                    <TableHead className="text-right">שטחי ציבור</TableHead>
                    <TableHead className="text-right">סיכון</TableHead>
                    <TableHead className="text-right">מחיר מודל</TableHead>
                    <TableHead className="text-right">פער</TableHead>
                    <TableHead className="text-right">רמת ביטחון</TableHead>
                    <TableHead className="text-right">תשואה</TableHead>
                    <TableHead className="text-right">פעולות</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {listings.map((listing) => (
                    <TableRow key={listing.id} className="hover:bg-muted/50">
                      <TableCell>
                        <div>
                          <div className="font-semibold">
                            <Link 
                              href={`/listings/${listing.id}`}
                              className="hover:text-primary transition-colors"
                            >
                              {listing.address}
                            </Link>
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
                      <TableCell>
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
            מציג {listings.length} נכסים עם נתוני שמאות מלאים
          </p>
          {listings.length > 0 && (
            <Button variant="outline" asChild>
              <Link href={`/listings/${listings[0].id}`}>
                פתח דף פרטי נכס לדוגמה →
              </Link>
            </Button>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
