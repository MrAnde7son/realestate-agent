'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import confetti from 'canvas-confetti'
import { useAuth } from '@/lib/auth-context'
import { authAPI, OnboardingStatus } from '@/lib/auth'

const steps = [
  { key: 'connect_payment', label: 'Connect payment', href: '/billing' },
  { key: 'add_first_asset', label: 'Add first asset', href: '/assets/new' },
  { key: 'generate_first_report', label: 'Generate first report', href: '/reports/new' },
  { key: 'set_one_alert', label: 'Set one alert', href: '/alerts/new' },
] as const

type StepKey = typeof steps[number]['key']

export default function OnboardingChecklist() {
  const { isAuthenticated } = useAuth()
  const [status, setStatus] = useState<OnboardingStatus | null>(null)
  const [celebrated, setCelebrated] = useState(false)

  useEffect(() => {
    if (!isAuthenticated) return
    authAPI
      .getOnboardingStatus()
      .then(setStatus)
      .catch(err => console.error('Failed to load onboarding status', err))
  }, [isAuthenticated])

  useEffect(() => {
    if (status?.completed && !celebrated) {
      confetti({ spread: 70, origin: { y: 0.6 } })
      setCelebrated(true)
    }
  }, [status, celebrated])

  if (!isAuthenticated || !status || status.completed) return null

  const completedCount = Object.values(status.steps).filter(Boolean).length

  return (
    <div className="fixed bottom-4 right-4 bg-white dark:bg-gray-800 shadow-lg rounded-lg p-4 w-72 z-50">
      <h3 className="text-lg font-semibold mb-2">Get Started</h3>
      <div className="text-sm text-gray-600 mb-2">{completedCount} of 4 completed</div>
      <div className="w-full bg-gray-200 h-2 rounded mb-4">
        <div
          className="h-2 bg-blue-500 rounded"
          style={{ width: `${(completedCount / 4) * 100}%` }}
        />
      </div>
      <ul className="space-y-2">
        {steps.map(step => (
          <li key={step.key} className="flex items-center">
            <input
              type="checkbox"
              className="mr-2"
              checked={status.steps[step.key as StepKey]}
              readOnly
            />
            <Link
              href={step.href}
              className={`text-sm ${
                status.steps[step.key as StepKey]
                  ? 'line-through text-gray-500'
                  : ''
              }`}
            >
              {step.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

