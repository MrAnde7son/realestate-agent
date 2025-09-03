'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import confetti from 'canvas-confetti'
import { X } from 'lucide-react'

import { useAuth } from '@/lib/auth-context'
import { authAPI, OnboardingStatus } from '@/lib/auth'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const steps = [
  { key: 'add_first_asset', label: 'Add first asset', href: '/assets' },
  { key: 'generate_first_report', label: 'Generate first report', href: '/reports' },
  { key: 'set_one_alert', label: 'Set one alert', href: '/alerts' },
] as const

export default function OnboardingChecklist() {
  const { isAuthenticated } = useAuth()
  const [status, setStatus] = useState<OnboardingStatus | null>(null)
  const [celebrated, setCelebrated] = useState(false)
  const [dismissed, setDismissed] = useState(false)

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

  useEffect(() => {
    const stored = localStorage.getItem('onboardingDismissed')
    if (stored === 'true') setDismissed(true)
  }, [])

  const handleClose = () => {
    setDismissed(true)
    localStorage.setItem('onboardingDismissed', 'true')
  }

  if (!isAuthenticated || !status || status.completed || dismissed) return null

  const completedCount = steps.filter(step => status.steps[step.key]).length
  const total = steps.length

  return (
    <Card className="fixed bottom-4 right-4 w-72 z-50 p-4">
      <CardHeader className="p-0 pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-lg font-semibold">Get Started</CardTitle>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleClose}
          className="h-6 w-6"
        >
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="text-sm text-muted-foreground mb-2">
          {completedCount} of {total} completed
        </div>
        <div className="w-full bg-muted h-2 rounded mb-4">
          <div
            className="h-2 bg-primary rounded"
            style={{ width: `${(completedCount / total) * 100}%` }}
          />
        </div>
        <ul className="space-y-2">
          {steps.map(step => (
            <li key={step.key} className="flex items-center">
              <input
                type="checkbox"
                className="mr-2"
                checked={status.steps[step.key]}
                readOnly
              />
              <Link
                href={step.href}
                className={`text-sm ${
                  status.steps[step.key]
                    ? 'line-through text-muted-foreground'
                    : ''
                }`}
              >
                {step.label}
              </Link>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}

