"use client"
import React, { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Globe, Bell, Shield, Palette, Database, Zap } from 'lucide-react'

interface UserSettings {
  language: string
  timezone: string
  currency: string
  date_format: string
  notify_email: boolean
  notify_whatsapp: boolean
  notify_urgent: boolean
  notification_time: string
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<UserSettings>({
    language: 'en',
    timezone: 'UTC',
    currency: 'usd',
    date_format: 'yyyy-mm-dd',
    notify_email: true,
    notify_whatsapp: false,
    notify_urgent: true,
    notification_time: '09:00'
  })

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch('/api/settings/')
        if (res.ok) {
          const data = await res.json()
          setSettings(data)
        }
      } catch (err) {
        console.error('Failed to load settings', err)
      }
    }
    load()
  }, [])

  const handleSave = async () => {
    try {
      const res = await fetch('/api/settings/', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      })
      if (!res.ok) {
        throw new Error('Failed to save settings')
      }
      alert('Settings saved successfully')
    } catch (err) {
      console.error('Failed to save settings', err)
      alert('Failed to save settings')
    }
  }

  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader
          heading="הגדרות מערכת" 
          text="התאם את המערכת לצרכים שלך" 
        />
        
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
          {/* Main Settings */}
          <div className="lg:col-span-2 space-y-6">
            {/* General Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="h-5 w-5" />
                  הגדרות כלליות
                </CardTitle>
                <CardDescription>
                  הגדרות בסיסיות למערכת
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="language">שפה</Label>
                    <Select value={settings.language} onValueChange={(v) => setSettings({ ...settings, language: v })}>
                      <SelectTrigger>
                        <SelectValue placeholder="בחר שפה" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="he">עברית</SelectItem>
                        <SelectItem value="en">English</SelectItem>
                        <SelectItem value="ar">العربية</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="timezone">אזור זמן</Label>
                    <Select value={settings.timezone} onValueChange={(v) => setSettings({ ...settings, timezone: v })}>
                      <SelectTrigger>
                        <SelectValue placeholder="בחר אזור זמן" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Asia/Jerusalem">אסיה/ירושלים</SelectItem>
                        <SelectItem value="UTC">UTC</SelectItem>
                        <SelectItem value="Europe/London">אירופה/לונדון</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="currency">מטבע</Label>
                    <Select value={settings.currency} onValueChange={(v) => setSettings({ ...settings, currency: v })}>
                      <SelectTrigger>
                        <SelectValue placeholder="בחר מטבע" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ils">שקל ישראלי (₪)</SelectItem>
                        <SelectItem value="usd">דולר אמריקאי ($)</SelectItem>
                        <SelectItem value="eur">אירו (€)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="dateFormat">פורמט תאריך</Label>
                    <Select value={settings.date_format} onValueChange={(v) => setSettings({ ...settings, date_format: v })}>
                      <SelectTrigger>
                        <SelectValue placeholder="בחר פורמט תאריך" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="dd-mm-yyyy">DD/MM/YYYY</SelectItem>
                        <SelectItem value="mm-dd-yyyy">MM/DD/YYYY</SelectItem>
                        <SelectItem value="yyyy-mm-dd">YYYY/MM/DD</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Notification Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5" />
                  הגדרות התראות
                </CardTitle>
                <CardDescription>
                  הגדר איך ומתי לקבל התראות
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
                  <Switch checked={settings.notify_email} onCheckedChange={(v) => setSettings({ ...settings, notify_email: v })} />
                </div>
                
                <Separator />
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">התראות בווטסאפ</p>
                    <p className="text-sm text-muted-foreground">
                      קבל התראות מיידיות בווטסאפ
                    </p>
                  </div>
                  <Switch checked={settings.notify_whatsapp} onCheckedChange={(v) => setSettings({ ...settings, notify_whatsapp: v })} />
                </div>
                
                <Separator />
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">התראות דחופות</p>
                    <p className="text-sm text-muted-foreground">
                      קבל התראות על עסקאות דחופות
                    </p>
                  </div>
                  <Switch checked={settings.notify_urgent} onCheckedChange={(v) => setSettings({ ...settings, notify_urgent: v })} />
                </div>
                
                <Separator />
                
                <div className="space-y-2">
                  <Label htmlFor="notificationTime">שעת התראות יומיות</Label>
                  <Select value={settings.notification_time} onValueChange={(v) => setSettings({ ...settings, notification_time: v })}>
                    <SelectTrigger>
                      <SelectValue placeholder="בחר שעה" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="08:00">08:00</SelectItem>
                      <SelectItem value="09:00">09:00</SelectItem>
                      <SelectItem value="10:00">10:00</SelectItem>
                      <SelectItem value="17:00">17:00</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* Security Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  הגדרות אבטחה
                </CardTitle>
                <CardDescription>
                  הגדרות אבטחה לחשבון שלך
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">אימות דו-שלבי</p>
                    <p className="text-sm text-muted-foreground">
                      הוסף שכבת אבטחה נוספת לחשבון שלך
                    </p>
                  </div>
                  <Switch />
                </div>
                
                <Separator />
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">התראות כניסה</p>
                    <p className="text-sm text-muted-foreground">
                      קבל התראה בכל כניסה לחשבון
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
                
                <Separator />
                
                <div className="space-y-2">
                  <Label htmlFor="sessionTimeout">זמן פגירת סשן (דקות)</Label>
                  <Select defaultValue="30">
                    <SelectTrigger>
                      <SelectValue placeholder="בחר זמן" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="15">15 דקות</SelectItem>
                      <SelectItem value="30">30 דקות</SelectItem>
                      <SelectItem value="60">שעה</SelectItem>
                      <SelectItem value="120">שעתיים</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* Data Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  הגדרות נתונים
                </CardTitle>
                <CardDescription>
                  הגדרות לניהול הנתונים שלך
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">גיבוי אוטומטי</p>
                    <p className="text-sm text-muted-foreground">
                      גבה את הנתונים שלך אוטומטית
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
                
                <Separator />
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">סנכרון בין מכשירים</p>
                    <p className="text-sm text-muted-foreground">
                      סנכרן נתונים בין כל המכשירים שלך
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
                
                <Separator />
                
                <div className="space-y-2">
                  <Label htmlFor="backupFrequency">תדירות גיבוי</Label>
                  <Select defaultValue="daily">
                    <SelectTrigger>
                      <SelectValue placeholder="בחר תדירות" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="hourly">שעתי</SelectItem>
                      <SelectItem value="daily">יומי</SelectItem>
                      <SelectItem value="weekly">שבועי</SelectItem>
                      <SelectItem value="monthly">חודשי</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>פעולות מהירות</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Zap className="h-4 w-4 ml-2" />
                  ייצא הגדרות
                </Button>
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Database className="h-4 w-4 ml-2" />
                  ייצא נתונים
                </Button>
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Shield className="h-4 w-4 ml-2" />
                  היסטוריית אבטחה
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>מידע על המערכת</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">גרסה:</span>
                  <span>1.0.0</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">עדכון אחרון:</span>
                  <span>היום</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">סטטוס:</span>
                  <span className="text-green-500">מעודכן</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>עזרה ותמיכה</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Globe className="h-4 w-4 ml-2" />
                  מדריך משתמש
                </Button>
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Bell className="h-4 w-4 ml-2" />
                  צור קשר עם התמיכה
                </Button>
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Shield className="h-4 w-4 ml-2" />
                  דווח על באג
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end mt-6">
          <Button size="lg" onClick={handleSave}>שמור הגדרות</Button>
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}
