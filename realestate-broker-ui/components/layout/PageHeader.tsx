import React from 'react'
import { cn } from '@/lib/utils'

export interface PageHeaderProps
  extends Omit<React.HTMLAttributes<HTMLElement>, 'title'> {
  title: React.ReactNode
  description?: React.ReactNode
  actions?: React.ReactNode
  breadcrumbs?: React.ReactNode
  meta?: React.ReactNode
}

function renderHeading(content: React.ReactNode) {
  if (typeof content === 'string') {
    return (
      <h1 className="text-3xl font-semibold tracking-tight text-foreground">
        {content}
      </h1>
    )
  }
  return content
}

function renderDescription(content?: React.ReactNode) {
  if (!content) return null
  if (typeof content === 'string') {
    return <p className="text-base text-muted-foreground">{content}</p>
  }
  return content
}

export function PageHeader({
  title,
  description,
  actions,
  breadcrumbs,
  meta,
  className,
  children,
  ...props
}: PageHeaderProps) {
  return (
    <header
      className={cn('w-full border-b border-border/60 bg-background', className)}
      {...props}
    >
      <div className="mx-auto flex w-full max-w-[var(--container-max)] flex-col gap-[var(--space-4)] px-[var(--space-4)] py-[var(--space-6)] sm:px-[var(--space-6)]">
        {breadcrumbs && (
          <div className="text-sm text-muted-foreground" data-testid="page-header-breadcrumbs">
            {breadcrumbs}
          </div>
        )}
        <div className="flex flex-col gap-[var(--space-4)] sm:flex-row sm:items-start sm:justify-between">
          <div className="flex flex-col gap-[var(--space-2)]">
            {renderHeading(title)}
            {renderDescription(description)}
            {children}
          </div>
          {(actions || meta) && (
            <div className="flex w-full flex-col items-start gap-[var(--space-2)] sm:w-auto sm:items-end">
              {meta && (
                <div className="text-sm font-medium text-muted-foreground" data-testid="page-header-meta">
                  {meta}
                </div>
              )}
              {actions && (
                <div className="flex flex-wrap justify-end gap-[var(--space-2)]" data-testid="page-header-actions">
                  {actions}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

export default PageHeader
