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
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-foreground">רשימת משימות</h3>
        {pct === 100 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setOpen(o => !o)}
            className="h-6 px-2 text-xs"
          >
            {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            <span className="sr-only">הצג/הסתר רשימת משימות</span>
          </Button>
        )}
      </div>
      {open && (
        <div className="bg-muted/30 rounded-lg p-3 border">
          <ul className="space-y-1.5">
            {steps.map(step => (
              <li key={step.key} className="flex items-center">
                <input type="checkbox" className="mr-2 h-3 w-3" checked={state[step.key]} readOnly />
                <Link
                  href={step.href}
                  className={`text-xs ${state[step.key] ? 'line-through text-muted-foreground' : 'text-foreground'}`}
                >
                  {step.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
      {pct === 100 && !open && (
        <div className="bg-muted/30 rounded-lg p-3 border">
          <Button
            variant="link"
            size="sm"
            className="p-0 h-auto text-xs"
            onClick={() => setOpen(true)}
          >
            הצג צעדים שהושלמו
          </Button>
        </div>
      )}
    </div>
  )
}
