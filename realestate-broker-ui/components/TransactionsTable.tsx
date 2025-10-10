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
import { Calendar, MapPin, Home, Building } from 'lucide-react'
import TableToolbar from '@/components/TableToolbar'
import { useAnalytics } from '@/hooks/useAnalytics'

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
            case 'internal': return 'מאגר פנימי'
            default: return source || 'לא ידוע'
          }
        }
        const getSourceVariant = (source: string) => {
          switch (source) {
            case 'collected_government': return 'default'
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
}: TransactionsTableProps) {
  const { trackFeatureUsage } = useAnalytics()
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = useState({})

  const columns = useMemo(() => createColumns(), [])

  // Filter data based on search and filters
  const filteredData = useMemo(() => {
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
  }, [data, searchValue, filters])

  const table = useReactTable({
    data: filteredData,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
    },
  })

  // Additional filters for the toolbar
  const additionalFilters = useMemo(() => {
    const sources = Array.from(new Set(data.map(t => t.source).filter(Boolean)))
    const areas = Array.from(new Set(data.map(t => t.area).filter((area): area is number => typeof area === 'number'))).sort((a, b) => a - b)
    
    // Create area ranges
    const areaRanges = []
    if (areas.length > 0) {
      const minArea = Math.min(...areas)
      const maxArea = Math.max(...areas)
      const step = Math.ceil((maxArea - minArea) / 5)
      
      for (let i = 0; i < 5; i++) {
        const start = minArea + (i * step)
        const end = i === 4 ? maxArea : start + step - 1
        areaRanges.push(`${start}-${end}`)
      }
    }

    return [
      {
        key: 'source',
        label: 'מקור',
        options: [
          { value: 'all', label: 'הכל' },
          ...sources.map(source => ({
            value: source,
            label: source === 'collected_government' ? 'ממשלתי' : 'מאגר פנימי'
          }))
        ]
      },
      {
        key: 'area',
        label: 'שטח',
        options: [
          { value: 'all', label: 'הכל' },
          ...areaRanges.map(range => ({
            value: range,
            label: `${range} מ״ר`
          }))
        ]
      }
    ]
  }, [data])

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
        totalCount={filteredData.length}
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
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id} className="text-right rtl:text-right">
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
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
    </div>
  )
}
