'use client'

import * as React from 'react'
import { Loader2, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'

export interface LoadingStateProps {
  variant?: 'spinner' | 'skeleton' | 'inline'
  message?: string
  description?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
  fullScreen?: boolean
}

/**
 * Standardized loading state component
 * Use this for consistent loading patterns across the application
 */
export function LoadingState({
  variant = 'spinner',
  message = 'טוען...',
  description,
  size = 'md',
  className,
  fullScreen = false,
}: LoadingStateProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  }

  if (variant === 'skeleton') {
    return (
      <div className={cn('space-y-4', className)}>
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-4 w-2/3" />
      </div>
    )
  }

  if (variant === 'inline') {
    return (
      <div className={cn('flex items-center gap-2', className)} role="status" aria-live="polite">
        <Loader2 className={cn('animate-spin text-primary', sizeClasses[size])} aria-hidden="true" />
        <span className="text-sm text-muted-foreground">{message}</span>
      </div>
    )
  }

  const content = (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-4',
        fullScreen ? 'min-h-screen' : 'py-12',
        className
      )}
      role="status"
      aria-live="polite"
      aria-label={message}
    >
      <Loader2 className={cn('animate-spin text-primary', sizeClasses[size])} aria-hidden="true" />
      <div className="text-center space-y-2">
        <p className="text-sm font-medium text-foreground">{message}</p>
        {description && (
          <p className="text-xs text-muted-foreground max-w-md">{description}</p>
        )}
      </div>
    </div>
  )

  return content
}

/**
 * Table loading state with skeleton rows
 */
export interface TableLoadingStateProps {
  rowCount?: number
  columnCount?: number
  className?: string
}

export function TableLoadingState({
  rowCount = 5,
  columnCount = 6,
  className,
}: TableLoadingStateProps) {
  return (
    <>
      {Array.from({ length: rowCount }).map((_, rowIndex) => (
        <tr key={`loading-row-${rowIndex}`} data-testid="table-skeleton-row">
          {Array.from({ length: columnCount }).map((_, colIndex) => (
            <td key={`loading-cell-${rowIndex}-${colIndex}`} className="py-4">
              <Skeleton className="h-4 w-20" />
            </td>
          ))}
        </tr>
      ))}
    </>
  )
}

/**
 * Card grid loading state
 */
export interface CardGridLoadingStateProps {
  count?: number
  className?: string
}

export function CardGridLoadingState({
  count = 3,
  className,
}: CardGridLoadingStateProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <div key={`loading-card-${index}`} className={className}>
          <div className="rounded-lg border bg-card p-4 space-y-3">
            <Skeleton className="h-48 w-full rounded-md" />
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <div className="flex gap-2">
              <Skeleton className="h-6 w-16" />
              <Skeleton className="h-6 w-20" />
            </div>
          </div>
        </div>
      ))}
    </>
  )
}

