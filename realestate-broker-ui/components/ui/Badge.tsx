import React from 'react'
import { cn } from '@/lib/utils'

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'neutral' | 'info' | 'secondary' | 'destructive' | 'outline' | 'accent'
  size?: 'sm' | 'md' | 'lg'
}

const badgeVariants = {
  default: 'bg-primary text-primary-foreground',
  success: 'bg-success text-success-foreground',
  warning: 'bg-warning text-warning-foreground',
  error: 'bg-error text-error-foreground',
  neutral: 'bg-neutral text-neutral-foreground',
  info: 'bg-info text-info-foreground',
  secondary: 'bg-secondary text-secondary-foreground',
  destructive: 'bg-destructive text-destructive-foreground',
  outline: 'border border-input bg-background text-foreground',
  accent: 'bg-accent text-accent-foreground',
}

const badgeSizes = {
  sm: 'px-2 py-1 text-xs',
  md: 'px-3 py-1.5 text-sm',
  lg: 'px-4 py-2 text-base',
}

export function Badge({ 
  className, 
  variant = 'default', 
  size = 'md',
  ...props 
}: BadgeProps) {
  return (
    <div
      className={cn(
        'inline-flex items-center rounded-full font-medium',
        badgeVariants[variant],
        badgeSizes[size],
        className
      )}
      {...props}
    />
  )
}