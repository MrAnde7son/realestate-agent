"use client"

import React from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

export default function UserGuidePage() {
  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader heading="מדריך משתמש" />
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>התחלה מהירה</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p>ברוכים הבאים למערכת ניהול הנדל&quot;ן. כאן תוכלו לנהל נכסים, לעקוב אחרי התראות ולבצע פעולות נוספות.</p>
              <p>להתחלה, היכנסו לתפריט &quot;נכסים&quot; והוסיפו נכס חדש באמצעות כפתור &quot;נכס חדש&quot;.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>חיפוש וניהול נכסים</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p>בתצוגת הנכסים ניתן לחפש לפי עיר, מחיר או סוג הנכס. לחיצה על נכס תפתח את פרטי הנכס ופעולות נוספות.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>התראות ותקשורת</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p>המערכת שולחת התראות במייל או בוואטסאפ לפי ההעדפות שלכם. ניתן לעדכן את ההגדרות בעמוד &quot;הגדרות&quot;.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>ניהול חשבון</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p>עדכון פרטי משתמש, שינוי שפה והגדרות נוספות נעשים דרך עמודי &quot;פרופיל&quot; ו&quot;הגדרות&quot;.</p>
            </CardContent>
          </Card>
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}

