import React from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Building, AlertCircle, Calculator, BarChart3, TrendingUp, Users, MapPin, Clock } from 'lucide-react'
import Link from 'next/link'
import { ProtectedRoute } from '@/components/auth/protected-route'

export default function HomePage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <DashboardShell>
          <DashboardHeader 
            heading="ברוכים הבאים לנדל״נר" 
            text="פלטפורמה מתקדמת לניהול נכסים, התראות שוק ומחשבוני משכנתא" 
          />
          
          {/* Welcome Section */}
          <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>סקירה כללית</CardTitle>
                  <CardDescription>
                    התחל לחקור את הפלטפורמה שלנו
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    נדל״נר היא פלטפורמה חכמה המחברת בין שמאים, מתווכים ומשקיעים. 
                    השתמש בכלים המתקדמים שלנו לניהול נכסים, מעקב אחר שוק הנדל״ן וחישובי משכנתא.
                  </p>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                      <Building className="h-5 w-5 text-primary" />
                      <div>
                        <div className="font-medium">נכסים במעקב</div>
                        <div className="text-sm text-muted-foreground">0 נכסים</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                      <AlertCircle className="h-5 w-5 text-orange-500" />
                      <div>
                        <div className="font-medium">התראות פעילות</div>
                        <div className="text-sm text-muted-foreground">0 התראות</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>פעולות מהירות</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Button asChild className="w-full justify-start">
                    <Link href="/listings">
                      <Building className="h-4 w-4 ml-2" />
                      הוסף נכס חדש
                    </Link>
                  </Button>
                  
                  <Button asChild variant="outline" className="w-full justify-start">
                    <Link href="/alerts">
                      <AlertCircle className="h-4 w-4 ml-2" />
                      צור התראה חדשה
                    </Link>
                  </Button>
                  
                  <Button asChild variant="outline" className="w-full justify-start">
                    <Link href="/mortgage/analyze">
                      <Calculator className="h-4 w-4 ml-2" />
                      מחשבון משכנתא
                    </Link>
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>סטטיסטיקות</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-green-500" />
                      <span className="text-sm">נכסים במעקב</span>
                    </div>
                    <span className="font-medium">0</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-blue-500" />
                      <span className="text-sm">לקוחות פעילים</span>
                    </div>
                    <span className="font-medium">0</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4 text-purple-500" />
                      <span className="text-sm">אזורים במעקב</span>
                    </div>
                    <span className="font-medium">0</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Features Grid */}
          <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Building className="h-5 w-5 text-blue-600" />
                  </div>
                  <CardTitle className="text-lg">ניהול נכסים</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  נהל את הנכסים שלך, עקוב אחר מחירים וקבל עדכונים בזמן אמת על שינויים בשוק.
                </CardDescription>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <AlertCircle className="h-5 w-5 text-orange-600" />
                  </div>
                  <CardTitle className="text-lg">התראות חכמות</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  הגדר התראות מותאמות אישית וקבל התראות על הזדמנויות בשוק הנדל״ן.
                </CardDescription>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Calculator className="h-5 w-5 text-green-600" />
                  </div>
                  <CardTitle className="text-lg">מחשבוני משכנתא</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  חשב משכנתאות, בדוק זכאות וקבל המלצות מותאמות אישית למצב הכלכלי שלך.
                </CardDescription>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <BarChart3 className="h-5 w-5 text-purple-600" />
                  </div>
                  <CardTitle className="text-lg">דוחות מתקדמים</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  צור דוחות מפורטים על נכסים, עסקאות וניתוחי שוק עם כלים מתקדמים.
                </CardDescription>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <Clock className="h-5 w-5 text-red-600" />
                  </div>
                  <CardTitle className="text-lg">עדכונים בזמן אמת</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  קבל עדכונים מיידיים על שינויים במחירים, עסקאות חדשות והזדמנויות בשוק.
                </CardDescription>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <Users className="h-5 w-5 text-yellow-600" />
                  </div>
                  <CardTitle className="text-lg">קהילה מקצועית</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  התחבר עם אנשי מקצוע אחרים בתחום הנדל״ן ושתף ידע וניסיון.
                </CardDescription>
              </CardContent>
            </Card>
          </div>
        </DashboardShell>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
