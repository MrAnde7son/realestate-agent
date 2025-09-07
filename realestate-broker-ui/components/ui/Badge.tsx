import React, { type HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

const variants: Record<BadgeVariant, string> = {
  primary: 'bg-primary text-white',
  accent: 'bg-accent text-white',
  success: 'bg-success text-white',
  warning: 'bg-warning text-black',
  error: 'bg-error text-white',
  neutral:
    'bg-neutral-200 text-neutral-800 dark:bg-neutral-700 dark:text-neutral-200',
}

export type BadgeVariant =
  | 'success'
  | 'warning'
  | 'error'
  | 'neutral'
  | 'accent'
  | 'primary'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
}

export function Badge({
  variant = 'neutral',
  className,
  ...props
}: BadgeProps) {
  return (
    <span
      data-slot="badge"
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        variants[variant],
        className
      )}
      {...props}
    />
  )
}

export default Badge
