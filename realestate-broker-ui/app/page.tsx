import React from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { getActiveAlertsCount, getActiveListingsCount, listings } from '@/lib/data'

export default function HomePage() {
  const activeAlertsCount = getActiveAlertsCount()
  const activeListingsCount = getActiveListingsCount()
  const totalPrice = listings.reduce((sum, listing) => sum + listing.price, 0)
  const averagePrice = totalPrice / listings.length
  const averageCapRate = listings.reduce((sum, listing) => sum + (listing.capRatePct || 0), 0) / listings.length

  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader heading="דשבורד נדל״ן" text="סקירה כללית של הפעילות והנתונים" />
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">נכסים פעילים</CardTitle>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                className="h-4 w-4 text-muted-foreground"
              >
                <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                <polyline points="9,22 9,12 15,12 15,22" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{activeListingsCount}</div>
              <p className="text-xs text-muted-foreground">מתוך {listings.length} נכסים כולל</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">התראות פעילות</CardTitle>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                className="h-4 w-4 text-muted-foreground"
              >
                <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
                <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{activeAlertsCount}</div>
              <p className="text-xs text-muted-foreground">דורש תשומת לב</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">ממוצע מחיר</CardTitle>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                className="h-4 w-4 text-muted-foreground"
              >
                <rect width="20" height="14" x="2" y="5" rx="2" />
                <path d="M2 10h20" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{(averagePrice / 1000000).toFixed(1)}M ₪</div>
              <p className="text-xs text-muted-foreground">מבוסס על {listings.length} נכסים</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">ROI ממוצע</CardTitle>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                className="h-4 w-4 text-muted-foreground"
              >
                <polyline points="22,12 18,12 15,21 9,3 6,12 2,12" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{averageCapRate.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">מבוסס על ניתוח השוק</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          <Card className="col-span-4">
            <CardHeader>
              <CardTitle>נכסים במעקב</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>כתובת</TableHead>
                    <TableHead>מחיר</TableHead>
                    <TableHead>סטטוס</TableHead>
                    <TableHead>תאריך</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {listings.map((listing) => (
                    <TableRow key={listing.id}>
                      <TableCell>{listing.address}</TableCell>
                      <TableCell>{(listing.price / 1000000).toFixed(2)}M ₪</TableCell>
                      <TableCell>
                        <Badge variant={
                          listing.status === 'active' ? 'secondary' : 
                          listing.status === 'pending' ? 'outline' : 'default'
                        }>
                          {listing.status === 'active' ? 'פעיל' : 
                           listing.status === 'pending' ? 'ממתין' : 'נמכר'}
                        </Badge>
                      </TableCell>
                      <TableCell>{new Date().toLocaleDateString('he-IL')}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
          
          <Card className="col-span-3">
            <CardHeader>
              <CardTitle>פעולות מהירות</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button className="w-full" variant="outline" asChild>
                <a href="/listings">צפה בכל הנכסים</a>
              </Button>
              <Button className="w-full" variant="outline" asChild>
                <a href="/alerts">נהל התראות ({activeAlertsCount})</a>
              </Button>
              <Button className="w-full" variant="outline" asChild>
                <a href="/mortgage/analyze">מחשבון משכנתא</a>
              </Button>
              <Button className="w-full" variant="outline">
                הפק דוח שוק
              </Button>
            </CardContent>
          </Card>
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}