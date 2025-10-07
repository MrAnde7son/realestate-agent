'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/button'
import { BadgeCheck, Circle, ChevronDown, ChevronUp } from 'lucide-react'
import { OnboardingState, getCompletionPct, isOnboardingComplete } from '@/onboarding/selectors'

const steps = [
  // { key: 'connectPayment', label: 'חיבור תשלום', href: '/billing' },
  { key: 'addAsset', label: 'הוסף נכס ראשון', href: '/assets' },
  { key: 'generateReport', label: 'צור דוח ראשון', href: '/reports' },
  { key: 'createAlert', label: 'צור התראה אחת', href: '/alerts' },
] as const

type Props = { state: OnboardingState }

export default function OnboardingChecklist({ state }: Props) {
  const pct = getCompletionPct(state)
  const [open, setOpen] = useState(!isOnboardingComplete(state))
  const completedCount = useMemo(() => steps.filter(step => state[step.key]).length, [state])

  // Hide the component when onboarding is complete
  if (isOnboardingComplete(state)) {
    return null
  }

  return (
    <Card className="mb-4 border shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 p-4">
        <div>
          <CardTitle className="text-base font-semibold text-foreground">רשימת משימות</CardTitle>
          <p className="text-xs text-muted-foreground">
            {completedCount === steps.length
              ? 'כל המשימות הושלמו'
              : `${completedCount}/${steps.length} הושלמו · ${pct}%`}
          </p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-muted-foreground hover:text-foreground sm:hidden"
          onClick={() => setOpen(prev => !prev)}
          aria-expanded={open}
          aria-controls="onboarding-checklist"
        >
          {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
      </CardHeader>
      <CardContent
        id="onboarding-checklist"
        className={`pt-0 transition-all duration-200 ease-in-out ${open ? 'block' : 'hidden sm:block'}`}
      >
        <ul className="flex flex-col gap-2">
          {steps.map(step => {
            const completed = state[step.key]

            return (
              <li key={step.key}>
                <Link
                  href={step.href}
                  className={`group flex w-full items-center justify-between gap-3 rounded-xl border px-4 py-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background sm:py-2.5 ${
                    completed
                      ? 'border-emerald-200 bg-emerald-50 text-emerald-700 line-through dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300'
                      : 'border-border bg-background text-foreground hover:border-primary/40 hover:bg-primary/5'
                  }`}
                >
                  <span className="flex items-center gap-3">
                    <span
                      className={`flex h-8 w-8 items-center justify-center rounded-full border-2 ${
                        completed
                          ? 'border-emerald-500 bg-emerald-500 text-white'
                          : 'border-muted-foreground/40 text-muted-foreground'
                      }`}
                      aria-hidden="true"
                    >
                      {completed ? (
                        <BadgeCheck className="h-4 w-4" />
                      ) : (
                        <Circle className="h-4 w-4" />
                      )}
                    </span>
                    <span>{step.label}</span>
                  </span>
                  <span
                    className={`text-xs font-medium transition-opacity group-hover:opacity-100 ${
                      completed ? 'text-emerald-700 dark:text-emerald-300' : 'text-muted-foreground'
                    }`}
                  >
                    {completed ? 'בוצע' : 'התחל'}
                  </span>
                </Link>
              </li>
            )
          })}
        </ul>
      </CardContent>
    </Card>
  )
}
