"use client"

import * as React from "react"
import { ChevronDown, Star, StarOff, Trash2, Filter } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/Badge"

const TOOLBAR_PILL_BUTTON_CLASSES =
  "h-8 sm:min-h-[44px] rounded-full px-2 sm:px-4 flex items-center gap-1 sm:gap-2 flex-shrink-0 text-xs sm:text-sm"

export interface SavedFilterPreset {
  id: string
  label: string
  description?: string
  isActive?: boolean
  isStarred?: boolean
  onClick: () => void
  onDelete?: () => void
}

interface SavedFiltersMenuProps {
  presets?: SavedFilterPreset[]
  onSaveCurrent?: () => void
  hasActiveFilters?: boolean
  className?: string
}

export function SavedFiltersMenu({
  presets = [],
  onSaveCurrent,
  hasActiveFilters = false,
  className,
}: SavedFiltersMenuProps) {
  const [open, setOpen] = React.useState(false)

  const starredPresets = presets.filter((p) => p.isStarred)
  const otherPresets = presets.filter((p) => !p.isStarred)
  const activePreset = presets.find((p) => p.isActive)

  if (presets.length === 0 && !onSaveCurrent) {
    return null
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={cn(
            TOOLBAR_PILL_BUTTON_CLASSES,
            hasActiveFilters && "border-primary",
            className
          )}
        >
          <Filter className="h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0" />
          <span className="hidden sm:inline">
            {activePreset ? (
              <>
                {activePreset.label}
                <Badge variant="secondary" className="ms-1 h-5 px-1.5 text-xs">
                  פעיל
                </Badge>
              </>
            ) : hasActiveFilters ? (
              "מסננים פעילים"
            ) : (
              "שמור מסננים"
            )}
          </span>
          <ChevronDown className="h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0 hidden sm:block" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        {onSaveCurrent && (
          <>
            <DropdownMenuItem onClick={onSaveCurrent} className="gap-2">
              <Star className="h-4 w-4" />
              שמור מסננים נוכחיים
            </DropdownMenuItem>
            <DropdownMenuSeparator />
          </>
        )}

        {starredPresets.length > 0 && (
          <>
            <DropdownMenuLabel>מועדפים</DropdownMenuLabel>
            {starredPresets.map((preset) => (
              <DropdownMenuItem
                key={preset.id}
                onClick={() => {
                  preset.onClick()
                  setOpen(false)
                }}
                className={cn(
                  "gap-2",
                  preset.isActive && "bg-accent"
                )}
              >
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                <div className="flex-1 flex flex-col">
                  <span>{preset.label}</span>
                  {preset.description && (
                    <span className="text-xs text-muted-foreground">{preset.description}</span>
                  )}
                </div>
                {preset.onDelete && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 hover:bg-destructive hover:text-destructive-foreground"
                    onClick={(e) => {
                      e.stopPropagation()
                      preset.onDelete?.()
                      setOpen(false)
                    }}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                )}
              </DropdownMenuItem>
            ))}
            {otherPresets.length > 0 && <DropdownMenuSeparator />}
          </>
        )}

        {otherPresets.length > 0 && (
          <>
            <DropdownMenuLabel>מסננים שמורים</DropdownMenuLabel>
            {otherPresets.map((preset) => (
              <DropdownMenuItem
                key={preset.id}
                onClick={() => {
                  preset.onClick()
                  setOpen(false)
                }}
                className={cn(
                  "gap-2",
                  preset.isActive && "bg-accent"
                )}
              >
                <div className="flex-1 flex flex-col">
                  <span>{preset.label}</span>
                  {preset.description && (
                    <span className="text-xs text-muted-foreground">{preset.description}</span>
                  )}
                </div>
                {preset.onDelete && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 hover:bg-destructive hover:text-destructive-foreground"
                    onClick={(e) => {
                      e.stopPropagation()
                      preset.onDelete?.()
                      setOpen(false)
                    }}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                )}
              </DropdownMenuItem>
            ))}
          </>
        )}

        {presets.length === 0 && onSaveCurrent && (
          <DropdownMenuItem disabled className="text-muted-foreground text-xs">
            אין מסננים שמורים
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

