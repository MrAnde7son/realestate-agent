"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/Badge"
import { SavedFiltersMenu, type SavedFilterPreset } from "./saved-filters-menu"

export interface SectionHeaderAction {
  label: string
  onClick: () => void
  icon?: React.ReactNode
  variant?: "default" | "outline" | "ghost" | "destructive"
  size?: "default" | "sm" | "lg" | "icon"
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
  savedFilterPresets?: SavedFilterPreset[]
  onSaveCurrentFilters?: () => void
  hasActiveFilters?: boolean
  toolbarActions?: React.ReactNode
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
  savedFilterPresets,
  onSaveCurrentFilters,
  hasActiveFilters,
  toolbarActions,
  className,
  children,
}: SectionHeaderProps) {
  const hasActions = (primaryActions && primaryActions.length > 0) || children || toolbarActions

  return (
    <div className={cn("flex flex-col gap-4", className)}>
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
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
        </div>
        
        {(hasActions || savedFilterPresets !== undefined) && (
          <div className="flex flex-wrap items-center gap-2 md:flex-shrink-0">
            {savedFilterPresets !== undefined && (
              <SavedFiltersMenu
                presets={savedFilterPresets}
                onSaveCurrent={onSaveCurrentFilters}
                hasActiveFilters={hasActiveFilters}
              />
            )}
            {toolbarActions}
            {primaryActions?.map((action, index) => (
              <Button
                key={index}
                variant={action.variant || "default"}
                size={action.size || "sm"}
                onClick={action.onClick}
                disabled={action.disabled}
                className="h-8 sm:min-h-[44px] rounded-full px-2 sm:px-4 flex items-center gap-1 sm:gap-2 flex-shrink-0 text-xs sm:text-sm"
              >
                {action.icon && <span aria-hidden="true">{action.icon}</span>}
                {action.label}
              </Button>
            ))}
            {children}
          </div>
        )}
      </div>

      {savedFilters && savedFilters.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {savedFilters.map((filter) => (
            <Button
              key={filter.id}
              variant={filter.isActive ? "default" : "outline"}
              size="sm"
              onClick={filter.onClick}
              className="h-7"
              aria-pressed={filter.isActive}
            >
              {filter.label}
            </Button>
          ))}
        </div>
      )}
    </div>
  )
}

