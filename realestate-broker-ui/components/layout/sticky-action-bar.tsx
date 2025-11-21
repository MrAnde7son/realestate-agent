import React from 'react'
import { cn } from '@/lib/utils'

interface StickyActionBarProps {
  children: React.ReactNode
  description?: React.ReactNode
  className?: string
  innerClassName?: string
}

export function StickyActionBar({
  children,
  description,
  className,
  innerClassName
}: StickyActionBarProps) {
  return (
    <div
      className={cn('sticky top-3 z-30', className)}
      data-testid="sticky-action-bar"
    >
      <div
        className={cn(
          'flex flex-col gap-2 rounded-2xl border border-border/70 bg-background/90 px-3 py-2 shadow-lg shadow-black/5 backdrop-blur supports-[backdrop-filter]:backdrop-blur',
          'sm:flex-row sm:items-center sm:justify-between',
          innerClassName
        )}
      >
        {description ? (
          <div className="text-xs text-muted-foreground hidden sm:block">{description}</div>
        ) : null}
        <div className="w-full sm:w-auto flex justify-end">{children}</div>
      </div>
    </div>
  )
}
