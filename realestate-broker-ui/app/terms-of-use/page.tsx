"use client"

import React from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'

type TermsSection =
  | {
      title: string
      list: string[]
      description?: never
    }
  | {
      title: string
      description: string
      list?: never
    }

const LAST_UPDATED = '6 באוקטובר 2025'

const SECTIONS: TermsSection[] = [
  {
    title: '1. מטרת האתר',
    description:
      'Nadlaner הוא פלטפורמה מקוונת המספקת למשתמשים מידע, ניתוחים והערכות שווי לנכסים בישראל, בהתבסס על מקורות מידע ציבוריים ופרטיים, לרבות מאגרי נדל״ן ממשלתיים, נתוני שוק ותוכן גולשים.',
  },
  {
    title: '2. שימוש באתר',
    list: [
      'האתר מיועד לשימוש אישי בלבד ואינו מהווה ייעוץ משפטי, שמאי, פיננסי או אחר.',
      'המשתמש מצהיר כי הוא בגיר (מעל גיל 18) ומוסמך להתקשר בהסכם זה.',
      'אין לעשות שימוש באתר לצורך ביצוע עבירה, פגיעה בזכויות צדדים שלישיים, או פעולה העלולה לפגוע בפעילות האתר.',
      'המפעיל רשאי להגביל או לחסום גישה למשתמשים לפי שיקול דעתו.',
    ],
  },
  {
    title: '3. אחריות מוגבלת',
    list: [
      'השירותים באתר ניתנים ״כמות שהם״ (AS IS) ללא אחריות מכל סוג.',
      'המידע עשוי להתבסס על מקורות חיצוניים (כגון govmap, nadlan.gov, MAVAT) ולכן ייתכנו טעויות, עיכובים או אי-דיוקים.',
      'המפעיל לא יישא באחריות לכל נזק ישיר או עקיף, הפסד כספי או תביעה הנובעים מהסתמכות על מידע באתר.',
      'המשתמש אחראי הבלעדי לבדוק את המידע מול מקורות מוסמכים לפני קבלת החלטות.',
    ],
  },
  {
    title: '4. קניין רוחני',
    list: [
      'כל זכויות היוצרים והקניין הרוחני באתר, לרבות עיצוב, קוד, טקסטים, לוגו, תוכן, תמונות ואלגוריתמים — שייכים למפעיל בלבד.',
      'אין לשכפל, להעתיק, להפיץ או לעשות שימוש מסחרי כלשהו בתכנים ללא רשות בכתב.',
      'סימני מסחר ושמות מסחריים שייכים לבעליהם החוקיים.',
    ],
  },
  {
    title: '5. תוכן משתמשים',
    list: [
      'המשתמש אחראי לכל תוכן שהוא מעלה לאתר (כגון הערות, טפסים או קבצים).',
      'המשתמש מצהיר שהתוכן אינו מפר זכויות יוצרים או דין כלשהו.',
      'המפעיל רשאי להסיר תוכן לפי שיקול דעתו.',
    ],
  },
  {
    title: '6. שינוי והפסקת השירות',
    list: [
      'המפעיל רשאי לשנות את מבנה האתר, תוכנו או השירותים המוצעים בו, בכל עת, ללא הודעה מוקדמת.',
      'המפעיל רשאי להפסיק את פעילות האתר באופן זמני או קבוע.',
      'במקרה של שינוי מהותי בתנאי השימוש, תפורסם הודעה באתר.',
    ],
  },
  {
    title: '7. שיפוי',
    description:
      'המשתמש מתחייב לשפות את המפעיל בגין כל נזק, תביעה או הוצאה (כולל שכר טרחת עו״ד) הנובעים מהפרת תנאי שימוש אלה או מפעולה אסורה מצד המשתמש.',
  },
  {
    title: '8. הדין החל וסמכות השיפוט',
    description:
      'הדין החל הוא הדין הישראלי בלבד, וסמכות השיפוט הבלעדית נתונה לבתי המשפט המוסמכים בעיר תל-אביב-יפו.',
  },
]

export default function TermsOfUsePage() {
  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader heading="🧾 תנאי שימוש באתר Nadlaner" text={`עודכן לאחרונה: ${LAST_UPDATED}`} />
        <div className="space-y-6 text-sm leading-6">
          <p>
            ברוך הבא לאתר Nadlaner (״האתר״), המופעל על ידי איתמר מזרחי (״המפעיל״, ״אנחנו״).
            השימוש באתר ובשירותיו כפוף לתנאים המפורטים להלן. השימוש באתר מהווה הסכמה לכל תנאי השימוש.
            אם אינך מסכים – אנא הימנע מלהשתמש באתר.
          </p>

          {SECTIONS.map((section) => (
            <Card key={section.title}>
              <CardHeader>
                <CardTitle>{section.title}</CardTitle>
              </CardHeader>
              <CardContent>
                {'list' in section ? (
                  <ul className="list-disc pr-5 space-y-2">
                    {section.list.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p>{section.description}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}
