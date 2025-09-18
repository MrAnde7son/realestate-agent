'use client'

import React from 'react'
import * as Tooltip from '@radix-ui/react-tooltip'
import { Building2, FileText, Bell /*, CreditCard*/ } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { OnboardingState, getCompletionPct, isOnboardingComplete } from '@/onboarding/selectors'

interface Step {
  key: keyof OnboardingState
  label: string
  icon: LucideIcon
  tooltip?: string
}

const steps: Step[] = [
  // { key: 'connectPayment', label: 'חיבור תשלום', icon: CreditCard },
  {
    key: 'addAsset',
    label: 'הוסף נכס ראשון',
    icon: Building2,
    tooltip: 'התחל בהוספת הנכס הראשון שלך',
  },
  {
    key: 'generateReport',
    label: 'צור דוח ראשון',
    icon: FileText,
    tooltip: 'לחץ כאן כדי ליצור את הדוח הראשון שלך',
  },
  { key: 'createAlert', label: 'צור התראה אחת', icon: Bell },
]
interface Props { state: OnboardingState }

export default function OnboardingProgress({ state }: Props) {
  const pct = getCompletionPct(state)
  
  // Hide the component when onboarding is complete
  if (isOnboardingComplete(state)) {
    return null
  }

  const firstIncomplete = steps.findIndex(s => !state[s.key])

  return (
    <div className="mb-4 p-4 bg-muted/30 rounded-lg border">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-foreground">התקדמות התחלת העבודה</h3>
        <span className="text-xs text-muted-foreground">{pct}% הושלם</span>
      </div>
      <div className="flex items-center justify-between mb-2">
        {steps.map((step: Step, idx) => {
          const completed = state[step.key]
          const active = idx === firstIncomplete
          const border = completed
            ? 'border-green-500 bg-green-500 text-white'
            : active
              ? 'border-primary text-primary'
              : 'border-muted text-muted-foreground'
          const labelColor = completed
            ? 'text-green-600'
            : active
              ? 'text-primary'
              : 'text-muted-foreground'

          const icon = (
            <div className="flex flex-col items-center text-center flex-1">
              <div className={`mb-1 p-1.5 rounded-full border ${border}`}>
                <step.icon className="h-3 w-3" />
              </div>
              <span className={`text-xs ${labelColor}`}>{step.label}</span>
            </div>
          )

          if (step.tooltip && !completed) {
            return (
              <Tooltip.Provider key={step.key} delayDuration={0}>
                <Tooltip.Root>
                  <Tooltip.Trigger asChild>{icon}</Tooltip.Trigger>
                  <Tooltip.Content sideOffset={4} className="rounded bg-gray-900 text-white px-2 py-1 text-xs">
                    {step.tooltip}
                  </Tooltip.Content>
                </Tooltip.Root>
              </Tooltip.Provider>
            )
          }
          return <div key={step.key}>{icon}</div>
        })}
      </div>
      <div className="w-full h-1 bg-muted rounded">
        <div className="h-1 bg-primary rounded" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
