import React from 'react'
import Link from 'next/link'
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
        <DashboardHeader heading="בית" text="סקירה כללית של הפעילות והנתונים" />
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Link href="/listings" className="block">
            <Card className="cursor-pointer hover:bg-accent transition-colors">
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
          </Link>
          
          <Link href="/alerts" className="block">
            <Card className="cursor-pointer hover:bg-accent transition-colors">
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
          </Link>
          
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

        {/* Simple Charts Section - Using CSS instead of Recharts for now */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          {/* Price Trend Chart - Simple CSS Bar Chart */}
          <Card className="col-span-4">
            <CardHeader>
              <CardTitle>מגמת מחירים - 6 חודשים אחרונים</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-end justify-between gap-2 p-4">
                <div className="flex-1 flex flex-col items-center">
                  <div className="w-full bg-primary/20 rounded-t" style={{ height: '60%' }}></div>
                  <span className="text-xs mt-2">ינו</span>
                </div>
                <div className="flex-1 flex flex-col items-center">
                  <div className="w-full bg-primary/20 rounded-t" style={{ height: '70%' }}></div>
                  <span className="text-xs mt-2">פבר</span>
                </div>
                <div className="flex-1 flex flex-col items-center">
                  <div className="w-full bg-primary/20 rounded-t" style={{ height: '65%' }}></div>
                  <span className="text-xs mt-2">מרץ</span>
                </div>
                <div className="flex-1 flex flex-col items-center">
                  <div className="w-full bg-primary/20 rounded-t" style={{ height: '80%' }}></div>
                  <span className="text-xs mt-2">אפר</span>
                </div>
                <div className="flex-1 flex flex-col items-center">
                  <div className="w-full bg-primary/20 rounded-t" style={{ height: '90%' }}></div>
                  <span className="text-xs mt-2">מאי</span>
                </div>
                <div className="flex-1 flex flex-col items-center">
                  <div className="w-full bg-primary/20 rounded-t" style={{ height: '85%' }}></div>
                  <span className="text-xs mt-2">יוני</span>
                </div>
              </div>
              <div className="text-center text-sm text-muted-foreground mt-4">
                מחיר ממוצע: 2.1M - 2.6M ₪
              </div>
            </CardContent>
          </Card>

          {/* Property Type Distribution - Simple CSS Pie Chart */}
          <Card className="col-span-3">
            <CardHeader>
              <CardTitle>התפלגות סוגי נכסים</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-center justify-center">
                <div className="relative w-32 h-32">
                  {/* Simple pie chart using CSS */}
                  <div className="absolute inset-0 rounded-full border-8 border-primary/20"></div>
                  <div className="absolute inset-0 rounded-full border-8 border-blue-500/20" style={{ clipPath: 'polygon(50% 50%, 50% 0%, 100% 0%, 100% 100%, 50% 100%)' }}></div>
                  <div className="absolute inset-0 rounded-full border-8 border-green-500/20" style={{ clipPath: 'polygon(50% 50%, 0% 0%, 50% 0%)' }}></div>
                  <div className="absolute inset-0 rounded-full border-8 border-yellow-500/20" style={{ clipPath: 'polygon(50% 50%, 0% 0%, 0% 100%, 50% 100%)' }}></div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 mt-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-primary/20 rounded"></div>
                  <span>דירות (65%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-blue-500/20 rounded"></div>
                  <span>בתים (20%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500/20 rounded"></div>
                  <span>דופלקס (10%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-yellow-500/20 rounded"></div>
                  <span>נטהאוס (5%)</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Additional Charts */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          {/* Market Activity Chart - Simple CSS Bar Chart */}
          <Card className="col-span-4">
            <CardHeader>
              <CardTitle>פעילות שוק לפי אזור</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-end justify-between gap-4 p-4">
                <div className="flex-1 flex flex-col items-center">
                  <div className="w-full bg-primary/20 rounded-t" style={{ height: '90%' }}></div>
                  <span className="text-xs mt-2">תל אביב</span>
                </div>
                <div className="flex-1 flex flex-col items-center">
                  <div className="w-full bg-primary/20 rounded-t" style={{ height: '46%' }}></div>
                  <span className="text-xs mt-2">רמת גן</span>
                </div>
                <div className="flex-1 flex flex-col items-center">
                  <div className="w-full bg-primary/20 rounded-t" style={{ height: '36%' }}></div>
                  <span className="text-xs mt-2">גבעתיים</span>
                </div>
                <div className="flex-1 flex flex-col items-center">
                  <div className="w-full bg-primary/20 rounded-t" style={{ height: '64%' }}></div>
                  <span className="text-xs mt-2">הרצליה</span>
                </div>
                <div className="flex-1 flex flex-col items-center">
                  <div className="w-full bg-primary/20 rounded-t" style={{ height: '56%' }}></div>
                  <span className="text-xs mt-2">רעננה</span>
                </div>
              </div>
              <div className="text-center text-sm text-muted-foreground mt-4">
                נכסים למכירה לפי אזור
              </div>
            </CardContent>
          </Card>

          {/* ROI Trend Chart - Simple CSS Line Chart */}
          <Card className="col-span-3">
            <CardHeader>
              <CardTitle>מגמת ROI</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-center justify-center">
                <div className="w-full h-32 relative">
                  {/* Simple line chart using CSS */}
                  <svg className="w-full h-full" viewBox="0 0 100 40">
                    <polyline
                      points="10,30 20,28 30,32 40,26 50,22 60,25"
                      fill="none"
                      stroke="#16a34a"
                      strokeWidth="2"
                    />
                    <circle cx="10" cy="30" r="2" fill="#16a34a" />
                    <circle cx="20" cy="28" r="2" fill="#16a34a" />
                    <circle cx="30" cy="32" r="2" fill="#16a34a" />
                    <circle cx="40" cy="26" r="2" fill="#16a34a" />
                    <circle cx="50" cy="22" r="2" fill="#16a34a" />
                    <circle cx="60" cy="25" r="2" fill="#16a34a" />
                  </svg>
                </div>
              </div>
              <div className="text-center text-sm text-muted-foreground mt-4">
                ROI ממוצע: 4.2% - 5.1%
              </div>
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
                <a href="/mortgage/analyze">מחשבון משכנתא</a>
              </Button>
              <Button className="w-full" variant="outline">
                הפק דוח נכס
              </Button>
              <Button className="w-full" variant="outline">
                חפש נכסים
              </Button>
            </CardContent>
          </Card>
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}
