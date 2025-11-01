import React from 'react'
import { cn } from '@/lib/utils'

export interface SectionHeaderProps
  extends Omit<React.HTMLAttributes<HTMLElement>, 'title'> {
  title: React.ReactNode
  description?: React.ReactNode
  actions?: React.ReactNode
}

function renderSectionTitle(content: React.ReactNode) {
  if (typeof content === 'string') {
    return (
      <h2 className="text-2xl font-semibold tracking-tight text-foreground">
        {content}
      </h2>
    )
  }
  return content
}

function renderSectionDescription(content?: React.ReactNode) {
  if (!content) return null
  if (typeof content === 'string') {
    return <p className="text-sm text-muted-foreground">{content}</p>
  }
  return content
}

export function SectionHeader({
  title,
  description,
  actions,
  className,
  children,
  ...props
}: SectionHeaderProps) {
  return (
    <header
      className={cn(
        'flex flex-col gap-[var(--space-3)] border-b border-border/50 pb-[var(--space-3)] sm:flex-row sm:items-center sm:justify-between',
        className
      )}
      {...props}
    >
      <div className="flex flex-col gap-[var(--space-2)]">
        {renderSectionTitle(title)}
        {renderSectionDescription(description)}
        {children}
      </div>
      {actions && (
        <div className="flex flex-wrap items-center gap-[var(--space-2)] sm:justify-end" data-testid="section-header-actions">
          {actions}
        </div>
      )}
    </header>
  )
}

export default SectionHeader
