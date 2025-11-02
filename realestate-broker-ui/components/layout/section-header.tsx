"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/Badge"

export interface SectionHeaderAction {
  label: string
  onClick: () => void
  icon?: React.ReactNode
  variant?: "default" | "outline" | "ghost" | "destructive"
  size?: "sm" | "md" | "lg"
  disabled?: boolean
}

export interface SavedFilter {
  id: string
  label: string
  onClick: () => void
  isActive?: boolean
}

interface SectionHeaderProps {
  title: string
  description?: string
  count?: number | string
  countLabel?: string
  primaryActions?: SectionHeaderAction[]
  savedFilters?: SavedFilter[]
  className?: string
  children?: React.ReactNode
}

export function SectionHeader({
  title,
  description,
  count,
  countLabel,
  primaryActions,
  savedFilters,
  className,
  children,
}: SectionHeaderProps) {
  return (
    <div className={cn("flex flex-col gap-4 md:flex-row md:items-center md:justify-between", className)}>
      <div className="flex-1">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground text-end">{title}</h1>
          {count !== undefined && (
            <Badge variant="secondary" className="text-sm font-medium">
              {count} {countLabel || ""}
            </Badge>
          )}
        </div>
        {description && (
          <p className="text-sm sm:text-base text-muted-foreground text-end mt-1">{description}</p>
        )}
        {savedFilters && savedFilters.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {savedFilters.map((filter) => (
              <Button
                key={filter.id}
                variant={filter.isActive ? "default" : "outline"}
                size="sm"
                onClick={filter.onClick}
                className="h-7"
              >
                {filter.label}
              </Button>
            ))}
          </div>
        )}
      </div>
      
      {(primaryActions && primaryActions.length > 0) || children ? (
        <div className="flex flex-wrap items-center gap-2 md:flex-shrink-0">
          {primaryActions?.map((action, index) => (
            <Button
              key={index}
              variant={action.variant || "default"}
              size={action.size || "sm"}
              onClick={action.onClick}
              disabled={action.disabled}
              className="gap-2"
            >
              {action.icon}
              {action.label}
            </Button>
          ))}
          {children}
        </div>
      ) : null}
    </div>
  )
}

