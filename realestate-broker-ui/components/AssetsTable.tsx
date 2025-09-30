'use client'
import * as React from 'react'
import { ColumnDef, flexRender, getCoreRowModel, useReactTable, ColumnResizeMode } from '@tanstack/react-table'
import type { Asset } from '@/lib/normalizers/asset'
import { fmtCurrency, fmtNumber, fmtPct } from '@/lib/utils'
import { Badge } from '@/components/ui/Badge'
import { Table, THead, TBody, TR, TH, TD } from '@/components/ui/table'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Trash2, Download, Bell, Eye, Settings, Search, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuContent, DropdownMenuCheckboxItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import AssetCard from './AssetCard'
import AlertRulesManager from '@/components/alerts/alert-rules-manager'
import TableToolbar from './TableToolbar'
import { useAnalytics } from '@/hooks/useAnalytics'
import ImageGallery from './ImageGallery'

function RiskCell({ flags }: { flags?: string[] }){
  if(!flags || flags.length===0) return <Badge variant='success'>ללא</Badge>;
  return <div className="flex gap-1 flex-wrap">{flags.map((f,i)=><Badge key={i} variant={f.includes('שימור')?'error':f.includes('אנטנה')?'warning':'neutral'}>{f}</Badge>)}</div>
}

function exportAssetsCsv(assets: Asset[], visibleColumns?: any[], trackFeatureUsage?: (feature: string, assetId?: number, meta?: Record<string, any>) => void) {
  if (assets.length === 0) return
  
  // Track export usage
  if (trackFeatureUsage) {
    trackFeatureUsage('export', undefined, {
      asset_count: assets.length,
      export_type: 'csv'
    })
  }
  
  // If visibleColumns is provided, use them; otherwise fall back to default columns
  const headers = visibleColumns ? 
    visibleColumns
      .filter(col => col.getCanHide() !== false && col.id !== 'select' && col.id !== 'actions')
      .map(col => col.columnDef.header as string)
    : ['id', 'address', 'city', 'type', 'price', 'pricePerSqm']
  
  const accessorKeys = visibleColumns ?
    visibleColumns
      .filter(col => col.getCanHide() !== false && col.id !== 'select' && col.id !== 'actions')
      .map(col => col.columnDef.accessorKey || col.id)
    : ['id', 'address', 'city', 'type', 'price', 'pricePerSqm']

  const csv = [
    headers.join(','),
    ...assets.map(a =>
      accessorKeys
        .map(key => {
          const value = key === 'docsCount' ? (a.documents?.length ?? 0) : (a as any)[key]
          return JSON.stringify(value ?? '')
        })
        .join(',')
    )
  ].join('\n')

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', 'assets.csv')
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function createColumns(onDelete?: (id: number) => void, onExport?: (asset: Asset) => void, onOpenAlert?: (assetId: number) => void): ColumnDef<Asset>[] {
  return [
  {
    id: 'select',
    header: ({ table }) => (
      <input
        type="checkbox"
        checked={table.getIsAllRowsSelected()}
        onChange={table.getToggleAllRowsSelectedHandler()}
        aria-label="בחר הכל"
        className="size-4 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      />
    ),
    cell: ({ row }) => (
      <input
        type="checkbox"
        checked={row.getIsSelected()}
        onClick={e => e.stopPropagation()}
        onChange={row.getToggleSelectedHandler()}
        aria-label={`בחר נכס ${row.original.address}`}
        className="size-4 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      />
    ),
    enableSorting: false,
    enableHiding: false
  },
  {
    header:'נכס',
    accessorKey:'address',
    cell: ({ row }) => (
      <div className="flex gap-3 items-start">
        {/* Image preview */}
        {row.original.images && row.original.images.length > 0 && (
          <div className="flex-shrink-0">
            <ImageGallery 
              images={row.original.images} 
              size="sm" 
              maxDisplay={1}
              showThumbnails={false}
            />
          </div>
        )}
        
        <div className="flex-1 min-w-0">
          <div className="font-semibold">
            <Link href={`/assets/${row.original.id}`}>{row.original.address}</Link>
          </div>
          <div className="text-xs text-sub">
              {row.original.city ?? '—'}
              {row.original.neighborhood ? ` · ${row.original.neighborhood}` : ''}
              {row.original.block ? ` · גוש ${row.original.block}` : ''}
              {row.original.parcel ? ` חלקה ${row.original.parcel}` : ''}
              {row.original.subparcel ? ` תת חלקה ${row.original.subparcel}` : ''}
              · {row.original.type ?? '—'} · {row.original.area !== undefined && row.original.area !== null ? `${fmtNumber(row.original.area)} מ"ר נטו` : '—'}
          </div>
        </div>
      </div>
    )
  },
  { header:'₪', accessorKey:'price', cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : fmtCurrency(v)}</span>
    } },
  { header:'₪/מ"ר', accessorKey:'pricePerSqm', cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : fmtNumber(v)}</span>
    } },
  { header:'Δ מול איזור', accessorKey:'deltaVsAreaPct', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge variant={typeof value === 'number' && value < 0 ? 'error' : 'neutral'}>{fmtPct(value)}</Badge>
    } },
  { header:'ימי שוק (אחוזון)', accessorKey:'domPercentile', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge>{!!value ? `P${value}` : '—'}</Badge>
    } },
  { header:'תחרות (1ק"מ)', accessorKey:'competition1km', cell: info => {
      const value = info.getValue() as string | undefined
      return <Badge>{value ?? '—'}</Badge>
    } },
  { header:'ייעוד', accessorKey:'zoning', cell: info => {
      const value = info.getValue() as string | undefined
      return <Badge>{value ?? '—'}</Badge>
    } },
  { header:'יתרת זכויות', accessorKey:'remainingRightsSqm', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge>{value !== undefined && value !== null ? `~+${fmtNumber(value)} מ"ר` : '—'}</Badge>
    } },
  { header:'תכנית', accessorKey:'program', cell: info => {
      const value = info.getValue() as string | undefined
      return <Badge>{value ?? '—'}</Badge>
    } },
  { header:'היתר עדכני', accessorKey:'lastPermitQ', cell: info => {
      const value = info.getValue() as string | undefined
      return <Badge>{value ?? '—'}</Badge>
    } },
  { header:'קבצים', id:'docsCount', accessorFn: row => row.documents?.length ?? 0, cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge>{fmtNumber(value)}</Badge>
    } },
  { header:'רעש', accessorKey:'noiseLevel', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge>{!!value ? `${value}/5` : '—'}</Badge>
    } },
  { header:'אנטנה (מ")', accessorKey:'antennaDistanceM', cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : fmtNumber(v)}</span>
    } },
  { header:'שטחי ציבור ≤300מ"', accessorKey:'greenWithin300m', cell: info => {
      const value = info.getValue() as boolean | undefined
      return <Badge variant={value === undefined ? 'neutral' : value ? 'success' : 'error'}>{value === undefined ? '—' : value ? 'כן' : 'לא'}</Badge>
    } },
  { header:'מקלט (מ")', accessorKey:'shelterDistanceM', cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : fmtNumber(v)}</span>
    } },
  { header:'סיכון', accessorKey:'riskFlags', cell: info => <RiskCell flags={info.getValue() as string[]}/> },
  { header:'סטטוס נכס', accessorKey:'assetStatus', cell: info => {
    const status = info.getValue() as string
    if (!status) return <Badge variant="neutral">—</Badge>
    const variant = status === 'done' ? 'success' : status === 'failed' ? 'error' : 'warning'
    const label = status === 'done' ? 'מוכן' : status === 'failed' ? 'שגיאה' : status === 'enriching' ? 'מתעשר' : 'ממתין'
    return <Badge variant={variant}>{label}</Badge>
  }},
  { header:'מחיר מודל', accessorKey:'modelPrice', cell: info => <span className="font-mono">{fmtCurrency(info.getValue() as number)}</span> },
  { header:'פער למחיר', accessorKey:'priceGapPct', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge variant={typeof value === 'number' && value > 0 ? 'warning' : 'success'}>{fmtPct(value)}</Badge>
    } },
  { header:'רמת ביטחון', accessorKey:'confidencePct', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge>{!!value ? `${value}%` : '—'}</Badge>
    } },
  { header:'שכ"ד', accessorKey:'rentEstimate', cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : fmtCurrency(v)}</span>
    } },
    { header:'תשואה', accessorKey:'capRatePct', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge>{typeof value === 'number' ? `${value.toFixed(1)}%` : '—'}</Badge>
    } },
    { 
      header:'—', 
      id:'actions', 
      enableResizing: false,
      size: 0,
      minSize: 0,
      maxSize: 0,
      cell: ({ row }) => (
        <div className="flex gap-2">
          <Link 
            className="text-blue-600 hover:text-blue-800 underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded p-1"
            href={`/assets/${row.original.id}`}
            aria-label={`צפה בפרטי נכס ${row.original.address}`}
            title="צפה בפרטי נכס"
          >
            <Eye className="h-4 w-4" />
          </Link>
          {onOpenAlert && (
            <button
              onClick={e => { e.stopPropagation(); onOpenAlert(row.original.id) }}
              className="text-amber-600 hover:text-amber-800 underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded p-1"
              title="הגדר התראות לנכס זה"
              aria-label={`הגדר התראות לנכס ${row.original.address}`}
            >
              <Bell className="h-4 w-4" />
            </button>
          )}
          {onExport && (
            <button
              onClick={e => { e.stopPropagation(); onExport(row.original) }}
              className="text-green-600 hover:text-green-800 underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded p-1"
              aria-label={`ייצא נכס ${row.original.address}`}
              title="ייצא נכס"
            >
              <Download className="h-4 w-4" />
            </button>
          )}
          {onDelete && (
            <button 
              onClick={e => { 
                e.stopPropagation(); 
                onDelete(row.original.id) 
              }} 
              className="text-red-600 hover:text-red-800 underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded p-1"
              aria-label={`מחק נכס ${row.original.address}`}
              title="מחק נכס"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      ) 
    }
  ]
}

interface AssetsTableProps {
  data?: Asset[]
  loading?: boolean
  onDelete?: (id: number) => void
  // Toolbar props
  searchValue?: string
  onSearchChange?: (value: string) => void
  filters?: {
    city: {
      value: string
      onChange: (value: string) => void
      options: string[]
    }
    type: {
      value: string
      onChange: (value: string) => void
      options: string[]
    }
    priceMin: {
      value: number | undefined
      onChange: (value: number | undefined) => void
    }
    priceMax: {
      value: number | undefined
      onChange: (value: number | undefined) => void
    }
    neighborhood?: {
      value: string
      onChange: (value: string) => void
      options: string[]
    }
    zoning?: {
      value: string
      onChange: (value: string) => void
      options: string[]
    }
    risk?: {
      value: string
      onChange: (value: string) => void
      options: Array<{ value: string; label: string }>
    }
    documents?: {
      value: string
      onChange: (value: string) => void
      options: Array<{ value: string; label: string }>
    }
    status?: {
      value: string
      onChange: (value: string) => void
      options: Array<{ value: string; label: string; count?: number }>
    }
    rentalSale?: {
      value: string
      onChange: (value: string) => void
      options: Array<{ value: string; label: string }>
    }
    userAssets?: {
      value: string
      onChange: (value: string) => void
      options: Array<{ value: string; label: string }>
    }
    buildingType?: {
      value: string
      onChange: (value: string) => void
      options: string[]
    }
    floorMin?: {
      value: number | undefined
      onChange: (value: number | undefined) => void
    }
    floorMax?: {
      value: number | undefined
      onChange: (value: number | undefined) => void
    }
    areaMin?: {
      value: number | undefined
      onChange: (value: number | undefined) => void
    }
    areaMax?: {
      value: number | undefined
      onChange: (value: number | undefined) => void
    }
    rooms?: {
      value: string
      onChange: (value: string) => void
      options: Array<{ value: string; label: string }>
    }
    features?: {
      value: string
      onChange: (value: string) => void
      options: Array<{ value: string; label: string }>
    }
    pricePerSqmMin?: {
      value: number | undefined
      onChange: (value: number | undefined) => void
    }
    pricePerSqmMax?: {
      value: number | undefined
      onChange: (value: number | undefined) => void
    }
    remainingRightsMin?: {
      value: number | undefined
      onChange: (value: number | undefined) => void
    }
    remainingRightsMax?: {
      value: number | undefined
      onChange: (value: number | undefined) => void
    }
    block?: {
      value: string
      onChange: (value: string) => void
      options: string[]
    }
    parcel?: {
      value: string
      onChange: (value: string) => void
      options: string[]
    }
  }
  onRefresh?: () => void
  onAddNew?: () => void
  viewMode?: 'table' | 'cards' | 'map'
  onViewModeChange?: (mode: 'table' | 'cards' | 'map') => void
  bulkActions?: Array<{
    label: string
    action: () => void
    icon?: React.ReactNode
    disabled?: boolean
  }>
}

const COLUMN_PREFERENCES_KEY = 'assets-table-column-preferences'
const COLUMN_SIZING_KEY = 'assets-table-column-sizing'

export default function AssetsTable({ 
  data = [], 
  loading = false, 
  onDelete,
  searchValue = '',
  onSearchChange,
  filters,
  onRefresh,
  onAddNew,
  viewMode = 'table',
  onViewModeChange
}: AssetsTableProps){
  const { trackFeatureUsage, trackSearch } = useAnalytics()
  const router = useRouter()
  const [rowSelection, setRowSelection] = React.useState({})
  const [columnVisibility, setColumnVisibility] = React.useState<Record<string, boolean>>(() => {
    // Load saved column preferences from localStorage on component mount
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem(COLUMN_PREFERENCES_KEY)
        return saved ? JSON.parse(saved) : {}
      } catch (error) {
        console.warn('Failed to load column preferences:', error)
        return {}
      }
    }
    return {}
  })
  const [columnSizing, setColumnSizing] = React.useState<Record<string, number>>(() => {
    // Load saved column sizing from localStorage on component mount
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem(COLUMN_SIZING_KEY)
        return saved ? JSON.parse(saved) : {}
      } catch (error) {
        console.warn('Failed to load column sizing:', error)
        return {}
      }
    }
    return {}
  })
  const [alertModalOpen, setAlertModalOpen] = React.useState(false)
  const [selectedAssetId, setSelectedAssetId] = React.useState<number | null>(null)
  const [mounted, setMounted] = React.useState(false)

  // Handle hydration mismatch
  React.useEffect(() => {
    setMounted(true)
  }, [])

  const handleOpenAlertModal = React.useCallback((assetId: number) => {
    setSelectedAssetId(assetId)
    setAlertModalOpen(true)
  }, [])

  // Save column preferences to localStorage whenever they change
  const handleColumnVisibilityChange = React.useCallback((updaterOrValue: any) => {
    setColumnVisibility(prev => {
      const newVisibility = typeof updaterOrValue === 'function' ? updaterOrValue(prev) : updaterOrValue
      
      // Save to localStorage
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem(COLUMN_PREFERENCES_KEY, JSON.stringify(newVisibility))
        } catch (error) {
          console.warn('Failed to save column preferences:', error)
        }
      }
      
      return newVisibility
    })
  }, [])

  // Save column sizing to localStorage whenever they change
  const handleColumnSizingChange = React.useCallback((updaterOrValue: any) => {
    setColumnSizing(prev => {
      const newSizing = typeof updaterOrValue === 'function' ? updaterOrValue(prev) : updaterOrValue
      
      // Save to localStorage
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem(COLUMN_SIZING_KEY, JSON.stringify(newSizing))
        } catch (error) {
          console.warn('Failed to save column sizing:', error)
        }
      }
      
      return newSizing
    })
  }, [])

  // Create a ref to store the table instance
  const tableRef = React.useRef<any>(null)

  // Define handleExportSingle that uses the table ref
  const handleExportSingle = React.useCallback((asset: Asset) => {
    if (tableRef.current) {
      exportAssetsCsv([asset], tableRef.current.getVisibleLeafColumns(), trackFeatureUsage)
    }
  }, [trackFeatureUsage])

  // Create columns with handleExportSingle - only after mounted to prevent hydration mismatch
  const columns = React.useMemo(() => {
    if (!mounted) return []
    return createColumns(onDelete, handleExportSingle, handleOpenAlertModal)
  }, [mounted, onDelete, handleExportSingle, handleOpenAlertModal])

  const table = useReactTable({
    data,
    columns,
    state: { 
      rowSelection,
      columnVisibility,
      columnSizing
    },
    enableRowSelection: true,
    enableColumnResizing: true,
    columnResizeMode: 'onChange' as ColumnResizeMode,
    columnResizeDirection: 'rtl',
    onRowSelectionChange: setRowSelection,
    onColumnVisibilityChange: handleColumnVisibilityChange,
    onColumnSizingChange: handleColumnSizingChange,
    getCoreRowModel: getCoreRowModel()
  })

  // Store table instance in ref
  React.useEffect(() => {
    tableRef.current = table
  }, [table])

  const handleRowClick = (asset: Asset) => {
    router.push(`/assets/${asset.id}`)
  }

  const handleExportSelected = () => {
    const selected = table.getSelectedRowModel().rows.map(r => r.original)
    exportAssetsCsv(selected, table.getVisibleLeafColumns(), trackFeatureUsage)
  }

  const anySelected = table.getSelectedRowModel().rows.length > 0

  // Prepare columns for toolbar
  const toolbarColumns = table.getAllColumns()
    .filter(column => column.getCanHide())
    .map(column => ({
      id: column.id,
      header: column.columnDef.header as string,
      visible: column.getIsVisible(),
      toggle: (value: boolean) => column.toggleVisibility(value)
    }))

  const additionalFilters = React.useMemo(() => {
    if (!filters) return []
    const items: Array<{ key: string; label: string; value: string; options?: Array<{ value: string; label: string; count?: number }> }> = []

    if (filters.neighborhood) {
      items.push({
        key: 'neighborhood',
        label: 'שכונה',
        value: filters.neighborhood.value,
        options: filters.neighborhood.options.map(option => ({ value: option, label: option }))
      })
    }

    if (filters.zoning) {
      items.push({
        key: 'zoning',
        label: 'ייעוד',
        value: filters.zoning.value,
        options: filters.zoning.options.map(option => ({ value: option, label: option }))
      })
    }

    if (filters.risk) {
      items.push({
        key: 'risk',
        label: 'סיכון',
        value: filters.risk.value,
        options: filters.risk.options.map(option => ({ value: option.value, label: option.label }))
      })
    }

    if (filters.documents) {
      items.push({
        key: 'documents',
        label: 'מסמכים',
        value: filters.documents.value,
        options: filters.documents.options.map(option => ({ value: option.value, label: option.label }))
      })
    }

    if (filters.rentalSale) {
      items.push({
        key: 'rentalSale',
        label: 'השכרה/מכירה',
        value: filters.rentalSale.value,
        options: filters.rentalSale.options.map(option => ({ value: option.value, label: option.label }))
      })
    }

    if (filters.userAssets) {
      items.push({
        key: 'userAssets',
        label: 'נכסים שלי',
        value: filters.userAssets.value,
        options: filters.userAssets.options.map(option => ({ value: option.value, label: option.label }))
      })
    }

    if (filters.buildingType) {
      items.push({
        key: 'buildingType',
        label: 'סוג בניין',
        value: filters.buildingType.value,
        options: filters.buildingType.options.map(option => ({ value: option, label: option }))
      })
    }

    if (filters.rooms) {
      items.push({
        key: 'rooms',
        label: 'חדרים',
        value: filters.rooms.value,
        options: filters.rooms.options.map(option => ({ value: option.value, label: option.label }))
      })
    }

    if (filters.features) {
      items.push({
        key: 'features',
        label: 'תכונות',
        value: filters.features.value,
        options: filters.features.options.map(option => ({ value: option.value, label: option.label }))
      })
    }

    if (filters.block) {
      items.push({
        key: 'block',
        label: 'גוש',
        value: filters.block.value,
        options: filters.block.options.map(option => ({ value: option, label: option }))
      })
    }

    if (filters.parcel) {
      items.push({
        key: 'parcel',
        label: 'חלקה',
        value: filters.parcel.value,
        options: filters.parcel.options.map(option => ({ value: option, label: option }))
      })
    }

    return items
  }, [filters])

  const handleAdditionalFilterChange = React.useCallback((key: string, value: string) => {
    if (!filters) return
    const track = (filterType: string, filterValue: string) => {
      trackFeatureUsage('filter', undefined, { filter_type: filterType, value: filterValue })
    }

    switch (key) {
      case 'neighborhood':
        filters.neighborhood?.onChange(value)
        track('neighborhood', value)
        break
      case 'zoning':
        filters.zoning?.onChange(value)
        track('zoning', value)
        break
      case 'risk':
        filters.risk?.onChange(value)
        track('risk', value)
        break
      case 'documents':
        filters.documents?.onChange(value)
        track('documents', value)
        break
      case 'rentalSale':
        filters.rentalSale?.onChange(value)
        track('rentalSale', value)
        break
      case 'userAssets':
        filters.userAssets?.onChange(value)
        track('userAssets', value)
        break
      case 'buildingType':
        filters.buildingType?.onChange(value)
        track('buildingType', value)
        break
      case 'rooms':
        filters.rooms?.onChange(value)
        track('rooms', value)
        break
      case 'features':
        filters.features?.onChange(value)
        track('features', value)
        break
      case 'block':
        filters.block?.onChange(value)
        track('block', value)
        break
      case 'parcel':
        filters.parcel?.onChange(value)
        track('parcel', value)
        break
      default:
        break
    }
  }, [filters, trackFeatureUsage])

  // Don't render table until mounted to prevent hydration mismatch
  if (!mounted) {
    return (
      <div className="block">
        <div className="rounded-xl border border-border bg-card overflow-x-auto">
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="block">
        <div className="rounded-xl border border-border bg-card overflow-x-auto">
          {/* Integrated Toolbar */}
          <TableToolbar
            searchValue={searchValue}
            onSearchChange={(value) => {
              if (onSearchChange) {
                onSearchChange(value)
              }
              // Track search usage
              if (value.trim()) {
                trackSearch(value.trim(), {}, 0)
              }
            }}
            searchPlaceholder="חיפוש בכתובת או עיר..."
            filters={filters || {
              city: { value: 'all', onChange: () => {}, options: [] },
              type: { value: 'all', onChange: () => {}, options: [] },
              priceMin: { value: undefined, onChange: () => {} },
              priceMax: { value: undefined, onChange: () => {} }
            }}
            additionalFilters={additionalFilters}
            onAdditionalFilterChange={handleAdditionalFilterChange}
            columns={toolbarColumns}
            onExportSelected={handleExportSelected}
            onExportAll={() => exportAssetsCsv(data, table.getVisibleLeafColumns(), trackFeatureUsage)}
            selectedCount={table.getSelectedRowModel().rows.length}
            totalCount={data.length}
            viewMode={viewMode}
            onViewModeChange={onViewModeChange || (() => {})}
            onRefresh={onRefresh || (() => {})}
            onAddNew={onAddNew}
            loading={loading}
            statusFilters={filters?.status ? {
              value: filters.status.value,
              onChange: (value: string) => {
                filters.status?.onChange(value)
                trackFeatureUsage('filter', undefined, { filter_type: 'status', value })
              },
              options: filters.status.options
            } : undefined}
          />
          {/* Table view - show when viewMode is 'table' */}
          {viewMode === 'table' && (
            <div className="overflow-x-auto" role="region" aria-label="טבלת נכסים">
              <Table style={{ width: '100%', minWidth: table.getCenterTotalSize() }}>
                <THead>
                  <TR className="group">
                    {table.getFlatHeaders().map(h=>(
                      <TH 
                        key={h.id} 
                        className={`relative ${h.column.id==='address'?'sticky right-0 bg-card z-10':''} ${
                          h.column.getCanResize() ? 'hover:bg-muted/30' : ''
                        } ${h.column.id === 'actions' ? 'w-full' : ''}`}
                        style={{ width: h.column.id === 'actions' ? 'auto' : h.getSize() }}
                      >
                        <div className="flex items-center justify-between w-full">
                          <div className="flex-1">
                            {flexRender(h.column.columnDef.header, h.getContext())}
                          </div>
                          {h.column.getCanResize() && (
                            <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 ml-2">
                              <div className="w-1 h-4 bg-muted-foreground/40 rounded-full"></div>
                            </div>
                          )}
                        </div>
                        <div
                          className={`absolute top-0 left-0 h-full w-2 cursor-e-resize select-none touch-none ${
                            h.column.getCanResize() 
                              ? 'bg-border/30 hover:bg-primary/60 hover:w-3 transition-all duration-200' 
                              : 'bg-transparent'
                          }`}
                          onMouseDown={h.getResizeHandler()}
                          onTouchStart={h.getResizeHandler()}
                          style={{
                            transform: 'translateX(-50%)',
                            zIndex: 1
                          }}
                          title="גרור לשינוי רוחב העמודה"
                        />
                      </TH>
                    ))}
                  </TR>
                </THead>
                <TBody>
                  {table.getRowModel().rows.length === 0 ? (
                    <TR>
                      <TD colSpan={table.getFlatHeaders().length} className="text-center py-12">
                        <div className="flex flex-col items-center justify-center space-y-4">
                          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
                            <Search className="h-8 w-8 text-muted-foreground" />
                          </div>
                          <div className="text-center">
                            <h3 className="text-lg font-semibold text-foreground">לא נמצאו נכסים</h3>
                            <p className="text-muted-foreground">
                              {searchValue || (filters && (filters.city.value !== 'all' || filters.type.value !== 'all' || filters.priceMin.value || filters.priceMax.value))
                                ? 'נסה לשנות את הסינון או החיפוש'
                                : 'אין נכסים זמינים כרגע'}
                            </p>
                            {!searchValue && filters && filters.city.value === 'all' && filters.type.value === 'all' && !filters.priceMin.value && !filters.priceMax.value && onAddNew && (
                              <Button className="mt-4" onClick={onAddNew}>
                                <Plus className="h-4 w-4 ms-2" />
                                הוסף נכס ראשון
                              </Button>
                            )}
                          </div>
                        </div>
                      </TD>
                    </TR>
                  ) : (
                    table.getRowModel().rows.map(row=>(
                      <TR 
                        key={row.id} 
                        className="clickable-row focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" 
                        onClick={() => handleRowClick(row.original)}
                        tabIndex={0}
                        role="button"
                        aria-label={`נכס ${row.original.address} - לחץ לפרטים`}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault()
                            handleRowClick(row.original)
                          }
                        }}
                      >
                        {row.getVisibleCells().map(cell=>(
                          <TD 
                            key={cell.id} 
                            className={`${cell.column.id==='address'?'sticky right-0 bg-card z-10':''} ${cell.column.id === 'actions' ? 'w-full' : ''}`}
                            style={{ width: cell.column.id === 'actions' ? 'auto' : cell.column.getSize() }}
                          >
                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                          </TD>
                        ))}
                      </TR>
                    ))
                  )}
                </TBody>
              </Table>
            </div>
          )}
        </div>
      </div>
      
      {/* Card view - show when viewMode is 'cards' */}
      {viewMode === 'cards' && (
        <div className="space-y-2">
          {data.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
                <Search className="h-8 w-8 text-muted-foreground" />
              </div>
              <div className="text-center">
                <h3 className="text-lg font-semibold text-foreground">לא נמצאו נכסים</h3>
                <p className="text-muted-foreground">
                  {searchValue || (filters && (filters.city.value !== 'all' || filters.type.value !== 'all' || filters.priceMin.value || filters.priceMax.value))
                    ? 'נסה לשנות את הסינון או החיפוש'
                    : 'אין נכסים זמינים כרגע'}
                </p>
                {!searchValue && filters && filters.city.value === 'all' && filters.type.value === 'all' && !filters.priceMin.value && !filters.priceMax.value && onAddNew && (
                  <Button className="mt-4" onClick={onAddNew}>
                    <Plus className="h-4 w-4 ms-2" />
                    הוסף נכס ראשון
                  </Button>
                )}
              </div>
            </div>
          ) : (
            data.map(asset => (
              <AssetCard key={asset.id} asset={asset} />
            ))
          )}
        </div>
      )}

      {/* Alert Modal */}
      <Dialog open={alertModalOpen} onOpenChange={setAlertModalOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>הגדרת התראות לנכס</DialogTitle>
          </DialogHeader>
          {selectedAssetId && (
            <AlertRulesManager assetId={selectedAssetId} />
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
