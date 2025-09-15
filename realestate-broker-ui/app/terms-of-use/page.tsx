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
          <p>
            ברוך הבא ל־Nadlaner.com (&quot;האתר&quot;). שימוש באתר ובשירותים הניתנים בו מהווה
            הסכמה מלאה לתנאים המפורטים להלן. אם אינך מסכים לתנאים אלה – אנא הימנע
            משימוש באתר.
          </p>

          <Card>
            <CardHeader>
              <CardTitle>הגדרות</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc pl-5 space-y-1">
                <li>&quot;האתר&quot; – Nadlaner.com וכל התכנים והשירותים הכלולים בו.</li>
                <li>&quot;משתמש&quot; – כל אדם הגולש או עושה שימוש באתר.</li>
                <li>
                  &quot;שירותים&quot; – כלים, מחשבונים, דוחות, מידע ונתונים המוצגים באתר.
                </li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>מטרת האתר</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                האתר נועד לספק למתווכים, שמאים, משקיעים ומשתמשים פרטיים מידע, ניתוחים
                וכלים בתחום הנדל&quot;ן. אין לראות במידע המופיע באתר ייעוץ משפטי, פיננסי או
                מקצועי מחייב.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>שימוש מותר</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                המשתמש מתחייב להשתמש באתר בהתאם לדין, בתום לב ולמטרות אישיות בלבד. אין
                להעתיק, לשכפל, להפיץ, למכור, לשדר או לפרסם מידע ונתונים מהאתר ללא אישור
                מראש ובכתב מהנהלת האתר.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>אחריות מוגבלת</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc pl-5 space-y-1">
                <li>
                  המידע באתר נאסף ממקורות שונים (כגון מאגרי מידע ציבוריים, ממשלתיים ואתרים
                  חיצוניים).
                </li>
                <li>
                  האתר עושה מאמצים לשמור על דיוק המידע, אך ייתכנו טעויות, אי־עדכונים או
                  שגיאות.
                </li>
                <li>
                  הנהלת האתר אינה אחראית לכל נזק שייגרם עקב הסתמכות על המידע או השירותים
                  באתר.
                </li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>הרשמה ושירותים בתשלום</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                חלק מהשירותים באתר ניתנים ללא תשלום וחלקם כרוכים בהרשמה או בתשלום דמי
                מנוי. הנהלת האתר רשאית לשנות את מחירי המנויים או את תנאי השימוש בכל עת.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>פרטיות ושמירת מידע</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                האתר רשאי לאסוף מידע סטטיסטי ושימושי לצורך שיפור השירותים. מידע אישי
                שיימסר על ידי המשתמשים ישמר בהתאם למדיניות הפרטיות של האתר.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>קישורים לאתרים חיצוניים</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                האתר עשוי לכלול קישורים לאתרים חיצוניים. הנהלת האתר אינה אחראית לתוכן או
                למדיניות באתרים אלה.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>הפסקת שירות</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                הנהלת האתר רשאית להפסיק את פעילות האתר או לשנותו, באופן זמני או קבוע,
                ללא צורך במתן הודעה מוקדמת וללא אחריות כלשהי כלפי המשתמשים.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>שיפוי</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                המשתמש מתחייב לשפות את הנהלת האתר בגין כל נזק, הפסד, תביעה או הוצאה
                שייגרמו לה עקב שימוש בניגוד לתנאי השימוש או בניגוד לדין.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>דין ושיפוט</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                תנאי שימוש אלה כפופים לדיני מדינת ישראל. סמכות השיפוט הבלעדית בכל מחלוקת
                הנוגעת לתנאי שימוש אלו נתונה לבית המשפט המוסמך במחוז תל אביב.
              </p>
            </CardContent>
          </Card>
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}
