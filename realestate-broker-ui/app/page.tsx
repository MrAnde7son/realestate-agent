import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Building, TrendingUp, AlertCircle, Calculator } from 'lucide-react'
import Link from 'next/link'
import DashboardLayout from '@/components/layout/dashboard-layout'

export default function Home() {
  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">בית ניהול נדל״ן</h1>
          <p className="text-muted-foreground">ממשק תיווך מתקדם עם נתוני שמאות ותכנון</p>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">נכסים זמינים</CardTitle>
              <Building className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">5</div>
              <p className="text-xs text-muted-foreground">
                עם נתוני שמאות מלאים
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">ממוצע מחיר למ״ר</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">₪62,840</div>
              <p className="text-xs text-muted-foreground">
                +4.1% מהחודש הקודם
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">התראות פעילות</CardTitle>
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">3</div>
              <p className="text-xs text-muted-foreground">
                התאמות למחפשים
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">ROI ממוצע</CardTitle>
              <Calculator className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">3.1%</div>
              <p className="text-xs text-muted-foreground">
                תשואה שנתית משוערת
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>פעולות מהירות</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">רשימת נכסים</h3>
                  <p className="text-sm text-muted-foreground">טבלה מפורטת עם נתוני שמאות</p>
                </div>
                <Button asChild>
                  <Link href="/listings">צפה</Link>
                </Button>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">התראות חדשות</h3>
                  <p className="text-sm text-muted-foreground">הגדר התראות על נכסים</p>
                </div>
                <Button variant="outline" asChild>
                  <Link href="/alerts">הגדר</Link>
                </Button>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">אנליזת משכנתא</h3>
                  <p className="text-sm text-muted-foreground">חישוב תרחישי מימון</p>
                </div>
                <Button variant="outline" asChild>
                  <Link href="/mortgage/analyze">חשב</Link>
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>נכסים מובילים</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">הגולן 1, תל אביב</h3>
                  <p className="text-sm text-muted-foreground">בית · 110 מ״ר · 4 חד׳</p>
                </div>
                <div className="text-right">
                  <div className="font-medium">₪7.65M</div>
                  <Badge variant="good">ללא סיכון</Badge>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">יהודה המכבי 120</h3>
                  <p className="text-sm text-muted-foreground">דירה · 73 מ״ר · 3 חד׳</p>
                </div>
                <div className="text-right">
                  <div className="font-medium">₪5.20M</div>
                  <Badge variant="good">ללא סיכון</Badge>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">שדרות ירושלים 45</h3>
                  <p className="text-sm text-muted-foreground">דירה · 76 מ״ר · 3 חד׳</p>
                </div>
                <div className="text-right">
                  <div className="font-medium">₪3.99M</div>
                  <Badge variant="warn">שימור</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}