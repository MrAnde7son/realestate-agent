'use client'

import React from 'react'
import * as Tooltip from '@radix-ui/react-tooltip'
import { Building2, FileText, Bell /*, CreditCard*/ } from 'lucide-react'
import { OnboardingState, getCompletionPct } from '@/onboarding/selectors'

const steps = [
  // { key: 'connectPayment', label: 'Connect Payment', icon: CreditCard },
  { key: 'addAsset', label: 'Add First Asset', icon: Building2, tooltip: 'Start by adding your first property' },
  { key: 'generateReport', label: 'Generate First Report', icon: FileText, tooltip: 'Click here to create your first report' },
  { key: 'createAlert', label: 'Create One Alert', icon: Bell },
] as const

type Step = typeof steps[number]
interface Props { state: OnboardingState }

export default function OnboardingProgress({ state }: Props) {
  const pct = getCompletionPct(state)
  if (pct === 100) {
    return <div className="mb-6 text-sm font-medium">All set ✅</div>
  }

  const firstIncomplete = steps.findIndex(s => !state[s.key])

  return (
    <div className="mb-6">
      <div className="flex items-start justify-between mb-2">
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
            <div className="flex flex-col items-center text-center w-full">
              <div className={`mb-1 p-2 rounded-full border ${border}`}>
                <step.icon className="h-4 w-4" />
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
