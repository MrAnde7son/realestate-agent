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
import TableToolbar, { AdditionalFilterConfig, AdditionalFilterValue } from '@/components/TableToolbar'
import TablePagination from '@/components/TablePagination'
import { TableSkeletonRows } from '@/components/TableSkeletonRows'

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
  }
  priceMin?: number
  onPriceMinChange?: (value: number | undefined) => void
  priceMax?: number
  onPriceMaxChange?: (value: number | undefined) => void
  pricePerSqmMin?: number
  onPricePerSqmMinChange?: (value: number | undefined) => void
  pricePerSqmMax?: number
  onPricePerSqmMaxChange?: (value: number | undefined) => void
  areaRange?: {
    min?: number
    max?: number
    onChange: (value: { min?: number; max?: number }) => void
  }
  addressFilter?: {
    value: string
    onChange: (value: string) => void
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
            case 'govmap':
              return 'GovMap'
            case 'collected_government':
            case 'government':
            case 'nadlan':
              return 'ממשלתי'
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
  priceMin,
  onPriceMinChange,
  priceMax,
  onPriceMaxChange,
  pricePerSqmMin,
  onPricePerSqmMinChange,
  pricePerSqmMax,
  onPricePerSqmMaxChange,
  areaRange,
  addressFilter,
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
    if (typeof priceMin === 'number') {
      filtered = filtered.filter((transaction) => typeof transaction.price === 'number' && transaction.price >= priceMin)
    }

    if (typeof priceMax === 'number') {
      filtered = filtered.filter((transaction) => typeof transaction.price === 'number' && transaction.price <= priceMax)
    }

    if (typeof pricePerSqmMin === 'number') {
      filtered = filtered.filter((transaction) => typeof transaction.price_per_sqm === 'number' && transaction.price_per_sqm >= pricePerSqmMin)
    }

    if (typeof pricePerSqmMax === 'number') {
      filtered = filtered.filter((transaction) => typeof transaction.price_per_sqm === 'number' && transaction.price_per_sqm <= pricePerSqmMax)
    }

    const areaMin = areaRange?.min
    if (areaMin !== undefined) {
      filtered = filtered.filter((transaction) => typeof transaction.area === 'number' && transaction.area >= areaMin)
    }

    const areaMax = areaRange?.max
    if (areaMax !== undefined) {
      filtered = filtered.filter((transaction) => typeof transaction.area === 'number' && transaction.area <= areaMax)
    }

    if (addressFilter?.value) {
      const search = addressFilter.value.trim().toLowerCase()
      if (search) {
        filtered = filtered.filter((transaction) => {
          const address = transaction.address?.toLowerCase() ?? ''
          return address.includes(search)
        })
      }
    }

    return filtered
  }, [
    addressFilter?.value,
    areaRange?.max,
    areaRange?.min,
    data,
    filters?.source?.value,
    priceMax,
    priceMin,
    pricePerSqmMax,
    pricePerSqmMin,
    searchValue,
    useClientFiltering,
  ])

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
  const additionalFilters = useMemo((): AdditionalFilterConfig[] => {
    const items: AdditionalFilterConfig[] = []

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

    if (sourceOptions.length > 0 && filters?.source) {
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

      items.push({
        key: 'source',
        label: 'מקור',
        type: 'select',
        value: filters.source.value ?? 'all',
        showAllOption: false,
        options: [
          { value: 'all', label: 'כל המקורות' },
          ...sourceOptions.map((value) => ({
            value,
            label: getSourceLabel(value),
          })),
        ],
      })
    }

    if (addressFilter) {
      items.push({
        key: 'address',
        label: 'כתובת',
        type: 'text',
        value: addressFilter.value,
        placeholder: 'חפש כתובת...',
      })
    }

    if (areaRange) {
      items.push({
        key: 'areaRange',
        label: 'שטח (מ״ר)',
        type: 'number-range',
        value: {
          min: areaRange.min,
          max: areaRange.max,
        },
        minPlaceholder: 'מינימום',
        maxPlaceholder: 'מקסימום',
        step: 1,
      })
    }

    return items
  }, [addressFilter, areaRange, data, filterOptions, filters?.source])

  const handleAdditionalFilterChange = (key: string, value: AdditionalFilterValue) => {
    if (key === 'source' && typeof value === 'string' && filters?.source?.onChange) {
      filters.source.onChange(value)
      return
    }

    if (key === 'address' && typeof value === 'string' && addressFilter) {
      addressFilter.onChange(value)
      return
    }

    if (
      key === 'areaRange' &&
      areaRange &&
      typeof value === 'object' &&
      value !== null &&
      !Array.isArray(value) &&
      ('min' in value || 'max' in value)
    ) {
      const nextValue = value as { min?: number; max?: number }
      areaRange.onChange({ min: nextValue.min, max: nextValue.max })
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
    <div
      className="surface-panel overflow-x-auto rtl"
      dir="rtl"
      aria-busy={loading}
    >
      {/* Integrated Toolbar */}
      <TableToolbar
        searchValue={searchValue}
        onSearchChange={(value) => {
          if (onSearchChange) {
            onSearchChange(value);
          }
        }}
        searchPlaceholder="חיפוש בעסקאות..."
        filters={{
          ...(onPriceMinChange
            ? {
                priceMin: {
                  value: priceMin,
                  onChange: onPriceMinChange,
                  label: 'מחיר מינימלי',
                  placeholder: '₪',
                  analyticsKey: 'transactions_price_min',
                },
              }
            : {}),
          ...(onPriceMaxChange
            ? {
                priceMax: {
                  value: priceMax,
                  onChange: onPriceMaxChange,
                  label: 'מחיר מקסימלי',
                  placeholder: '₪',
                  analyticsKey: 'transactions_price_max',
                },
              }
            : {}),
          ...(onPricePerSqmMinChange
            ? {
                pricePerSqmMin: {
                  value: pricePerSqmMin,
                  onChange: onPricePerSqmMinChange,
                  label: 'מחיר למ"ר מינימלי',
                  placeholder: '₪/מ"ר',
                  analyticsKey: 'transactions_price_per_sqm_min',
                },
              }
            : {}),
          ...(onPricePerSqmMaxChange
            ? {
                pricePerSqmMax: {
                  value: pricePerSqmMax,
                  onChange: onPricePerSqmMaxChange,
                  label: 'מחיר למ"ר מקסימלי',
                  placeholder: '₪/מ"ר',
                  analyticsKey: 'transactions_price_per_sqm_max',
                },
              }
            : {}),
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
                    <TableHead key={header.id} className="text-start">
                      {header.isPlaceholder ? null : (
                        <button
                          type="button"
                          onClick={header.column.getToggleSortingHandler()}
                          disabled={!header.column.getCanSort()}
                          className="flex w-full items-center justify-start gap-1 text-xs font-medium disabled:cursor-default"
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
            {loading ? (
              <TableSkeletonRows columnCount={columns.length} />
            ) : table.getRowModel().rows.length === 0 ? (
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
                    <TableCell key={cell.id} className="text-start">
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
