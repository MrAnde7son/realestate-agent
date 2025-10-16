'use client'

import React, { useState, useMemo } from 'react'
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  getPaginationRowModel,
  PaginationState,
  Updater,
} from '@tanstack/react-table'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { ArrowDown, ArrowUp, ArrowUpDown, Calendar, Home, Building } from 'lucide-react'
import TableToolbar from '@/components/TableToolbar'
import { useAnalytics } from '@/hooks/useAnalytics'
import TablePagination from '@/components/TablePagination'

interface Transaction {
  id?: string
  address: string
  area?: number
  rooms?: number
  price: number
  price_per_sqm: number
  date?: string
  source?: string
}

interface TransactionsTableProps {
  data: Transaction[]
  loading?: boolean
  searchValue?: string
  onSearchChange?: (value: string) => void
  filters?: {
    source?: {
      value: string
      onChange: (value: string) => void
      options: { value: string; label: string }[]
    }
    area?: {
      value: string
      onChange: (value: string) => void
      options: { value: string; label: string }[]
    }
  }
  onRefresh?: () => void
  manualPagination?: boolean
  manualSorting?: boolean
  pageCount?: number
  paginationState?: PaginationState
  onPaginationChange?: (updater: Updater<PaginationState>) => void
  sortingState?: SortingState
  onSortingChange?: (updater: Updater<SortingState>) => void
  totalCount?: number
  filterOptions?: {
    source?: string[]
    area?: string[]
  }
}

function createColumns(): ColumnDef<Transaction>[] {
  return [
    {
      accessorKey: 'address',
      header: 'כתובת',
      cell: ({ row }) => (
        <div className="font-medium text-sm">
          {row.getValue('address')}
        </div>
      ),
    },
    {
      accessorKey: 'area',
      header: 'שטח',
      cell: ({ row }) => {
        const area = row.getValue('area') as number
        return area ? (
          <div className="flex items-center gap-1 text-sm rtl:flex-row-reverse">
            <Home className="h-3 w-3" />
            {area} מ״ר
          </div>
        ) : (
          <span className="text-muted-foreground text-sm">—</span>
        )
      },
    },
    {
      accessorKey: 'rooms',
      header: 'חדרים',
      cell: ({ row }) => {
        const rooms = row.getValue('rooms') as number
        return rooms ? (
          <div className="text-sm">{rooms}</div>
        ) : (
          <span className="text-muted-foreground text-sm">—</span>
        )
      },
    },
    {
      accessorKey: 'price',
      header: 'מחיר',
      cell: ({ row }) => {
        const price = row.getValue('price') as number
        return (
          <div className="font-bold text-sm">
            {price ? new Intl.NumberFormat('he-IL', {
              style: 'currency',
              currency: 'ILS',
              minimumFractionDigits: 0,
              maximumFractionDigits: 0,
            }).format(price) : '—'}
          </div>
        )
      },
    },
    {
      accessorKey: 'price_per_sqm',
      header: 'מחיר למ״ר',
      cell: ({ row }) => {
        const pricePerSqm = row.getValue('price_per_sqm') as number
        return (
          <div className="text-sm text-muted-foreground">
            {pricePerSqm ? new Intl.NumberFormat('he-IL', {
              style: 'currency',
              currency: 'ILS',
              minimumFractionDigits: 0,
              maximumFractionDigits: 0,
            }).format(pricePerSqm) : '—'}
          </div>
        )
      },
    },
    {
      accessorKey: 'date',
      header: 'תאריך',
      cell: ({ row }) => {
        const date = row.getValue('date') as string
        return date ? (
          <div className="flex items-center gap-1 text-sm text-muted-foreground rtl:flex-row-reverse">
            <Calendar className="h-3 w-3" />
            {new Date(date).toLocaleDateString('he-IL')}
          </div>
        ) : (
          <span className="text-muted-foreground text-sm">—</span>
        )
      },
    },
    {
      accessorKey: 'source',
      header: 'מקור',
      cell: ({ row }) => {
        const source = row.getValue('source') as string
        const getSourceDisplay = (source: string) => {
          switch (source) {
            case 'collected_government': return 'ממשלתי'
            case 'government': return 'ממשלתי'
            case 'internal': return 'מאגר פנימי'
            default: return source || 'לא ידוע'
          }
        }
        const getSourceVariant = (source: string) => {
          switch (source) {
            case 'collected_government': return 'default'
            case 'government': return 'default'
            case 'internal': return 'secondary'
            default: return 'outline'
          }
        }
        return (
          <Badge variant={getSourceVariant(source) as any}>
            {getSourceDisplay(source)}
          </Badge>
        )
      },
    },
  ]
}

export default function TransactionsTable({
  data,
  loading = false,
  searchValue = '',
  onSearchChange,
  filters,
  onRefresh,
  manualPagination = false,
  manualSorting = false,
  pageCount,
  paginationState,
  onPaginationChange,
  sortingState,
  onSortingChange,
  totalCount,
  filterOptions,
}: TransactionsTableProps) {
  const { trackFeatureUsage } = useAnalytics()
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = useState({})
  const [internalSorting, setInternalSorting] = useState<SortingState>(sortingState ?? [])
  const [internalPagination, setInternalPagination] = useState<PaginationState>(
    paginationState ?? { pageIndex: 0, pageSize: 10 }
  )

  React.useEffect(() => {
    if (sortingState) {
      setInternalSorting(sortingState)
    }
  }, [sortingState])

  React.useEffect(() => {
    if (paginationState) {
      setInternalPagination(paginationState)
    }
  }, [paginationState])

  const columns = useMemo(() => createColumns(), [])

  const useClientFiltering = !(manualPagination || manualSorting)

  const filteredData = useMemo(() => {
    if (!useClientFiltering) {
      return data
    }

    let filtered = data

    // Apply search filter
    if (searchValue) {
      const searchLower = searchValue.toLowerCase()
      filtered = filtered.filter((transaction) =>
        transaction.address?.toLowerCase().includes(searchLower) ||
        transaction.area?.toString().includes(searchLower) ||
        transaction.rooms?.toString().includes(searchLower) ||
        transaction.price?.toString().includes(searchLower) ||
        transaction.price_per_sqm?.toString().includes(searchLower) ||
        transaction.source?.toLowerCase().includes(searchLower)
      )
    }

    // Apply source filter
    if (filters?.source?.value && filters.source.value !== 'all') {
      filtered = filtered.filter((transaction) => transaction.source === filters.source?.value)
    }

    // Apply area filter
    if (filters?.area?.value && filters.area.value !== 'all') {
      const areaRange = filters.area.value.split('-')
      if (areaRange.length === 2) {
        const minArea = parseInt(areaRange[0])
        const maxArea = parseInt(areaRange[1])
        filtered = filtered.filter((transaction) => 
          transaction.area && transaction.area >= minArea && transaction.area <= maxArea
        )
      }
    }

    return filtered
  }, [data, searchValue, filters, useClientFiltering])

  React.useEffect(() => {
    if (!manualPagination && useClientFiltering) {
      setInternalPagination((prev) => ({ ...prev, pageIndex: 0 }))
    }
  }, [filteredData.length, manualPagination, useClientFiltering])

  const tableData = useClientFiltering ? filteredData : data
  const resolvedSorting = sortingState ?? internalSorting
  const resolvedPagination = paginationState ?? internalPagination

  const handleSortingChange = (updater: Updater<SortingState>) => {
    const next = typeof updater === 'function' ? updater(resolvedSorting) : updater
    if (onSortingChange) {
      onSortingChange(next)
    } else {
      setInternalSorting(next)
    }
  }

  const handlePaginationChange = (updater: Updater<PaginationState>) => {
    const next = typeof updater === 'function' ? updater(resolvedPagination) : updater
    if (onPaginationChange) {
      onPaginationChange(next)
    } else {
      setInternalPagination(next)
    }
  }

  const table = useReactTable({
    data: tableData,
    columns,
    onSortingChange: handleSortingChange,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    state: {
      sorting: resolvedSorting,
      columnFilters,
      columnVisibility,
      rowSelection,
      pagination: resolvedPagination,
    },
    manualPagination,
    manualSorting,
    pageCount: manualPagination ? pageCount : undefined,
    onPaginationChange: handlePaginationChange,
    ...(!manualSorting ? { getSortedRowModel: getSortedRowModel() } : {}),
    ...(!manualPagination ? { getPaginationRowModel: getPaginationRowModel() } : {}),
    ...(!manualSorting || !manualPagination ? { getFilteredRowModel: getFilteredRowModel() } : {}),
  })

  const resolvedTotalCount = totalCount ?? filteredData.length

  // Additional filters for the toolbar
  const additionalFilters = useMemo(() => {
    const getSourceLabel = (source: string) => {
      switch (source) {
        case 'collected_government':
        case 'government':
          return 'ממשלתי'
        case 'internal':
          return 'מאגר פנימי'
        default:
          return source || 'לא ידוע'
      }
    }

    const getAreaLabel = (range: string) => {
      if (range.endsWith('+')) {
        return `${range.replace('+', '+')} מ״ר`
      }
      const [start, end] = range.split('-')
      if (!start || !end) {
        return range
      }
      return `${start}-${end} מ״ר`
    }

    const sourceOptions =
      filterOptions?.source && filterOptions.source.length > 0
        ? filterOptions.source
        : Array.from(
            new Set(
              data
                .map((transaction) => transaction.source)
                .filter((value): value is string => typeof value === 'string' && value.length > 0)
            )
          )

    const areaOptions =
      filterOptions?.area && filterOptions.area.length > 0
        ? filterOptions.area
        : []

    return [
      {
        key: 'source',
        label: 'מקור',
        value: filters?.source?.value ?? 'all',
        options: [
          { value: 'all', label: 'הכל' },
          ...sourceOptions.map((value) => ({
            value,
            label: getSourceLabel(value),
          })),
        ],
      },
      {
        key: 'area',
        label: 'שטח',
        value: filters?.area?.value ?? 'all',
        options: [
          { value: 'all', label: 'הכל' },
          ...(areaOptions.length > 0
            ? areaOptions.map((value) => ({
                value,
                label: getAreaLabel(value),
              }))
            : []),
        ],
      },
    ]
  }, [filterOptions, data, filters])

  const handleAdditionalFilterChange = (key: string, value: string) => {
    if (key === 'source' && filters?.source?.onChange) {
      filters.source.onChange(value)
    } else if (key === 'area' && filters?.area?.onChange) {
      filters.area.onChange(value)
    }
  }

  const toolbarColumns = useMemo(() => 
    columns.map(column => ({
      id: column.id || '',
      header: typeof column.header === 'string' ? column.header : '',
      visible: true,
      toggle: () => {}, // No-op since we don't need column visibility toggle for transactions
    })), [columns]
  )

  return (
    <div className="rounded-xl border border-border bg-card overflow-x-auto rtl" dir="rtl">
      {/* Integrated Toolbar */}
      <TableToolbar
        searchValue={searchValue}
        onSearchChange={(value) => {
          if (onSearchChange) {
            onSearchChange(value);
          }
          if (value.trim()) {
            trackFeatureUsage('search', undefined, { query: value.trim() });
          }
        }}
        searchPlaceholder="חיפוש בעסקאות..."
        filters={{
          city: { value: 'all', onChange: () => {}, options: [] },
          type: { value: 'all', onChange: () => {}, options: [] },
          priceMin: { value: undefined, onChange: () => {} },
          priceMax: { value: undefined, onChange: () => {} },
          ...(filters || {})
        }}
        additionalFilters={additionalFilters}
        onAdditionalFilterChange={handleAdditionalFilterChange}
        columns={toolbarColumns}
        selectedCount={table.getSelectedRowModel().rows.length}
        totalCount={resolvedTotalCount}
        onExportSelected={() => {}}
        onExportAll={() => {}}
        viewMode="table"
        onViewModeChange={() => {}}
        onRefresh={onRefresh || (() => {})}
        loading={loading}
      />

      {/* Table */}
      <div className="relative">
        <Table className="rtl">
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const sorted = header.column.getIsSorted()
                  return (
                    <TableHead key={header.id} className="text-right rtl:text-right">
                      {header.isPlaceholder ? null : (
                        <button
                          type="button"
                          onClick={header.column.getToggleSortingHandler()}
                          disabled={!header.column.getCanSort()}
                          className="flex w-full items-center justify-end gap-1 text-xs font-medium rtl:flex-row-reverse disabled:cursor-default"
                        >
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                          {header.column.getCanSort() && (
                            <span className="text-muted-foreground">
                              {sorted === 'asc' ? (
                                <ArrowUp className="h-3 w-3" />
                              ) : sorted === 'desc' ? (
                                <ArrowDown className="h-3 w-3" />
                              ) : (
                                <ArrowUpDown className="h-3 w-3" />
                              )}
                            </span>
                          )}
                        </button>
                      )}
                    </TableHead>
                  )
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {filteredData.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  <div className="flex flex-col items-center justify-center py-8">
                    <Building className="h-8 w-8 text-muted-foreground mb-2" />
                    <div className="text-muted-foreground">לא נמצאו עסקאות השוואה</div>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id} className="hover:bg-muted/50">
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="text-right rtl:text-right">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      <TablePagination table={table} />
    </div>
  )
}
