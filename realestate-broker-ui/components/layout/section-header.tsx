"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export interface SectionHeaderProps {
  title: string
  count?: number | null
  countLabel?: string
  description?: React.ReactNode
  primaryActions?: React.ReactNode
  savedFilters?: React.ReactNode
  className?: string
  headingLevel?: 1 | 2 | 3 | 4 | 5 | 6
}

const formatCount = (value: number | null | undefined) => {
  if (value === null || value === undefined) {
    return null
  }

  try {
    return new Intl.NumberFormat("he-IL").format(value)
  } catch (error) {
    console.error("Failed to format count", error)
    return value.toString()
  }
}

export function SectionHeader({
  title,
  count,
  countLabel,
  description,
  primaryActions,
  savedFilters,
  className,
  headingLevel = 1,
}: SectionHeaderProps) {
  const HeadingTag = `h${headingLevel}` as const
  const formattedCount = formatCount(count)

  return (
    <section
      className={cn(
        "space-y-3 border-b border-border/60 bg-background/95 px-4 py-4 text-right shadow-sm backdrop-blur-sm sm:px-6 lg:px-8",
        className
      )}
      aria-labelledby="section-header-title"
    >
      <div className="flex flex-col items-stretch gap-3 md:flex-row md:items-center md:justify-between">
        <div className="space-y-1">
          <HeadingTag id="section-header-title" className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {title}
          </HeadingTag>
          {(formattedCount || description) && (
            <p className="text-sm text-muted-foreground sm:text-base">
              {formattedCount ? (
                <span>
                  {formattedCount}
                  {countLabel ? <span className="ms-1">{countLabel}</span> : null}
                </span>
              ) : null}
              {formattedCount && description ? <span className="px-1">•</span> : null}
              {description}
            </p>
          )}
        </div>
        <div className="flex flex-col items-stretch justify-end gap-2 sm:flex-row sm:items-center sm:gap-3">
          {savedFilters ? (
            <div className="flex items-center justify-end gap-2 sm:justify-start">{savedFilters}</div>
          ) : null}
          {primaryActions ? (
            <div className="flex flex-wrap items-center justify-end gap-2 sm:justify-start">{primaryActions}</div>
          ) : null}
        </div>
      </div>
    </section>
  )
}

SectionHeader.displayName = "SectionHeader"
