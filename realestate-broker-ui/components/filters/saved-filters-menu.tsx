"use client"

import * as React from "react"
import { usePathname, useRouter } from "next/navigation"
import { Filter, BookmarkCheck, PlusCircle, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const STORAGE_NAMESPACE = "nadlanr:saved-filters"

type SavedFilter = {
  id: string
  name: string
  query: string
  pathname: string
}

const loadSavedFilters = (storageKey: string): SavedFilter[] => {
  if (typeof window === "undefined") return []

  try {
    const stored = window.localStorage.getItem(`${STORAGE_NAMESPACE}:${storageKey}`)
    if (!stored) {
      return []
    }
    const parsed = JSON.parse(stored)
    if (!Array.isArray(parsed)) {
      return []
    }
    return parsed.filter((item): item is SavedFilter =>
      item && typeof item === "object" && typeof item.name === "string" && typeof item.query === "string"
    )
  } catch (error) {
    console.warn("Failed to parse saved filters", error)
    return []
  }
}

const persistSavedFilters = (storageKey: string, filters: SavedFilter[]) => {
  if (typeof window === "undefined") return
  try {
    window.localStorage.setItem(`${STORAGE_NAMESPACE}:${storageKey}`, JSON.stringify(filters))
  } catch (error) {
    console.warn("Failed to persist saved filters", error)
  }
}

export interface SavedFiltersMenuProps {
  storageKey: string
  label?: string
  disabled?: boolean
  onApplied?: () => void
}

export function SavedFiltersMenu({ storageKey, label = "סינונים שמורים", disabled, onApplied }: SavedFiltersMenuProps) {
  const router = useRouter()
  const pathname = usePathname()
  const [savedFilters, setSavedFilters] = React.useState<SavedFilter[]>([])

  React.useEffect(() => {
    setSavedFilters(loadSavedFilters(storageKey))
  }, [storageKey])

  const handleSaveCurrent = React.useCallback(() => {
    if (typeof window === "undefined") return
    const query = window.location.search.startsWith("?") ? window.location.search.slice(1) : window.location.search
    const defaultName = `תצוגה ${savedFilters.length + 1}`
    const name = window.prompt("שם לסינון השמור", defaultName)
    if (!name) {
      return
    }
    const newFilter: SavedFilter = {
      id: typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}`,
      name: name.trim(),
      query,
      pathname: pathname || "/",
    }
    const nextFilters = [...savedFilters.filter((item) => item.name !== newFilter.name), newFilter]
    setSavedFilters(nextFilters)
    persistSavedFilters(storageKey, nextFilters)
  }, [pathname, savedFilters, storageKey])

  const handleApply = React.useCallback(
    (filter: SavedFilter) => {
      const destination = filter.query ? `${filter.pathname}?${filter.query}` : filter.pathname
      router.push(destination)
      if (onApplied) {
        onApplied()
      }
    },
    [onApplied, router]
  )

  const handleClearAll = React.useCallback(() => {
    if (typeof window === "undefined") return
    const shouldClear = window.confirm("למחוק את כל הסינונים השמורים?")
    if (!shouldClear) return
    setSavedFilters([])
    persistSavedFilters(storageKey, [])
  }, [storageKey])

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" disabled={disabled} className="gap-2">
          <Filter className="h-4 w-4" />
          {label}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel className="text-right">{label}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuGroup className="space-y-1">
          {savedFilters.length === 0 ? (
            <DropdownMenuItem disabled className="justify-end text-muted-foreground">
              אין סינונים שמורים
            </DropdownMenuItem>
          ) : (
            savedFilters.map((filter) => (
              <DropdownMenuItem
                key={filter.id}
                onSelect={(event) => {
                  event.preventDefault()
                  handleApply(filter)
                }}
                className="flex items-center justify-between gap-2"
              >
                <div className="flex items-center gap-2">
                  <BookmarkCheck className="h-4 w-4 text-muted-foreground" />
                  <div className="flex flex-col text-right">
                    <span className="text-sm font-medium">{filter.name}</span>
                    <span className="text-[0.7rem] text-muted-foreground">{filter.pathname}</span>
                  </div>
                </div>
              </DropdownMenuItem>
            ))
          )}
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onSelect={(event) => {
            event.preventDefault()
            handleSaveCurrent()
          }}
          className="justify-end gap-2"
        >
          <PlusCircle className="h-4 w-4 text-muted-foreground" />
          שמור סינון נוכחי
        </DropdownMenuItem>
        {savedFilters.length > 0 && (
          <DropdownMenuItem
            onSelect={(event) => {
              event.preventDefault()
              handleClearAll()
            }}
            className="justify-end gap-2 text-destructive focus:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
            נקה הכל
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

SavedFiltersMenu.displayName = "SavedFiltersMenu"
