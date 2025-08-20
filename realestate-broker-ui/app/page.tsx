'use client'

import React from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Building, AlertCircle, Calculator, BarChart3, TrendingUp, Users, MapPin, Clock, DollarSign, Home, Car, TrendingDown, Eye, Heart, Share2 } from 'lucide-react'
import Link from 'next/link'
import { ProtectedRoute } from '@/components/auth/protected-route'
import { useAuth } from '@/lib/auth-context'
import { fmtCurrency, fmtNumber } from '@/lib/utils'
import { useDashboardData } from '@/lib/dashboard'

// Chart components
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

export default function HomePage() {
  const { user } = useAuth()
  const { data: dashboardData, loading, error } = useDashboardData()

  if (loading) {
    return (
      <ProtectedRoute>
        <DashboardLayout>
          <DashboardShell>
            <DashboardHeader 
              heading="ברוכים הבאים לנדל״נר" 
              text="פלטפורמה מתקדמת לניהול נכסים, התראות שוק ומחשבוני משכנתא" 
            />
            <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
              {[...Array(4)].map((_, i) => (
                <Card key={i}>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <Skeleton className="h-4 w-20" />
                    <Skeleton className="h-4 w-4" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-8 w-16 mb-2" />
                    <Skeleton className="h-4 w-24" />
                  </CardContent>
                </Card>
              ))}
            </div>
          </DashboardShell>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  if (!dashboardData) {
    return (
      <ProtectedRoute>
        <DashboardLayout>
          <DashboardShell>
            <DashboardHeader 
              heading="ברוכים הבאים לנדל״נר" 
              text="פלטפורמה מתקדמת לניהול נכסים, התראות שוק ומחשבוני משכנתא" 
            />
            <div className="text-center py-12">
              <p className="text-muted-foreground">לא ניתן לטעון נתוני לוח הבקרה</p>
            </div>
          </DashboardShell>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  if (error) {
    return (
      <ProtectedRoute>
        <DashboardLayout>
          <DashboardShell>
            <DashboardHeader 
              heading="ברוכים הבאים לנדל״נר" 
              text="פלטפורמה מתקדמת לניהול נכסים, התראות שוק ומחשבוני משכנתא" 
            />
            <div className="text-center py-12">
              <div className="bg-destructive/10 text-destructive p-4 rounded-lg max-w-md mx-auto">
                <p className="font-medium mb-2">שגיאה בטעינת נתונים</p>
                <p className="text-sm">{error}</p>
                <Button 
                  onClick={() => window.location.reload()} 
                  variant="outline" 
                  className="mt-4"
                >
                  נסה שוב
                </Button>
              </div>
            </div>
          </DashboardShell>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042']

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <DashboardShell>
          <DashboardHeader 
            heading={`ברוכים הבאים, ${user?.first_name || 'משתמש'}!`}
            text="פלטפורמה מתקדמת לניהול נכסים, התראות שוק ומחשבוני משכנתא" 
          />
          
          {/* KPI Cards */}
          <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
          <Link href="/listings" className="block">

            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">סה&quot;כ נכסים</CardTitle>
                <Building className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{fmtNumber(dashboardData.totalListings)}</div>
                <p className="text-xs text-muted-foreground">
                  +{Math.floor(Math.random() * 5) + 1} מהחודש שעבר
                </p>
              </CardContent>
            </Card>
            </Link>

            <Link href="/alerts" className="block">

            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">התראות פעילות</CardTitle>
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{fmtNumber(dashboardData.activeAlerts)}</div>
                <p className="text-xs text-muted-foreground">
                  {Math.floor(Math.random() * 3) + 1} התראות חדשות היום
                </p>
              </CardContent>
            </Card>
            </Link>

            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">לקוחות פעילים</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{fmtNumber(dashboardData.totalClients)}</div>
                <p className="text-xs text-muted-foreground">
                  +{Math.floor(Math.random() * 3) + 1} השבוע
                </p>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">הכנסה חודשית</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{fmtCurrency(dashboardData.monthlyRevenue)}</div>
                <p className="text-xs text-muted-foreground">
                  {dashboardData.marketTrend === 'up' ? '+' : ''}{Math.floor(Math.random() * 15) + 5}% מהחודש שעבר
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Charts Section */}
          <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
            {/* Market Trends Chart */}
            <Card>
              <CardHeader>
                <CardTitle>מגמות שוק - מחירים ממוצעים</CardTitle>
                <CardDescription>שינויי מחירים לאורך 6 החודשים האחרונים</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={dashboardData.marketData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip 
                      formatter={(value: number) => [fmtCurrency(value), 'מחיר ממוצע']}
                      labelFormatter={(label) => `חודש: ${label}`}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="avgPrice" 
                      stroke="#8884d8" 
                      fill="#8884d8" 
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Property Types Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>התפלגות סוגי נכסים</CardTitle>
                <CardDescription>חלוקה לפי סוגי נכסים במאגר</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={dashboardData.propertyTypes}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ type, percentage }) => `${type} ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {dashboardData.propertyTypes.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => [value, 'כמות']} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Market Volume and Transactions */}
          <Card>
            <CardHeader>
              <CardTitle>נפח עסקאות ושוק</CardTitle>
              <CardDescription>סך העסקאות ונפח השוק החודשי</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={dashboardData.marketData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip 
                    formatter={(value: number, name: string) => [
                      name === 'transactions' ? value : fmtCurrency(value),
                      name === 'transactions' ? 'עסקאות' : 'נפח שוק'
                    ]}
                  />
                  <Bar yAxisId="left" dataKey="transactions" fill="#8884d8" name="transactions" />
                  <Bar yAxisId="right" dataKey="volume" fill="#82ca9d" name="volume" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Top Areas Performance */}
          <Card>
            <CardHeader>
              <CardTitle>ביצועי האזורים המובילים</CardTitle>
              <CardDescription>האזורים עם הפעילות הגבוהה ביותר</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
                {dashboardData.topAreas.map((area, index) => (
                  <div key={index} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">{area.area}</h4>
                      <Badge variant={area.trend > 5 ? "default" : area.trend > 3 ? "secondary" : "outline"}>
                        {area.trend > 0 ? '+' : ''}{area.trend}%
                      </Badge>
                    </div>
                    <div className="text-2xl font-bold">{fmtNumber(area.listings)}</div>
                    <div className="text-sm text-muted-foreground">
                      {fmtCurrency(area.avgPrice)} ממוצע
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recent Activity Feed */}
          <Card>
            <CardHeader>
              <CardTitle>פעילות אחרונה</CardTitle>
              <CardDescription>הפעילויות והעדכונים האחרונים במערכת</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {dashboardData.recentActivity.map((activity) => (
                  <div key={activity.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-full ${
                        activity.type === 'listing' ? 'bg-blue-100 text-blue-600' :
                        activity.type === 'alert' ? 'bg-orange-100 text-orange-600' :
                        activity.type === 'client' ? 'bg-green-100 text-green-600' :
                        'bg-purple-100 text-purple-600'
                      }`}>
                        {activity.type === 'listing' ? <Building className="h-4 w-4" /> :
                         activity.type === 'alert' ? <AlertCircle className="h-4 w-4" /> :
                         activity.type === 'client' ? <Users className="h-4 w-4" /> :
                         <DollarSign className="h-4 w-4" />}
                      </div>
                      <div>
                        <p className="font-medium">{activity.title}</p>
                        <p className="text-sm text-muted-foreground">
                          {new Date(activity.timestamp).toLocaleString('he-IL')}
                        </p>
                      </div>
                    </div>
                    {activity.value && (
                      <div className="text-right">
                        <div className="font-medium">{fmtCurrency(activity.value)}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Building className="h-5 w-5 text-blue-600" />
                  </div>
                  <CardTitle className="text-lg">הוסף נכס חדש</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  הוסף נכס חדש למאגר שלך עם כל הפרטים והתמונות
                </CardDescription>
                <Button asChild className="w-full mt-4">
                  <Link href="/listings">
                    <Building className="h-4 w-4 ml-2" />
                    הוסף נכס
                  </Link>
                </Button>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <AlertCircle className="h-5 w-5 text-orange-600" />
                  </div>
                  <CardTitle className="text-lg">צור התראה חדשה</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  הגדר התראה מותאמת אישית וקבל התראות על הזדמנויות בשוק
                </CardDescription>
                <Button asChild variant="outline" className="w-full mt-4">
                  <Link href="/alerts">
                    <AlertCircle className="h-4 w-4 ml-2" />
                    צור התראה
                  </Link>
                </Button>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Calculator className="h-5 w-5 text-green-600" />
                  </div>
                  <CardTitle className="text-lg">מחשבון משכנתא</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  חשב משכנתאות ובדוק זכאות עם נתוני בנק ישראל בזמן אמת
                </CardDescription>
                <Button asChild variant="outline" className="w-full mt-4">
                  <Link href="/mortgage/analyze">
                    <Calculator className="h-4 w-4 ml-2" />
                    חשב משכנתא
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </DashboardShell>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
