'use client'
import * as React from 'react'
import { ColumnDef, flexRender, getCoreRowModel, getPaginationRowModel, useReactTable, ColumnResizeMode, PaginationState, Updater } from '@tanstack/react-table'
import type { Asset } from '@/lib/normalizers/asset'
import { fmtCurrency, fmtNumber, fmtPct } from '@/lib/utils'
import { Badge } from '@/components/ui/Badge'
import { Table, THead, TBody, TR, TH, TD } from '@/components/ui/table'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Trash2, Download, Bell, Eye, Search, Plus, Phone, Play, Star, StarOff, Handshake } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import AssetCard from './AssetCard'
import AlertRulesManager from '@/components/alerts/alert-rules-manager'
import TableToolbar, { AdditionalFilterValue, AdditionalFilterConfig } from './TableToolbar'
import TablePagination from '@/components/TablePagination'
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

const formatListingTypeLabel = (value?: string | null) => {
  if (!value) return '—'
  const normalized = value.toLowerCase()
  if (normalized === 'rent') return 'השכרה'
  if (normalized === 'sale') return 'מכירה'
  if (normalized === 'commercial') return 'מסחרי'
  return value
}

const formatAdTypeLabel = (value?: string | null) => {
  if (!value) return '—'
  const normalized = value.toLowerCase()
  if (normalized === 'private') return 'פרטי'
  if (normalized === 'broker' || normalized === 'agency' || normalized === 'agent') return 'מתווך'
  return value
}

function createColumns({
  onDelete,
  onExport,
  onOpenAlert,
  onToggleWatch,
  watchLoadingIds,
}: {
  onDelete?: (id: number) => void
  onExport?: (asset: Asset) => void
  onOpenAlert?: (assetId: number) => void
  onToggleWatch?: (asset: Asset) => void
  watchLoadingIds?: Set<number>
}): ColumnDef<Asset>[] {
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
          <div
            className="flex-shrink-0"
            onClick={event => event.stopPropagation()}
            onMouseDown={event => event.stopPropagation()}
            onTouchStart={event => event.stopPropagation()}
            onKeyDown={event => {
              if (
                event.key === 'Enter' ||
                event.key === ' ' ||
                event.key === 'Spacebar' ||
                event.key === 'Space'
              ) {
                event.stopPropagation()
              }
            }}
          >
            <ImageGallery 
              images={row.original.images} 
              size="sm" 
              maxDisplay={1}
              showThumbnails={false}
            />
          </div>
        )}
        
        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-2 text-base font-semibold">
            <Link href={`/assets/${row.original.id}`} className="flex-1 min-w-0">
              <span className="block truncate">{row.original.address}</span>
            </Link>
            {row.original.isWatched && (
              <Badge variant="outline" className="flex items-center gap-1 text-amber-600 border-amber-200 bg-amber-50">
                <Star className="h-3 w-3 fill-current" />
                במעקב
              </Badge>
            )}
          </div>
          <div className="text-xs text-sub">
              {row.original.city ?? '—'}
              {row.original.neighborhood ? ` · ${row.original.neighborhood}` : ''}
              {row.original.block ? ` · גוש ${row.original.block}` : ''}
              {row.original.parcel ? ` חלקה ${row.original.parcel}` : ''}
              {row.original.subparcel ? ` תת חלקה ${row.original.subparcel}` : ''}
              · {row.original.type ?? '—'} · {row.original.area !== undefined && row.original.area !== null ? `${fmtNumber(row.original.area)} מ"ר` : '—'}
              {row.original.subparcelArea && ` · ${fmtNumber(row.original.subparcelArea)} מ"ר מגרש`}
              {row.original.builtArea && ` · ${fmtNumber(row.original.builtArea)} מ"ר בנוי`}
              {row.original.isCommercial && (
                <>
                  {' · '}
                  <Badge variant="secondary" className="text-[10px] font-normal px-2 py-0.5">
                    מסחרי
                  </Badge>
                </>
              )}
          </div>
        </div>
      </div>
    )
  },
  {
    header: 'עיר',
    accessorKey: 'city',
    cell: info => {
      const value = info.getValue() as string | null | undefined
      return <span>{value ?? '—'}</span>
    },
  },
  {
    header: 'רחוב',
    accessorKey: 'street',
    cell: info => {
      const value = info.getValue() as string | null | undefined
      return <span>{value ?? '—'}</span>
    },
  },
  {
    header: 'מס׳',
    id: 'number',
    accessorFn: row => row.number ?? null,
    cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : fmtNumber(v)}</span>
    },
  },
  {
    header: 'דירה',
    accessorKey: 'apartment',
    cell: info => {
      const value = info.getValue() as string | number | null | undefined
      return <span>{value == null || value === '' ? '—' : String(value)}</span>
    },
  },
  {
    header: 'גוש',
    accessorKey: 'block',
    cell: info => {
      const value = info.getValue() as string | null | undefined
      return <span>{value ?? '—'}</span>
    },
  },
  {
    header: 'חלקה',
    accessorKey: 'parcel',
    cell: info => {
      const value = info.getValue() as string | null | undefined
      return <span>{value ?? '—'}</span>
    },
  },
  {
    header: 'תת חלקה',
    accessorKey: 'subparcel',
    cell: info => {
      const value = info.getValue() as string | null | undefined
      return <span>{value ?? '—'}</span>
    },
  },
  {
    header: 'מ"ר נטו',
    id: 'area',
    accessorFn: row => row.area ?? row.primaryListing?.size ?? null,
    cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : `${fmtNumber(v)} מ"ר`}</span>
    },
  },
  {
    header: 'מ"ר כולל',
    accessorKey: 'totalArea',
    cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : `${fmtNumber(v)} מ"ר`}</span>
    },
  },
  {
    header: 'מ"ר מגרש',
    accessorKey: 'subparcelArea',
    cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : `${fmtNumber(v)} מ"ר`}</span>
    },
  },
  {
    header: 'מ"ר בנוי',
    accessorKey: 'builtArea',
    cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : `${fmtNumber(v)} מ"ר`}</span>
    },
  },
  {
    header: 'קומה',
    id: 'floor',
    accessorFn: row => row.floor ?? row.primaryListing?.floor ?? null,
    cell: info => {
      const v = info.getValue() as number | string | null | undefined
      return <span>{v == null || v === '' ? '—' : String(v)}</span>
    },
  },
  {
    header: 'סה"כ קומות',
    accessorKey: 'totalFloors',
    cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : fmtNumber(v)}</span>
    },
  },
  {
    header: 'סוג עסקה',
    id: 'listingType',
    accessorFn: row => row.listingType ?? row.primaryListing?.listingType ?? null,
    cell: info => {
      const value = info.getValue() as string | null | undefined
      return <Badge>{formatListingTypeLabel(value)}</Badge>
    },
  },
  {
    header: 'סוג מפרסם',
    id: 'adType',
    accessorFn: row => row.adType ?? row.primaryListing?.adType ?? null,
    cell: info => {
      const value = info.getValue() as string | null | undefined
      return <Badge>{formatAdTypeLabel(value)}</Badge>
    },
  },
  {
    header: 'איש קשר',
    id: 'contact',
    cell: ({ row }) => {
      const name = row.original.contactName ?? row.original.primaryListing?.contactName ?? row.original.contactInfo?.name ?? null
      const phone =
        row.original.contactPhone ??
        row.original.primaryListing?.contactPhone ??
        row.original.contactInfo?.phone ??
        row.original.contactInfo?.brokerPhone ??
        null

      if (!name && !phone) {
        return <span>—</span>
      }

      const sanitizedPhone = phone ? phone.replace(/[^+\d]/g, '') : ''

      return (
        <div className="flex flex-col gap-1 text-xs">
          {name && <span className="font-medium text-foreground">{name}</span>}
          {phone && (
            <a
              href={sanitizedPhone ? `tel:${sanitizedPhone}` : undefined}
              className="inline-flex items-center gap-1 text-primary hover:underline"
              onClick={event => event.stopPropagation()}
            >
              <Phone className="h-3 w-3" />
              <span dir="ltr">{phone}</span>
            </a>
          )}
        </div>
      )
    },
  },
  {
    header: 'נמכר לאחרונה',
    id: 'recentDeal',
    accessorFn: row => row.recentDeal ?? row.primaryListing?.recentDeal ?? null,
    cell: info => {
      const value = info.getValue() as boolean | null | undefined
      if (value === null || value === undefined) {
        return <Badge variant="neutral">—</Badge>
      }
      return <Badge variant={value ? 'success' : 'neutral'}>{value ? 'כן' : 'לא'}</Badge>
    },
  },
  {
    header: 'וידאו',
    id: 'videoUrl',
    cell: ({ row }) => {
      const videoUrl = row.original.videoUrl ?? row.original.primaryListing?.videoUrl
      if (!videoUrl) {
        return <span>—</span>
      }
      return (
        <Button
          variant="ghost"
          size="sm"
          onClick={event => {
            event.stopPropagation()
            window.open(videoUrl, '_blank', 'noopener')
          }}
          className="me-0"
          aria-label="פתח וידאו"
        >
          <Play className="h-4 w-4" />
        </Button>
      )
    },
  },
  { header:'₪', accessorKey:'price', cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : fmtCurrency(v)}</span>
    } },
  { header:'₪ שכ"ד', accessorKey:'rentPrice', cell: info => {
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
  { header:'שכ"ד מוערך', accessorKey:'rentEstimate', cell: info => {
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
      cell: ({ row }) => {
        const watched = row.original.isWatched === true
        const watchLoading = watchLoadingIds?.has(row.original.id) ?? false
        const watchTitle = watched ? 'הסר מרשימת המעקב' : 'הוסף לרשימת המעקב'
        return (
          <div className="flex gap-2">
            <Link 
              className="text-blue-600 hover:text-blue-800 underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded p-1"
              href={`/assets/${row.original.id}`}
              aria-label={`צפה בפרטי נכס ${row.original.address}`}
              title="צפה בפרטי נכס"
            >
              <Eye className="h-4 w-4" />
            </Link>
            <Link
              className="text-indigo-600 hover:text-indigo-800 underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded p-1"
              href={`/assets/${row.original.id}/deal`}
              onClick={e => e.stopPropagation()}
              aria-label={`פתח סביבת עסקה לנכס ${row.original.address}`}
              title="סביבת עסקה"
            >
              <Handshake className="h-4 w-4" />
            </Link>
            {onToggleWatch && (
              <button
                type="button"
                onClick={e => { 
                  e.stopPropagation()
                  onToggleWatch(row.original) 
                }}
                className={`rounded p-1 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${
                  watched
                    ? 'text-amber-500 hover:text-amber-600'
                    : 'text-muted-foreground hover:text-amber-500'
                } ${watchLoading ? 'pointer-events-none opacity-60' : ''}`}
                title={watchTitle}
                aria-label={watchTitle}
                aria-pressed={watched}
                disabled={watchLoading}
              >
                {watched ? (
                  <Star className="h-4 w-4" fill="currentColor" />
                ) : (
                  <StarOff className="h-4 w-4" />
                )}
              </button>
            )}
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
    }
  ]
}

type AssetsTableBulkAction = {
  label: string
  action: (selectedAssets: Asset[], helpers: { clearSelection: () => void }) => void | Promise<void>
  icon?: React.ReactNode
  disabled?: boolean
}

type NumberRangeFilterConfig = {
  value: { min?: number; max?: number }
  onChange: (value: { min?: number; max?: number }) => void
  minPlaceholder?: string
  maxPlaceholder?: string
  step?: number
}

interface AssetsTableProps {
  data?: Asset[]
  loading?: boolean
  onDelete?: (id: number) => void
  onToggleWatch?: (asset: Asset) => void
  watchingAssetIds?: Set<number>
  onExportAllRequest?: () => Promise<Asset[]>
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
    adType?: {
      value: string
      onChange: (value: string) => void
      options: Array<{ value: string; label: string }>
    }
    commercial?: {
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
    bedrooms?: NumberRangeFilterConfig
    bathrooms?: NumberRangeFilterConfig
    totalFloors?: NumberRangeFilterConfig
    totalArea?: NumberRangeFilterConfig
    balconyArea?: NumberRangeFilterConfig
    parkingSpaces?: NumberRangeFilterConfig
    yearBuilt?: NumberRangeFilterConfig
    rentPrice?: NumberRangeFilterConfig
    rentEstimate?: NumberRangeFilterConfig
    priceGapPct?: NumberRangeFilterConfig
    capRatePct?: NumberRangeFilterConfig
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
    renovated?: {
      value: string
      onChange: (value: string) => void
      options: Array<{ value: string; label: string }>
    }
    furnished?: {
      value: string
      onChange: (value: string) => void
      options: Array<{ value: string; label: string }>
    }
    airConditioning?: {
      value: string
      onChange: (value: string) => void
      options: Array<{ value: string; label: string }>
    }
    storageRoom?: {
      value: string
      onChange: (value: string) => void
      options: Array<{ value: string; label: string }>
    }
    hasElevator?: {
      value: string
      onChange: (value: string) => void
      options: Array<{ value: string; label: string }>
    }
  }
  onRefresh?: () => void
  onAddNew?: () => void
  extraActions?: React.ReactNode
  importAction?: {
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
  };
  viewMode?: 'table' | 'cards' | 'map'
  onViewModeChange?: (mode: 'table' | 'cards' | 'map') => void
  onViewModePrefetch?: (mode: 'table' | 'cards' | 'map') => void
  bulkActions?: AssetsTableBulkAction[]
  manualPagination?: boolean
  paginationState?: PaginationState
  onPaginationChange?: (value: PaginationState) => void
  pageCount?: number
  totalCount?: number
  pageSizeOptions?: number[]
}

const COLUMN_PREFERENCES_KEY = 'assets-table-column-preferences'
const COLUMN_SIZING_KEY = 'assets-table-column-sizing'

const DEFAULT_VISIBLE_COLUMNS = new Set([
  'select',
  'address',
  'price',
  'area',
  'rentPrice',
  'modelPrice',
  'rentEstimate',
  'actions'
])

const ALL_COLUMN_IDS = [
  'select',
  'address',
  'city',
  'street',
  'number',
  'apartment',
  'block',
  'parcel',
  'subparcel',
  'area',
  'totalArea',
  'subparcelArea',
  'builtArea',
  'floor',
  'totalFloors',
  'assetStatus',
  'recentDeal',
  'adType',
  'contact',
  'price',
  'rentPrice',
  'pricePerSqm',
  'riskFlags',
  'deltaVsAreaPct',
  'domPercentile',
  'competition1km',
  'zoning',
  'remainingRightsSqm',
  'program',
  'lastPermitQ',
  'docsCount',
  'noiseLevel',
  'antennaDistanceM',
  'greenWithin300m',
  'shelterDistanceM',
  'riskFlags',
  'assetStatus',
  'priceGapPct',
  'confidencePct',
  'capRatePct',
  'actions',
  'videoUrl'
] as const

const DEFAULT_COLUMN_VISIBILITY = ALL_COLUMN_IDS.reduce<Record<string, boolean>>((acc, columnId) => {
  if (!DEFAULT_VISIBLE_COLUMNS.has(columnId)) {
    acc[columnId] = false
  }
  return acc
}, {})

export default function AssetsTable({
  data = [],
  loading = false,
  onDelete,
  onToggleWatch,
  watchingAssetIds,
  onExportAllRequest,
  searchValue = '',
  onSearchChange,
  filters,
  onRefresh,
  onAddNew,
  extraActions,
  importAction,
  viewMode = 'table',
  onViewModeChange,
  onViewModePrefetch,
  bulkActions = [],
  manualPagination = false,
  paginationState,
  onPaginationChange,
  pageCount,
  totalCount,
  pageSizeOptions,
}: AssetsTableProps){
  const { trackFeatureUsage, trackSearch } = useAnalytics()
  const router = useRouter()
  const [rowSelection, setRowSelection] = React.useState({})
  const [columnVisibility, setColumnVisibility] = React.useState<Record<string, boolean>>(() => {
    // Load saved column preferences from localStorage on component mount
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem(COLUMN_PREFERENCES_KEY)
        return saved ? { ...DEFAULT_COLUMN_VISIBILITY, ...JSON.parse(saved) } : { ...DEFAULT_COLUMN_VISIBILITY }
      } catch (error) {
        console.warn('Failed to load column preferences:', error)
        return { ...DEFAULT_COLUMN_VISIBILITY }
      }
    }
    return { ...DEFAULT_COLUMN_VISIBILITY }
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
  const [internalPagination, setInternalPagination] = React.useState<PaginationState>({ pageIndex: 0, pageSize: 25 })
  const [exportingAll, setExportingAll] = React.useState(false)

  const manualPaginationActive = Boolean(manualPagination && paginationState && onPaginationChange)
  const resolvedPagination = manualPaginationActive ? paginationState! : internalPagination

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

  const handleResetColumns = React.useCallback(() => {
    setColumnVisibility(() => {
      const defaults = { ...DEFAULT_COLUMN_VISIBILITY }

      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem(COLUMN_PREFERENCES_KEY, JSON.stringify(defaults))
        } catch (error) {
          console.warn('Failed to save column preferences:', error)
        }
      }

      return defaults
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

  const handlePaginationChange = React.useCallback(
    (updater: Updater<PaginationState>) => {
      if (manualPaginationActive) {
        if (onPaginationChange) {
          const next = typeof updater === 'function' ? updater(resolvedPagination) : updater
          onPaginationChange(next)
        }
      } else {
        setInternalPagination(prev =>
          typeof updater === 'function' ? updater(prev) : updater
        )
      }
    },
    [manualPaginationActive, onPaginationChange, resolvedPagination]
  )

  const computedPageCount = React.useMemo(() => {
    if (!manualPaginationActive) {
      return undefined
    }
    if (typeof pageCount === 'number') {
      return pageCount
    }
    const total = totalCount ?? data.length
    if (!resolvedPagination.pageSize) {
      return 1
    }
    return total === 0 ? 1 : Math.ceil(total / resolvedPagination.pageSize)
  }, [manualPaginationActive, pageCount, totalCount, data.length, resolvedPagination.pageSize])

  const recordCount = manualPaginationActive ? (totalCount ?? data.length) : data.length

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
    return createColumns({
      onDelete,
      onExport: handleExportSingle,
      onOpenAlert: handleOpenAlertModal,
      onToggleWatch,
      watchLoadingIds: watchingAssetIds,
    })
  }, [mounted, onDelete, handleExportSingle, handleOpenAlertModal, onToggleWatch, watchingAssetIds])

  const table = useReactTable({
    data,
    columns,
    state: {
      rowSelection,
      columnVisibility,
      columnSizing,
      pagination: resolvedPagination,
    },
    enableRowSelection: true,
    enableColumnResizing: true,
    columnResizeMode: 'onChange' as ColumnResizeMode,
    columnResizeDirection: 'rtl',
    onRowSelectionChange: setRowSelection,
    onColumnVisibilityChange: handleColumnVisibilityChange,
    onColumnSizingChange: handleColumnSizingChange,
    onPaginationChange: handlePaginationChange,
    getCoreRowModel: getCoreRowModel(),
    ...(manualPaginationActive
      ? {
          manualPagination: true as const,
          pageCount: computedPageCount ?? 1,
        }
      : {
          getPaginationRowModel: getPaginationRowModel(),
        }),
  })

  const clearSelection = React.useCallback(() => {
    setRowSelection({})
    table.resetRowSelection()
  }, [table])

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

  const handleExportAll = React.useCallback(async () => {
    if (exportingAll) {
      return
    }
    if (!onExportAllRequest) {
      exportAssetsCsv(data, table.getVisibleLeafColumns(), trackFeatureUsage)
      return
    }
    try {
      setExportingAll(true)
      const assets = await onExportAllRequest()
      exportAssetsCsv(assets, table.getVisibleLeafColumns(), trackFeatureUsage)
    } catch (error) {
      console.error('Failed to export assets', error)
    } finally {
      setExportingAll(false)
    }
  }, [data, exportingAll, onExportAllRequest, table, trackFeatureUsage])

  const selectedAssets = React.useMemo(
    () => {
      void rowSelection
      return table.getSelectedRowModel().rows.map(row => row.original)
    },
    [table, rowSelection]
  )

  const toolbarBulkActions = React.useMemo(
    () =>
      (bulkActions || []).map(action => ({
        label: action.label,
        icon: action.icon,
        disabled: action.disabled,
        action: () => action.action(selectedAssets, { clearSelection })
      })),
    [bulkActions, selectedAssets, clearSelection]
  )

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
    const items: AdditionalFilterConfig[] = []

    if (filters.neighborhood) {
      items.push({
        key: 'neighborhood',
        label: 'שכונה',
        type: 'select',
        value: filters.neighborhood.value,
        options: (filters.neighborhood.options || []).map(option => ({ value: option, label: option }))
      })
    }

    if (filters.zoning) {
      items.push({
        key: 'zoning',
        label: 'ייעוד',
        type: 'select',
        value: filters.zoning.value,
        options: (filters.zoning.options || []).map(option => ({ value: option, label: option }))
      })
    }

    if (filters.risk) {
      items.push({
        key: 'risk',
        label: 'סיכון',
        type: 'select',
        value: filters.risk.value,
        options: (filters.risk.options || []).map(option => ({ value: option.value, label: option.label }))
      })
    }

    if (filters.documents) {
      items.push({
        key: 'documents',
        label: 'מסמכים',
        type: 'select',
        value: filters.documents.value,
        options: (filters.documents.options || []).map(option => ({ value: option.value, label: option.label }))
      })
    }

    if (filters.rentalSale) {
      items.push({
        key: 'rentalSale',
        label: 'השכרה/מכירה',
        type: 'select',
        value: filters.rentalSale.value,
        options: (filters.rentalSale.options || []).map(option => ({ value: option.value, label: option.label }))
      })
    }

      if (filters.adType) {
        items.push({
          key: 'adType',
          label: 'סוג מפרסם',
          type: 'select',
          value: filters.adType.value,
          options: (filters.adType.options || []).map(option => ({ value: option.value, label: option.label }))
        })
      }

      if (filters.commercial) {
        items.push({
          key: 'commercial',
          label: 'ייעוד נכס',
          type: 'select',
          value: filters.commercial.value,
          options: (filters.commercial.options || []).map(option => ({ value: option.value, label: option.label }))
        })
      }

      if (filters.userAssets) {
        items.push({
          key: 'userAssets',
        label: 'נכסים שלי',
        type: 'select',
        value: filters.userAssets.value,
        options: (filters.userAssets.options || []).map(option => ({ value: option.value, label: option.label }))
      })
    }

    if (filters.buildingType) {
      items.push({
        key: 'buildingType',
        label: 'סוג בניין',
        type: 'select',
        value: filters.buildingType.value,
        options: (filters.buildingType.options || []).map(option => ({ value: option, label: option }))
      })
    }

    if (filters.rooms) {
      items.push({
        key: 'rooms',
        label: 'חדרים',
        type: 'select',
        value: filters.rooms.value,
        options: (filters.rooms.options || []).map(option => ({ value: option.value, label: option.label }))
      })
    }

    if (filters.features) {
      items.push({
        key: 'features',
        label: 'תכונות',
        type: 'select',
        value: filters.features.value,
        options: (filters.features.options || []).map(option => ({ value: option.value, label: option.label }))
      })
    }

    if (filters.bedrooms) {
      items.push({
        key: 'bedrooms',
        label: 'חדרי שינה',
        type: 'number-range',
        value: filters.bedrooms.value,
        minPlaceholder: filters.bedrooms.minPlaceholder,
        maxPlaceholder: filters.bedrooms.maxPlaceholder,
        step: filters.bedrooms.step,
        analyticsKey: 'bedrooms'
      })
    }

    if (filters.bathrooms) {
      items.push({
        key: 'bathrooms',
        label: 'חדרי רחצה',
        type: 'number-range',
        value: filters.bathrooms.value,
        minPlaceholder: filters.bathrooms.minPlaceholder,
        maxPlaceholder: filters.bathrooms.maxPlaceholder,
        step: filters.bathrooms.step,
        analyticsKey: 'bathrooms'
      })
    }

    if (filters.totalFloors) {
      items.push({
        key: 'totalFloors',
        label: 'קומות בבניין',
        type: 'number-range',
        value: filters.totalFloors.value,
        minPlaceholder: filters.totalFloors.minPlaceholder,
        maxPlaceholder: filters.totalFloors.maxPlaceholder,
        step: filters.totalFloors.step,
        analyticsKey: 'total_floors'
      })
    }

    if (filters.totalArea) {
      items.push({
        key: 'totalArea',
        label: 'שטח כולל',
        type: 'number-range',
        value: filters.totalArea.value,
        minPlaceholder: filters.totalArea.minPlaceholder,
        maxPlaceholder: filters.totalArea.maxPlaceholder,
        step: filters.totalArea.step,
        analyticsKey: 'total_area'
      })
    }

    if (filters.balconyArea) {
      items.push({
        key: 'balconyArea',
        label: 'שטח מרפסות',
        type: 'number-range',
        value: filters.balconyArea.value,
        minPlaceholder: filters.balconyArea.minPlaceholder,
        maxPlaceholder: filters.balconyArea.maxPlaceholder,
        step: filters.balconyArea.step,
        analyticsKey: 'balcony_area'
      })
    }

    if (filters.parkingSpaces) {
      items.push({
        key: 'parkingSpaces',
        label: 'חניות',
        type: 'number-range',
        value: filters.parkingSpaces.value,
        minPlaceholder: filters.parkingSpaces.minPlaceholder,
        maxPlaceholder: filters.parkingSpaces.maxPlaceholder,
        step: filters.parkingSpaces.step,
        analyticsKey: 'parking_spaces'
      })
    }

    if (filters.yearBuilt) {
      items.push({
        key: 'yearBuilt',
        label: 'שנת בנייה',
        type: 'number-range',
        value: filters.yearBuilt.value,
        minPlaceholder: filters.yearBuilt.minPlaceholder,
        maxPlaceholder: filters.yearBuilt.maxPlaceholder,
        step: filters.yearBuilt.step,
        analyticsKey: 'year_built'
      })
    }

    if (filters.rentPrice) {
      items.push({
        key: 'rentPrice',
        label: 'מחיר שכירות',
        type: 'number-range',
        value: filters.rentPrice.value,
        minPlaceholder: filters.rentPrice.minPlaceholder,
        maxPlaceholder: filters.rentPrice.maxPlaceholder,
        step: filters.rentPrice.step,
        analyticsKey: 'rent_price'
      })
    }

    if (filters.rentEstimate) {
      items.push({
        key: 'rentEstimate',
        label: 'שכירות משוערת',
        type: 'number-range',
        value: filters.rentEstimate.value,
        minPlaceholder: filters.rentEstimate.minPlaceholder,
        maxPlaceholder: filters.rentEstimate.maxPlaceholder,
        step: filters.rentEstimate.step,
        analyticsKey: 'rent_estimate'
      })
    }

    if (filters.priceGapPct) {
      items.push({
        key: 'priceGapPct',
        label: 'פער מחיר %',
        type: 'number-range',
        value: filters.priceGapPct.value,
        minPlaceholder: filters.priceGapPct.minPlaceholder,
        maxPlaceholder: filters.priceGapPct.maxPlaceholder,
        step: filters.priceGapPct.step,
        analyticsKey: 'price_gap_pct'
      })
    }

    if (filters.capRatePct) {
      items.push({
        key: 'capRatePct',
        label: 'תשואה %',
        type: 'number-range',
        value: filters.capRatePct.value,
        minPlaceholder: filters.capRatePct.minPlaceholder,
        maxPlaceholder: filters.capRatePct.maxPlaceholder,
        step: filters.capRatePct.step,
        analyticsKey: 'cap_rate_pct'
      })
    }

    if (filters.block) {
      items.push({
        key: 'block',
        label: 'גוש',
        type: 'select',
        value: filters.block.value,
        options: (filters.block.options || []).map(option => ({ value: option, label: option }))
      })
    }

    if (filters.parcel) {
      items.push({
        key: 'parcel',
        label: 'חלקה',
        type: 'select',
        value: filters.parcel.value,
        options: (filters.parcel.options || []).map(option => ({ value: option, label: option }))
      })
    }

    if (filters.renovated) {
      items.push({
        key: 'renovated',
        label: 'שיפוץ',
        type: 'select',
        value: filters.renovated.value,
        options: (filters.renovated.options || []).map(option => ({ value: option.value, label: option.label })),
        analyticsKey: 'renovated'
      })
    }

    if (filters.furnished) {
      items.push({
        key: 'furnished',
        label: 'ריהוט',
        type: 'select',
        value: filters.furnished.value,
        options: (filters.furnished.options || []).map(option => ({ value: option.value, label: option.label })),
        analyticsKey: 'furnished'
      })
    }

    if (filters.airConditioning) {
      items.push({
        key: 'airConditioning',
        label: 'מיזוג אוויר',
        type: 'select',
        value: filters.airConditioning.value,
        options: (filters.airConditioning.options || []).map(option => ({ value: option.value, label: option.label })),
        analyticsKey: 'air_conditioning'
      })
    }

    if (filters.storageRoom) {
      items.push({
        key: 'storageRoom',
        label: 'מחסן',
        type: 'select',
        value: filters.storageRoom.value,
        options: (filters.storageRoom.options || []).map(option => ({ value: option.value, label: option.label })),
        analyticsKey: 'storage_room'
      })
    }

    if (filters.hasElevator) {
      items.push({
        key: 'hasElevator',
        label: 'מעלית',
        type: 'select',
        value: filters.hasElevator.value,
        options: (filters.hasElevator.options || []).map(option => ({ value: option.value, label: option.label })),
        analyticsKey: 'elevator'
      })
    }

    return items
  }, [filters])

  const handleAdditionalFilterChange = React.useCallback((key: string, value: AdditionalFilterValue) => {
    if (!filters) return

    const trackString = (filterType: string, filterValue: string) => {
      trackFeatureUsage('filter', undefined, { filter_type: filterType, value: filterValue })
    }

    const trackRange = (filterType: string, range: { min?: number; max?: number }) => {
      trackFeatureUsage('filter', undefined, {
        filter_type: filterType,
        min: range.min ?? 'any',
        max: range.max ?? 'any',
      })
    }

    if (typeof value === 'string') {
      switch (key) {
        case 'neighborhood':
          filters.neighborhood?.onChange(value)
          trackString('neighborhood', value)
          break
        case 'zoning':
          filters.zoning?.onChange(value)
          trackString('zoning', value)
          break
        case 'risk':
          filters.risk?.onChange(value)
          trackString('risk', value)
          break
        case 'documents':
          filters.documents?.onChange(value)
          trackString('documents', value)
          break
        case 'rentalSale':
          filters.rentalSale?.onChange(value)
          trackString('rentalSale', value)
          break
        case 'adType':
          filters.adType?.onChange(value)
          trackString('adType', value)
          break
        case 'commercial':
          filters.commercial?.onChange(value)
          trackString('commercial', value)
          break
        case 'userAssets':
          filters.userAssets?.onChange(value)
          trackString('userAssets', value)
          break
        case 'buildingType':
          filters.buildingType?.onChange(value)
          trackString('buildingType', value)
          break
        case 'rooms':
          filters.rooms?.onChange(value)
          trackString('rooms', value)
          break
        case 'features':
          filters.features?.onChange(value)
          trackString('features', value)
          break
        case 'block':
          filters.block?.onChange(value)
          trackString('block', value)
          break
        case 'parcel':
          filters.parcel?.onChange(value)
          trackString('parcel', value)
          break
        case 'renovated':
          filters.renovated?.onChange(value)
          trackString('renovated', value)
          break
        case 'furnished':
          filters.furnished?.onChange(value)
          trackString('furnished', value)
          break
        case 'airConditioning':
          filters.airConditioning?.onChange(value)
          trackString('air_conditioning', value)
          break
        case 'storageRoom':
          filters.storageRoom?.onChange(value)
          trackString('storage_room', value)
          break
        case 'hasElevator':
          filters.hasElevator?.onChange(value)
          trackString('elevator', value)
          break
        default:
          break
      }
      return
    }

    if (value && typeof value === 'object') {
      const rangeValue = value as { min?: number; max?: number }
      switch (key) {
        case 'bedrooms':
          filters.bedrooms?.onChange(rangeValue)
          trackRange('bedrooms', rangeValue)
          break
        case 'bathrooms':
          filters.bathrooms?.onChange(rangeValue)
          trackRange('bathrooms', rangeValue)
          break
        case 'totalFloors':
          filters.totalFloors?.onChange(rangeValue)
          trackRange('total_floors', rangeValue)
          break
        case 'totalArea':
          filters.totalArea?.onChange(rangeValue)
          trackRange('total_area', rangeValue)
          break
        case 'balconyArea':
          filters.balconyArea?.onChange(rangeValue)
          trackRange('balcony_area', rangeValue)
          break
        case 'parkingSpaces':
          filters.parkingSpaces?.onChange(rangeValue)
          trackRange('parking_spaces', rangeValue)
          break
        case 'yearBuilt':
          filters.yearBuilt?.onChange(rangeValue)
          trackRange('year_built', rangeValue)
          break
        case 'rentPrice':
          filters.rentPrice?.onChange(rangeValue)
          trackRange('rent_price', rangeValue)
          break
        case 'rentEstimate':
          filters.rentEstimate?.onChange(rangeValue)
          trackRange('rent_estimate', rangeValue)
          break
        case 'priceGapPct':
          filters.priceGapPct?.onChange(rangeValue)
          trackRange('price_gap_pct', rangeValue)
          break
        case 'capRatePct':
          filters.capRatePct?.onChange(rangeValue)
          trackRange('cap_rate_pct', rangeValue)
          break
        default:
          break
      }
    }
  }, [filters, trackFeatureUsage])

  // Don't render table until mounted to prevent hydration mismatch
  if (!mounted) {
    return (
      <div className="block">
        <div className="rounded-xl border border-border/50 bg-card overflow-x-auto shadow-md">
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="block w-full max-w-full">
        <div className="rounded-xl border border-border/50 bg-card overflow-x-auto w-full max-w-full shadow-md">
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
            onResetColumns={handleResetColumns}
            columns={toolbarColumns}
            onExportSelected={handleExportSelected}
            onExportAll={handleExportAll}
            disableExportAll={exportingAll}
            selectedCount={table.getSelectedRowModel().rows.length}
            totalCount={recordCount}
            viewMode={viewMode}
            onViewModeChange={onViewModeChange || (() => {})}
            onViewModePrefetch={onViewModePrefetch}
            onRefresh={onRefresh || (() => {})}
            onAddNew={onAddNew}
            loading={loading}
            extraActions={extraActions}
            importAction={importAction}
            bulkActions={toolbarBulkActions}
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
            <div className="max-w-full" role="region" aria-label="טבלת נכסים">
              <div className="min-w-fit">
                <Table style={{ minWidth: table.getCenterTotalSize() }}>
                <THead>
                  <TR className="group">
                    {table.getFlatHeaders().map(h=>(
                      <TH 
                        key={h.id} 
                        className={`relative whitespace-nowrap ${h.column.id==='address'?'sticky end-0 bg-card z-10':''} ${
                          h.column.getCanResize() ? 'hover:bg-muted/30' : ''
                        } ${h.column.id === 'actions' ? 'w-full' : ''}`}
                        style={{ 
                          width: h.column.id === 'actions' ? 'auto' : h.getSize(),
                          minWidth: h.column.id === 'address' ? '200px' : '80px'
                        }}
                      >
                        <div className="flex items-center justify-between w-full">
                          <div className="flex-1">
                            {flexRender(h.column.columnDef.header, h.getContext())}
                          </div>
                          {h.column.getCanResize() && (
                            <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 ms-2">
                              <div className="w-1 h-4 bg-muted-foreground/40 rounded-full"></div>
                            </div>
                          )}
                        </div>
                        <div
                          className={`absolute top-0 start-0 h-full w-2 cursor-e-resize select-none touch-none ${
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
                <TBody
                  data-testid={loading ? 'assets-table-loading-body' : undefined}
                  aria-busy={loading ? 'true' : undefined}
                >
                  {loading ? (
                    Array.from({ length: 5 }).map((_, index) => (
                      <TR key={`loading-${index}`} className="animate-pulse">
                        <TD colSpan={table.getFlatHeaders().length} className="py-6">
                          <div className="flex items-center gap-4">
                            <Skeleton className="h-4 w-4 rounded-full" />
                            <div className="flex-1 space-y-2">
                              <Skeleton className="h-4 w-32" />
                              <Skeleton className="h-3 w-1/2" />
                            </div>
                          </div>
                        </TD>
                      </TR>
                    ))
                  ) : table.getRowModel().rows.length === 0 ? (
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
                            className={`whitespace-nowrap ${cell.column.id==='address'?'sticky end-0 bg-card z-10':''} ${cell.column.id === 'actions' ? 'w-full' : ''}`}
                            style={{ 
                              width: cell.column.id === 'actions' ? 'auto' : cell.column.getSize(),
                              minWidth: cell.column.id === 'address' ? '200px' : '80px'
                            }}
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
            </div>
          )}
        </div>
      </div>
      
      {/* Card view - show when viewMode is 'cards' */}
      {viewMode === 'cards' && (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 auto-rows-fr relative z-0">
          {loading ? (
            Array.from({ length: 3 }).map((_, index) => (
              <div key={`card-skeleton-${index}`} className="h-full rounded-lg bg-card/95 backdrop-blur-sm shadow-md p-4 space-y-3">
                <Skeleton className="h-48 w-full rounded-md" />
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
                <div className="flex gap-2">
                  <Skeleton className="h-6 w-16" />
                  <Skeleton className="h-6 w-20" />
                  <Skeleton className="h-6 w-12" />
                </div>
                <Skeleton className="h-4 w-1/3" />
              </div>
            ))
          ) : data.length === 0 ? (
            <div className="col-span-full flex flex-col items-center justify-center gap-4 py-12">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                <Search className="h-8 w-8 text-muted-foreground" />
              </div>
              <div className="text-center space-y-2">
                <h3 className="text-lg font-semibold text-foreground">לא נמצאו נכסים</h3>
                <p className="text-sm text-muted-foreground">
                  {searchValue || (filters && (filters.city.value !== 'all' || filters.type.value !== 'all' || filters.priceMin.value || filters.priceMax.value))
                    ? 'נסה לשנות את הסינון או החיפוש'
                    : 'אין נכסים זמינים כרגע'}
                </p>
                {!searchValue && filters && filters.city.value === 'all' && filters.type.value === 'all' && !filters.priceMin.value && !filters.priceMax.value && onAddNew && (
                  <Button className="mt-4" onClick={onAddNew}>
                    <Plus className="ms-2 h-4 w-4" />
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

      <TablePagination table={table} pageSizeOptions={pageSizeOptions} />

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
