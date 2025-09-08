'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { OnboardingState, getCompletionPct } from '@/onboarding/selectors'

const steps = [
  // { key: 'connectPayment', label: 'חיבור תשלום', href: '/billing' },
  { key: 'addAsset', label: 'הוסף נכס ראשון', href: '/assets' },
  { key: 'generateReport', label: 'צור דוח ראשון', href: '/reports' },
  { key: 'createAlert', label: 'צור התראה אחת', href: '/alerts' },
] as const

type Props = { state: OnboardingState }

export default function OnboardingChecklist({ state }: Props) {
  const pct = getCompletionPct(state)
  const [open, setOpen] = useState(pct !== 100)

  return (
    <Card className="mb-6">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg font-semibold">בוא נתחיל</CardTitle>
        {pct === 100 && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setOpen(o => !o)}
            className="h-6 w-6"
          >
            {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            <span className="sr-only">הצג/הסתר רשימת משימות</span>
          </Button>
        )}
      </CardHeader>
      {open && (
        <CardContent className="pt-0">
          <ul className="space-y-2">
            {steps.map(step => (
              <li key={step.key} className="flex items-center">
                <input type="checkbox" className="mr-2" checked={state[step.key]} readOnly />
                <Link
                  href={step.href}
                  className={`text-sm ${state[step.key] ? 'line-through text-muted-foreground' : ''}`}
                >
                  {step.label}
                </Link>
              </li>
            ))}
          </ul>
        </CardContent>
      )}
      {pct === 100 && !open && (
        <CardContent className="pt-0">
          <Button
            variant="link"
            size="sm"
            className="p-0 h-auto"
            onClick={() => setOpen(true)}
          >
            הצג צעדים שהושלמו
          </Button>
        </CardContent>
      )}
    </Card>
  )
}
