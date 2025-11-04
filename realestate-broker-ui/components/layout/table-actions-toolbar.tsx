"use client"

import * as React from "react"
import { Settings, MoreHorizontal, RefreshCw, Plus, Download, ChevronDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"
import { Badge } from "@/components/ui/Badge"
import { cn } from "@/lib/utils"

const TOOLBAR_PILL_BUTTON_CLASSES =
  "h-8 sm:min-h-[44px] rounded-full px-2 sm:px-4 flex items-center gap-1 sm:gap-2 flex-shrink-0 text-xs sm:text-sm"

export interface TableActionColumn {
  id: string
  header: string
  visible: boolean
  toggle: (value: boolean) => void
}

export interface TableAction {
  label: string
  onClick: () => void
  icon?: React.ReactNode
  disabled?: boolean
}

export interface TableActionsToolbarProps {
  // Columns
  columns?: TableActionColumn[]
  onResetColumns?: () => void
  
  // Actions menu
  exportAll?: () => void
  exportSelected?: () => void
  importAction?: {
    label: string
    onClick: () => void
    icon?: React.ReactNode
  }
  bulkActions?: TableAction[]
  selectedCount?: number
  totalCount?: number
  disableExportAll?: boolean
  
  // Refresh
  onRefresh?: () => void
  loading?: boolean
  
  // Add new
  onAddNew?: () => void
  
  className?: string
}

export function TableActionsToolbar({
  columns,
  onResetColumns,
  exportAll,
  exportSelected,
  importAction,
  bulkActions,
  selectedCount = 0,
  totalCount = 0,
  disableExportAll = false,
  onRefresh,
  loading = false,
  onAddNew,
  className,
}: TableActionsToolbarProps) {
  const [columnSearch, setColumnSearch] = React.useState('')

  const filteredColumns = React.useMemo(() => {
    if (!columns) return []
    if (!columnSearch.trim()) return columns
    const search = columnSearch.toLowerCase()
    return columns.filter(col => col.header.toLowerCase().includes(search))
  }, [columns, columnSearch])

  return (
    <div
      data-testid="toolbar-actions-container"
      className={cn(
        "inline-flex flex-wrap items-center gap-1.5 sm:gap-2 justify-start lg:justify-end",
        className
      )}
    >
      {/* Column selection */}
      {columns && columns.length > 0 && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className={TOOLBAR_PILL_BUTTON_CLASSES}
            >
              <Settings className="h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0" />
              <span className="hidden sm:inline">עמודות</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-64 bg-white max-h-80">
            <DropdownMenuLabel className="bg-white text-foreground sticky top-0 z-10 bg-background border-b">
              בחר עמודות
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <div className="p-2 border-b">
              <div className="relative">
                <Search className="absolute end-2 top-1/2 transform -translate-y-1/2 h-3 w-3 text-muted-foreground" />
                <Input
                  placeholder="חיפוש עמודות..."
                  value={columnSearch}
                  onChange={(e) => setColumnSearch(e.target.value)}
                  className="pe-8 text-start text-sm h-8"
                  dir="rtl"
                />
              </div>
            </div>
            <div className="max-h-60 overflow-y-auto">
              {/* Quick actions */}
              <div className="p-2 border-b bg-muted/30">
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      filteredColumns.forEach(column => {
                        if (!column.visible) column.toggle(true)
                      })
                    }}
                    className="h-6 px-2 text-xs"
                  >
                    בחר הכל
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      filteredColumns.forEach(column => {
                        if (column.visible) column.toggle(false)
                      })
                    }}
                    className="h-6 px-2 text-xs"
                  >
                    בטל הכל
                  </Button>
                  {onResetColumns && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        setColumnSearch('')
                        onResetColumns()
                      }}
                      className="h-6 px-2 text-xs"
                    >
                      שחזר
                    </Button>
                  )}
                </div>
              </div>
              {filteredColumns.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  לא נמצאו עמודות
                </div>
              ) : (
                filteredColumns.map((column) => (
                  <DropdownMenuCheckboxItem
                    key={column.id}
                    checked={column.visible}
                    onCheckedChange={column.toggle}
                    onSelect={(e) => e.preventDefault()}
                    className="bg-white text-foreground hover:bg-muted"
                  >
                    {column.header}
                  </DropdownMenuCheckboxItem>
                ))
              )}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>
      )}

      {/* Actions dropdown */}
      {(exportAll || exportSelected || importAction || (bulkActions && bulkActions.length > 0)) && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className={TOOLBAR_PILL_BUTTON_CLASSES}
              aria-label="פעולות על נתונים"
            >
              <MoreHorizontal className="h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0" />
              <span className="hidden sm:inline">פעולות</span>
              {selectedCount > 0 && (
                <>
                  <Badge
                    variant="secondary"
                    className="hidden sm:inline-flex items-center gap-1 px-1.5 sm:px-2 py-0.5 text-xs font-medium ms-1 sm:ms-2"
                  >
                    {selectedCount}
                  </Badge>
                  <Badge
                    variant="secondary"
                    className="inline-flex items-center justify-center px-1.5 sm:px-2 py-0.5 text-xs font-medium sm:hidden ms-1 sm:ms-2"
                  >
                    {selectedCount}
                  </Badge>
                </>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="bg-white">
            <DropdownMenuLabel className="bg-white text-foreground">פעולות</DropdownMenuLabel>
            <DropdownMenuSeparator />
            
            {/* Export section */}
            {(exportAll || exportSelected) && (
              <>
                <div className="px-2 py-1.5">
                  <span className="text-xs font-medium text-muted-foreground">ייצוא נתונים</span>
                </div>
                {exportAll && (
                  <DropdownMenuCheckboxItem 
                    onClick={exportAll}
                    disabled={disableExportAll}
                    className="bg-white text-foreground hover:bg-muted disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    <Download className="h-4 w-4 me-2 rtl:ms-2 rtl:me-0" />
                    ייצוא הכל ({totalCount})
                  </DropdownMenuCheckboxItem>
                )}
                {exportSelected && (
                  <DropdownMenuCheckboxItem 
                    onClick={exportSelected}
                    disabled={selectedCount === 0}
                    className="bg-white text-foreground hover:bg-muted"
                  >
                    <Download className="h-4 w-4 me-2 rtl:ms-2 rtl:me-0" />
                    ייצוא נבחרים ({selectedCount})
                  </DropdownMenuCheckboxItem>
                )}
              </>
            )}

            {/* Import section */}
            {importAction && (
              <>
                <DropdownMenuSeparator />
                <div className="px-2 py-1.5">
                  <span className="text-xs font-medium text-muted-foreground">ייבוא נתונים</span>
                </div>
                <DropdownMenuCheckboxItem 
                  onClick={importAction.onClick}
                  className="bg-white text-foreground hover:bg-muted"
                >
                  {importAction.icon && <span className="me-2 rtl:ms-2 rtl:me-0">{importAction.icon}</span>}
                  {importAction.label}
                </DropdownMenuCheckboxItem>
              </>
            )}

            {/* Bulk actions section */}
            {bulkActions && bulkActions.length > 0 && selectedCount > 0 && (
              <>
                <DropdownMenuSeparator />
                <div className="px-2 py-1.5">
                  <span className="text-xs font-medium text-muted-foreground">פעולות על נבחרים ({selectedCount})</span>
                </div>
                {bulkActions.map((action, index) => (
                  <DropdownMenuCheckboxItem 
                    key={index}
                    onClick={action.onClick}
                    disabled={action.disabled}
                    className="bg-white text-foreground hover:bg-muted"
                  >
                    {action.icon && <span className="me-2 rtl:ms-2 rtl:me-0">{action.icon}</span>}
                    {action.label}
                  </DropdownMenuCheckboxItem>
                ))}
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      )}

      {/* Refresh */}
      {onRefresh && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={loading}
          className={TOOLBAR_PILL_BUTTON_CLASSES}
        >
          <RefreshCw className={cn("h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0", loading && "animate-spin")} />
          <span className="hidden sm:inline">רענן</span>
        </Button>
      )}

      {/* Add new */}
      {onAddNew && (
        <Button
          onClick={onAddNew}
          size="sm"
          className={TOOLBAR_PILL_BUTTON_CLASSES}
        >
          <Plus className="h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0" />
          <span className="hidden sm:inline">הוסף חדש</span>
        </Button>
      )}
    </div>
  )
}

