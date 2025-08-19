import React from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { User, Mail, Phone, MapPin, Building, Shield, Key, Star } from 'lucide-react'

export default function ProfilePage() {
  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader 
          heading="פרופיל אישי" 
          text="נהל את המידע האישי והגדרות החשבון שלך" 
        />
        
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Profile Information */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>מידע אישי</CardTitle>
                <CardDescription>
                  עדכן את הפרטים האישיים שלך
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                  <Avatar className="h-20 w-20">
                    <AvatarImage src="/avatars/01.png" alt="User" />
                    <AvatarFallback className="text-lg">משתמש</AvatarFallback>
                  </Avatar>
                  <div>
                    <Button variant="outline">שנה תמונה</Button>
                    <p className="text-sm text-muted-foreground mt-1">
                      JPG, PNG או GIF עד 2MB
                    </p>
                  </div>
                </div>
                
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">שם פרטי</Label>
                    <Input id="firstName" defaultValue="משתמש" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">שם משפחה</Label>
                    <Input id="lastName" defaultValue="דמו" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">דוא״ל</Label>
                    <Input id="email" type="email" defaultValue="demo@example.com" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone">טלפון</Label>
                    <Input id="phone" defaultValue="050-123-4567" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="company">חברה</Label>
                    <Input id="company" defaultValue="נדל״ן דמו בע״מ" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="position">תפקיד</Label>
                    <Input id="position" defaultValue="מתווך נדל״ן" />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="address">כתובת</Label>
                  <Input id="address" defaultValue="רחוב הרצל 123, תל אביב" />
                </div>
                
                <div className="flex gap-2">
                  <Button>שמור שינויים</Button>
                  <Button variant="outline">בטל</Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>הגדרות התראות</CardTitle>
                <CardDescription>
                  הגדר איך תרצה לקבל התראות
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">התראות בדוא״ל</p>
                    <p className="text-sm text-muted-foreground">
                      קבל התראות על שינויים במחירים ועדכונים
                    </p>
                  </div>
                  <Button variant="outline" size="sm">
                    הפעל
                  </Button>
                </div>
                
                <Separator />
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">התראות בווטסאפ</p>
                    <p className="text-sm text-muted-foreground">
                      קבל התראות מיידיות בווטסאפ
                    </p>
                  </div>
                  <Button variant="outline" size="sm">
                    הפעל
                  </Button>
                </div>
                
                <Separator />
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">התראות דחופות</p>
                    <p className="text-sm text-muted-foreground">
                      קבל התראות על עסקאות דחופות
                    </p>
                  </div>
                  <Button variant="outline" size="sm">
                    הפעל
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>סטטוס חשבון</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-green-500"></div>
                  <span className="text-sm font-medium">פעיל</span>
                </div>
                <div className="text-sm text-muted-foreground">
                  החשבון שלך פעיל ופועל כרגיל
                </div>
                <Button variant="outline" size="sm" className="w-full">
                  צפה בפרטי החשבון
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>חבילה נוכחית</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-2">
                  <Star className="h-4 w-4 text-yellow-500" />
                  <span className="text-sm font-medium">חבילה: Basic</span>
                </div>
                <div className="text-sm text-muted-foreground">
                  עד 25 נכסים במעקב
                </div>
                <Button variant="outline" size="sm" className="w-full">
                  שדרג חבילה
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>פעולות מהירות</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Shield className="h-4 w-4 ml-2" />
                  שנה סיסמה
                </Button>
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Key className="h-4 w-4 ml-2" />
                  מפתחות API
                </Button>
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Building className="h-4 w-4 ml-2" />
                  הגדרות חברה
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}
