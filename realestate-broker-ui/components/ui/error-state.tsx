'use client'

import * as React from 'react'
import { AlertCircle, RefreshCw, Home } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

export interface ErrorStateProps {
  title?: string
  message?: string
  error?: Error | string
  onRetry?: () => void
  retryLabel?: string
  showHomeButton?: boolean
  className?: string
}

/**
 * Standardized error state component
 * Use this for consistent error handling across the application
 */
export function ErrorState({
  title = 'אירעה שגיאה',
  message = 'משהו השתבש. אנא נסה שוב מאוחר יותר.',
  error,
  onRetry,
  retryLabel = 'נסה שוב',
  showHomeButton = false,
  className,
}: ErrorStateProps) {
  const errorMessage = error instanceof Error ? error.message : error

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-4 py-12 px-4',
        className
      )}
      role="alert"
      aria-live="assertive"
    >
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
        <AlertCircle className="h-8 w-8 text-destructive" aria-hidden="true" />
      </div>
      <div className="text-center space-y-2">
        <h3 className="text-lg font-semibold text-foreground">{title}</h3>
        <p className="text-sm text-muted-foreground max-w-md">{message}</p>
        {errorMessage && (
          <p className="text-xs text-muted-foreground/70 font-mono max-w-md break-words">
            {errorMessage}
          </p>
        )}
      </div>
      <div className="flex gap-2 mt-2">
        {onRetry && (
          <Button onClick={onRetry} variant="default">
            <RefreshCw className="h-4 w-4 ms-2" aria-hidden="true" />
            {retryLabel}
          </Button>
        )}
        {showHomeButton && (
          <Button asChild variant="outline">
            <Link href="/assets">
              <Home className="h-4 w-4 ms-2" aria-hidden="true" />
              חזרה לדף הבית
            </Link>
          </Button>
        )}
      </div>
    </div>
  )
}

/**
 * Inline error state for forms and smaller components
 */
export interface InlineErrorStateProps {
  message: string
  className?: string
}

export function InlineErrorState({
  message,
  className,
}: InlineErrorStateProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-2 text-sm text-destructive',
        className
      )}
      role="alert"
      aria-live="polite"
    >
      <AlertCircle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
      <span>{message}</span>
    </div>
  )
}

