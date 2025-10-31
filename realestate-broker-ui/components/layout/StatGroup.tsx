import React from 'react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'

export type StatTrendDirection = 'up' | 'down' | 'neutral'

export interface StatTrend {
  direction: StatTrendDirection
  label: string
}

export interface StatGroupItemProps extends React.HTMLAttributes<HTMLDivElement> {
  label: React.ReactNode
  value: React.ReactNode
  helperText?: React.ReactNode
  trend?: StatTrend
  tone?: 'default' | 'positive' | 'negative' | 'warning'
}

export interface StatGroupProps extends React.HTMLAttributes<HTMLElement> {
  columns?: 2 | 3 | 4
}

const toneClasses: Record<NonNullable<StatGroupItemProps['tone']>, string> = {
  default: 'text-foreground',
  positive: 'text-success',
  negative: 'text-destructive',
  warning: 'text-warning',
}

const trendClasses: Record<StatTrendDirection, string> = {
  up: 'text-success',
  down: 'text-destructive',
  neutral: 'text-muted-foreground',
}

const trendIconMap: Record<StatTrendDirection, React.ComponentType<{ className?: string }>> = {
  up: TrendingUp,
  down: TrendingDown,
  neutral: Minus,
}

const columnLayouts: Record<NonNullable<StatGroupProps['columns']>, string> = {
  2: 'grid-cols-1 sm:grid-cols-2',
  3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
  4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
}

export const StatGroup = ({ columns = 3, className, children, ...props }: StatGroupProps) => {
  const columnClass = columnLayouts[columns] ?? columnLayouts[3]
  return (
    <section className={cn('w-full', className)} {...props}>
      <div className={cn('grid gap-[var(--space-4)]', columnClass)}>{children}</div>
    </section>
  )
}

const StatGroupItem = ({
  label,
  value,
  helperText,
  trend,
  tone = 'default',
  className,
  children,
  ...props
}: StatGroupItemProps) => {
  const TrendIcon = trend ? trendIconMap[trend.direction] : null
  return (
    <div
      className={cn(
        'flex flex-col gap-[var(--space-3)] rounded-[var(--radius-2)] border border-border/60 bg-card/80 p-[var(--space-4)] shadow-[var(--shadow-1)] backdrop-blur-sm',
        className
      )}
      {...props}
    >
      <span className="text-sm font-medium text-muted-foreground">{label}</span>
      <div className="flex flex-wrap items-baseline gap-[var(--space-2)]">
        <span className={cn('text-3xl font-semibold tracking-tight', toneClasses[tone])}>
          {value}
        </span>
        {trend && TrendIcon && (
          <span
            className={cn('inline-flex items-center gap-1 text-xs font-medium', trendClasses[trend.direction])}
            data-testid="stat-group-trend"
          >
            <TrendIcon className="h-3.5 w-3.5" aria-hidden />
            {trend.label}
          </span>
        )}
      </div>
      {children}
      {helperText && (
        <p className="text-xs text-muted-foreground" data-testid="stat-group-helper">
          {helperText}
        </p>
      )}
    </div>
  )
}

StatGroupItem.displayName = 'StatGroupItem'

export { StatGroupItem }

;(StatGroup as any).Item = StatGroupItem

export default StatGroup
