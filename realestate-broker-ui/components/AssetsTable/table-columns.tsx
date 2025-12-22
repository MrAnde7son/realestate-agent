'use client'

import * as React from 'react'
import { ColumnDef } from '@tanstack/react-table'
import type { Asset } from '@/lib/normalizers/asset'
import { fmtCurrency, fmtNumber, fmtPct } from '@/lib/utils'
import { Badge } from '@/components/ui/Badge'
import Link from 'next/link'
import { Trash2, Download, Bell, Eye, Star, StarOff, Handshake } from 'lucide-react'
import { Button } from '@/components/ui/button'
import ImageGallery from '@/components/ImageGallery'
import AssetStatusIndicator from '@/components/AssetStatusIndicator'
import { RiskCell } from './risk-cell'

// Utility functions
export const formatListingTypeLabel = (value?: string | null) => {
  if (!value) return '—'
  const normalized = value.toLowerCase()
  if (normalized === 'rent') return 'השכרה'
  if (normalized === 'sale') return 'מכירה'
  if (normalized === 'commercial') return 'מסחרי'
  if (normalized === 'auction') return 'מכרז'
  return value
}

export const formatAdTypeLabel = (value?: string | null) => {
  if (!value) return '—'
  const normalized = value.toLowerCase()
  if (normalized === 'private') return 'פרטי'
  if (normalized === 'broker' || normalized === 'agency' || normalized === 'agent') return 'מתווך'
  return value
}

interface CreateColumnsParams {
  onDelete?: (id: number) => void
  onExport?: (asset: Asset) => void
  onOpenAlert?: (assetId: number) => void
  onToggleWatch?: (asset: Asset) => void
  watchLoadingIds?: Set<number>
  onDealWorkspaceClick?: (asset: Asset, e: React.MouseEvent) => void
}

export function createColumns({
  onDelete,
  onExport,
  onOpenAlert,
  onToggleWatch,
  watchLoadingIds,
  onDealWorkspaceClick,
}: CreateColumnsParams): ColumnDef<Asset>[] {
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
      enableHiding: false,
      enableResizing: false,
      size: 48,
      minSize: 48,
      maxSize: 48,
    },
    {
      header: 'נכס',
      accessorKey: 'address',
      cell: ({ row }) => (
        <div className="flex gap-3 items-start">
          {row.original.images && row.original.images.length > 0 && (
            <div
              className="flex-shrink-0"
              onClick={event => event.stopPropagation()}
              onMouseDown={event => event.stopPropagation()}
              onTouchStart={event => event.stopPropagation()}
              onKeyDown={event => {
                if (event.key === 'Enter' || event.key === ' ' || event.key === 'Spacebar' || event.key === 'Space') {
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
                <Badge variant="warning" className="flex items-center gap-1">
                  <Star className="h-3 w-3 fill-current" />
                  במעקב
                </Badge>
              )}
              <AssetStatusIndicator status={row.original.assetStatus} size="sm" />
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
      ),
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
      header: 'מחיר',
      accessorKey: 'price',
      cell: info => {
        const value = info.getValue() as number | null | undefined
        return <span className="font-semibold">{value != null ? fmtCurrency(value) : '—'}</span>
      },
    },
    {
      header: 'שכ"ד מוערך',
      accessorKey: 'rentPrice',
      cell: info => {
        const value = info.getValue() as number | null | undefined
        return <span>{value != null ? fmtCurrency(value) : '—'}</span>
      },
    },
    {
      header: 'שטח',
      accessorKey: 'area',
      cell: info => {
        const value = info.getValue() as number | null | undefined
        return <span>{value != null ? `${fmtNumber(value)} מ"ר` : '—'}</span>
      },
    },
    {
      header: 'דגלי סיכון',
      accessorKey: 'riskFlags',
      cell: ({ row }) => <RiskCell flags={row.original.riskFlags ?? undefined} />,
    },
    {
      id: 'actions',
      header: 'פעולות',
      cell: ({ row }) => {
        const asset = row.original
        const isWatched = asset.isWatched === true
        const watchLoading = watchLoadingIds?.has(asset.id)
        
        return (
          <div className="flex items-center gap-1" onClick={e => e.stopPropagation()}>
            {onToggleWatch && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => onToggleWatch(asset)}
                disabled={watchLoading}
                aria-label={isWatched ? 'הסר מרשימת המעקב' : 'הוסף לרשימת המעקב'}
                title={isWatched ? 'הסר מרשימת המעקב' : 'הוסף לרשימת המעקב'}
              >
                {watchLoading ? (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                ) : isWatched ? (
                  <Star className="h-4 w-4 fill-amber-500 text-amber-500" />
                ) : (
                  <StarOff className="h-4 w-4" />
                )}
                <span className="sr-only">{isWatched ? 'הסר מרשימת המעקב' : 'הוסף לרשימת המעקב'}</span>
              </Button>
            )}
            
            {onExport && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => onExport(asset)}
                aria-label="ייצא נכס"
                title="ייצא נכס"
              >
                <Download className="h-4 w-4" />
                <span className="sr-only">ייצא נכס</span>
              </Button>
            )}
            
            {onOpenAlert && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => onOpenAlert(asset.id)}
                aria-label="הגדר התראות"
                title="הגדר התראות"
              >
                <Bell className="h-4 w-4" />
                <span className="sr-only">הגדר התראות</span>
              </Button>
            )}
            
            <Link href={`/assets/${asset.id}`}>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                aria-label={`צפה בפרטי ${asset.address || asset.id}`}
                title="צפה בפרטים"
              >
                <Eye className="h-4 w-4" />
                <span className="sr-only">צפה בפרטים</span>
              </Button>
            </Link>
            
            {onDealWorkspaceClick && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={(e) => onDealWorkspaceClick?.(asset, e)}
                aria-label="פתח סביבת עסקה"
                title="פתח סביבת עסקה"
              >
                <Handshake className="h-4 w-4" />
                <span className="sr-only">פתח סביבת עסקה</span>
              </Button>
            )}
            
            {onDelete && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-destructive hover:text-destructive"
                onClick={() => onDelete(asset.id)}
                aria-label="מחק נכס"
                title="מחק נכס"
              >
                <Trash2 className="h-4 w-4" />
                <span className="sr-only">מחק נכס</span>
              </Button>
            )}
          </div>
        )
      },
      enableSorting: false,
      enableHiding: false,
    },
  ]
}

