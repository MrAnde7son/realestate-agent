"use client"

import React from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'

export default function TermsOfUsePage() {
  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader heading="תנאי שימוש" />
        <div className="space-y-6 text-sm leading-6">
          <Card>
            <CardHeader>
              <CardTitle>כללי</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p>ברוכים הבאים לאתר נדלנר (להלן: &quot;החברה&quot;).</p>
              <p>השימוש באתר וכל שירותיו כפוף לקבלת תנאי שימוש אלו והתחייבותך לפעול לפיהם.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>הגבלת אחריות</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p>השירותים והמידע באתר ניתנים כפי שהם (&quot;AS IS&quot;), ללא כל אחריות לגבי נכונותם או התאמתם.</p>
              <p>כל החלטה שתתקבל על סמך המידע באתר הינה באחריות המשתמש בלבד.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>קניין רוחני</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p>כל זכויות הקניין הרוחני בתכני האתר, לרבות עיצובו והקוד, שייכות לחברה בלבד.</p>
              <p>אין להעתיק, לשכפל או להפיץ כל חלק מהאתר ללא קבלת רשות מראש ובכתב מהחברה.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>שימוש בפורום</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p>הפורום באתר נועד לשיתוף מידע בלבד. החברה אינה אחראית לתוכן שיתפרסם בו.</p>
              <p>המשתמש מתחייב להימנע מפרסום תוכן בלתי חוקי או פוגעני.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>פרטיות</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p>החברה עשויה לאסוף מידע הנובע מהשימוש באתר לצורכי שיפור השירותים.</p>
              <p>השימוש במידע ייעשה בהתאם למדיניות הפרטיות של החברה.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>אבטחת מידע</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p>החברה פועלת להגן על המידע באתר אך אינה יכולה להבטיח חסינות מוחלטת מפני פריצות.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>תחולת הדין</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p>על השימוש באתר יחולו דיני מדינת ישראל והסמכות הבלעדית תהיה לבתי המשפט בתל אביב-יפו.</p>
            </CardContent>
          </Card>
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}
