"use client"

import { useState, useEffect, useCallback } from "react"

export interface SavedFilterData {
  id: string
  label: string
  description?: string
  filters: Record<string, any>
  isStarred?: boolean
  createdAt: string
}

const getStorageKey = (section: string) => `saved-filters-${section}`

export function useSavedFilters(section: string) {
  const [savedFilters, setSavedFilters] = useState<SavedFilterData[]>([])

  useEffect(() => {
    if (typeof window === "undefined") return

    try {
      const stored = localStorage.getItem(getStorageKey(section))
      if (stored) {
        const parsed = JSON.parse(stored) as SavedFilterData[]
        setSavedFilters(parsed)
      }
    } catch (error) {
      console.error("Failed to load saved filters:", error)
    }
  }, [section])

  const saveFilters = useCallback(
    (filters: Record<string, any>, label: string, description?: string) => {
      const newFilter: SavedFilterData = {
        id: `filter-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        label,
        description,
        filters,
        isStarred: false,
        createdAt: new Date().toISOString(),
      }

      const updated = [...savedFilters, newFilter]
      setSavedFilters(updated)

      if (typeof window !== "undefined") {
        try {
          localStorage.setItem(getStorageKey(section), JSON.stringify(updated))
        } catch (error) {
          console.error("Failed to save filters:", error)
        }
      }

      return newFilter.id
    },
    [savedFilters, section]
  )

  const deleteFilter = useCallback(
    (id: string) => {
      const updated = savedFilters.filter((f) => f.id !== id)
      setSavedFilters(updated)

      if (typeof window !== "undefined") {
        try {
          localStorage.setItem(getStorageKey(section), JSON.stringify(updated))
        } catch (error) {
          console.error("Failed to delete filter:", error)
        }
      }
    },
    [savedFilters, section]
  )

  const toggleStar = useCallback(
    (id: string) => {
      const updated = savedFilters.map((f) =>
        f.id === id ? { ...f, isStarred: !f.isStarred } : f
      )
      setSavedFilters(updated)

      if (typeof window !== "undefined") {
        try {
          localStorage.setItem(getStorageKey(section), JSON.stringify(updated))
        } catch (error) {
          console.error("Failed to update filter:", error)
        }
      }
    },
    [savedFilters, section]
  )

  const applyFilter = useCallback(
    (id: string, onApply: (filters: Record<string, any>) => void) => {
      const filter = savedFilters.find((f) => f.id === id)
      if (filter) {
        onApply(filter.filters)
      }
    },
    [savedFilters]
  )

  const hasActiveFilters = useCallback(
    (currentFilters: Record<string, any>) => {
      return Object.entries(currentFilters).some(([key, value]) => {
        if (value === undefined || value === null || value === "" || value === "all") {
          return false
        }
        if (typeof value === "object" && "min" in value && "max" in value) {
          return value.min !== undefined || value.max !== undefined
        }
        return true
      })
    },
    []
  )

  return {
    savedFilters,
    saveFilters,
    deleteFilter,
    toggleStar,
    applyFilter,
    hasActiveFilters,
  }
}

