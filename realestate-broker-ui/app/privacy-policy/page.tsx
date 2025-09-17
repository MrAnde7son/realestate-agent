"use client"

import React from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'

export default function PrivacyPolicyPage() {
  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader heading="מדיניות פרטיות" />
        <div className="space-y-6 text-sm leading-6">
          <p>
            נדל"נר מכבד את פרטיות המשתמשים ומחויב להגן על המידע האישי שמועבר אלינו. 
            מדיניות פרטיות זו מסבירה כיצד אנו אוספים, משתמשים ומגנים על המידע שלך.
          </p>

          <Card>
            <CardHeader>
              <CardTitle>איסוף מידע</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc pl-5 space-y-1">
                <li><strong>מידע אישי:</strong> שם, כתובת אימייל, מספר טלפון ופרטי תשלום</li>
                <li><strong>מידע שימוש:</strong> נתונים על השימוש בפלטפורמה, דפים שנצפו ופעולות שבוצעו</li>
                <li><strong>מידע טכני:</strong> כתובת IP, סוג דפדפן, מערכת הפעלה וזמן גישה</li>
                <li><strong>מידע נדל"ן:</strong> כתובות נכסים, פרטי עסקאות ונתונים פיננסיים</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>שימוש במידע</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc pl-5 space-y-1">
                <li>מתן שירותי הפלטפורמה והתאמה אישית</li>
                <li>עיבוד תשלומים וניהול חשבונות</li>
                <li>שיפור השירותים ופיתוח תכונות חדשות</li>
                <li>תקשורת עם המשתמשים (עדכונים, תמיכה טכנית)</li>
                <li>אנליטיקה וסטטיסטיקות שימוש</li>
                <li>עמידה בחובות משפטיות ורגולטוריות</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>שיתוף מידע</CardTitle>
            </CardHeader>
            <CardContent>
              <p>אנו לא מוכרים, משכירים או חושפים מידע אישי לצדדים שלישיים, למעט:</p>
              <ul className="list-disc pl-5 space-y-1 mt-2">
                <li>ספקי שירותים מהימנים המסייעים לנו להפעיל את הפלטפורמה</li>
                <li>כאשר נדרש על פי חוק או צו בית משפט</li>
                <li>כדי להגן על זכויותינו, רכושנו או בטיחות המשתמשים</li>
                <li>עם הסכמה מפורשת מהמשתמש</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>אבטחת מידע</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc pl-5 space-y-1">
                <li>הצפנה מתקדמת של נתונים רגישים</li>
                <li>גישה מוגבלת למידע אישי רק לעובדים מורשים</li>
                <li>מערכות אבטחה מתקדמות ומניטור 24/7</li>
                <li>גיבויים קבועים ומוגנים של הנתונים</li>
                <li>עדכונים שוטפים של מערכות האבטחה</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>זכויות המשתמש</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc pl-5 space-y-1">
                <li><strong>גישה למידע:</strong> זכות לקבל עותק של המידע האישי שלך</li>
                <li><strong>תיקון מידע:</strong> זכות לתקן מידע שגוי או לא מעודכן</li>
                <li><strong>מחיקת מידע:</strong> זכות לבקש מחיקת המידע האישי שלך</li>
                <li><strong>הגבלת עיבוד:</strong> זכות להגביל את השימוש במידע שלך</li>
                <li><strong>ניידות נתונים:</strong> זכות לקבל את המידע שלך בפורמט מועבר</li>
                <li><strong>התנגדות:</strong> זכות להתנגד לעיבוד המידע שלך למטרות שיווק</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>עוגיות (Cookies)</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                אנו משתמשים בעוגיות כדי לשפר את חוויית המשתמש, לנתח תנועה באתר 
                ולספק תוכן מותאם אישית. ניתן להגדיר את הדפדפן לדחות עוגיות, 
                אך הדבר עלול להשפיע על תפקוד הפלטפורמה.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>שינויים במדיניות</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                אנו רשאים לעדכן מדיניות פרטיות זו מעת לעת. שינויים משמעותיים 
                יפורסמו באתר ויישלחו הודעה למשתמשים רשומים. מומלץ לבדוק 
                מדיניות זו באופן קבוע.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>יצירת קשר</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                לשאלות או בקשות הקשורות לפרטיות, ניתן לפנות אלינו:
              </p>
              <ul className="list-disc pl-5 space-y-1 mt-2">
                <li>דרך טופס "צור קשר" באפליקציה</li>
                <li>בדף ההגדרות תחת "עזרה ותמיכה"</li>
                <li>בדוא"ל: privacy@nadlaner.com</li>
              </ul>
            </CardContent>
          </Card>

          <div className="text-xs text-neutral-500 mt-8">
            <p>עדכון אחרון: ינואר 2025</p>
            <p>מדיניות זו נכנסה לתוקף: ינואר 2025</p>
          </div>
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}
