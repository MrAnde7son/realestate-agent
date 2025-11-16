'use client'

import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Asset } from '@/lib/normalizers/asset'
import { fmtCurrency, fmtNumber } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/button'
import { Bed, Bath, Ruler, Eye, FileText, Heart } from 'lucide-react'
import ImageGallery from './ImageGallery'

function exportAssetCsv(asset: Asset) {
  // Export all available fields from the Asset type
  const headers = [
    'id', 'address', 'city', 'neighborhood', 'street', 'number', 'type', 'bedrooms', 'rooms', 'bathrooms',
    'area', 'totalArea', 'balconyArea', 'parkingSpaces', 'price', 'rentPrice', 'pricePerSqm', 'pricePerSqmDisplay',
    'description', 'block', 'parcel', 'subparcel', 'lat', 'lon', 'normalizedAddress', 'buildingType',
    'floor', 'totalFloors', 'storageRoom', 'elevator', 'airConditioning', 'furnished', 'renovated',
    'yearBuilt', 'lastRenovation', 'deltaVsAreaPct', 'domPercentile', 'competition1km', 'zoning',
    'riskFlags', 'priceGapPct', 'expectedPriceRange', 'remainingRightsSqm', 'program', 'lastPermitQ',
    'noiseLevel', 'greenWithin300m', 'schoolsWithin500m', 'modelPrice', 'confidencePct', 'capRatePct',
    'antennaDistanceM', 'shelterDistanceM', 'rentEstimate', 'buildingRights', 'permitStatus', 'permitDate',
    'assetStatus', 'documents', 'assetId', 'sources', 'primarySource', 'permitDateDisplay',
    'permitStatusDisplay', 'permitDetails', 'permitMainArea', 'permitServiceArea', 'permitApplicant',
    'permitDocUrl', 'mainRightsSqm', 'serviceRightsSqm', 'additionalPlanRights', 'planStatus',
    'publicObligations', 'publicTransport', 'openSpacesNearby', 'publicBuildings', 'parking',
    'nearbyProjects', 'rightsUsagePct', 'legalRestrictions', 'urbanRenewalPotential', 'bettermentLevy'
  ] as const

  const csv = [
    headers.join(','),
    headers.map(k => {
      const value = (asset as any)[k]
      // Handle arrays and objects by converting to JSON strings
      if (Array.isArray(value)) {
        return JSON.stringify(value.join('; '))
      } else if (typeof value === 'object' && value !== null) {
        return JSON.stringify(JSON.stringify(value))
      }
      return JSON.stringify(value ?? '')
    }).join(',')
  ].join('\n')
  
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', 'asset.csv')
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

interface AssetCardProps {
  asset: Asset
  onToggleWatch?: (asset: Asset) => void
  watchLoading?: boolean
}

export default function AssetCard({ asset, onToggleWatch, watchLoading = false }: AssetCardProps) {
  const status = asset.assetStatus
  const statusVariant = status === 'done' ? 'success' : status === 'failed' ? 'error' : 'warning'
  const statusLabel =
    status === 'done' ? 'מוכן' : status === 'failed' ? 'שגיאה' : status === 'enriching' ? 'מתעשר' : 'ממתין'
  const isWatched = asset.isWatched === true
  const watchTitle = isWatched ? 'הסר מרשימת המעקב' : 'הוסף לרשימת המעקב'

  const router = useRouter()

  const handleNavigate = React.useCallback(() => {
    router.push(`/assets/${asset.id}`)
  }, [asset.id, router])

  const handleKeyDown = React.useCallback(
    (event: React.KeyboardEvent<HTMLDivElement>) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault()
        handleNavigate()
      }
    },
    [handleNavigate]
  )

  const handleExportClick = React.useCallback(
    (event: React.MouseEvent<HTMLButtonElement>) => {
      event.stopPropagation()
      exportAssetCsv(asset)
    },
    [asset]
  )

  const handleWatchClick = React.useCallback(
    (event: React.MouseEvent<HTMLButtonElement>) => {
      event.stopPropagation()
      event.preventDefault()
      onToggleWatch?.(asset)
    },
    [asset, onToggleWatch]
  )

  return (
    <Card
      variant="elevated"
      className="flex h-full flex-col gap-3 p-3 transition-transform hover:-translate-y-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary cursor-pointer sm:p-4"
      role="link"
      tabIndex={0}
      aria-label={asset.address ? `צפה בפרטי ${asset.address}` : 'צפה בפרטי נכס'}
      onClick={handleNavigate}
      onKeyDown={handleKeyDown}
    >
      {/* Images */}
      {asset.images && asset.images.length > 0 && (
        <ImageGallery
          images={asset.images}
          size="md"
          maxDisplay={2}
        />
      )}

      <div className="flex flex-col gap-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 truncate text-sm font-bold sm:text-base">{asset.address ?? '—'}</div>
          <div className="flex items-center gap-1">
            {onToggleWatch && (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className={`h-8 w-8 text-muted-foreground hover:text-amber-600 ${
                  isWatched ? 'text-amber-500' : ''
                } ${watchLoading ? 'pointer-events-none opacity-60' : ''}`}
                aria-label={watchTitle}
                aria-pressed={isWatched}
                title={watchTitle}
                disabled={watchLoading}
                onClick={handleWatchClick}
              >
                <Heart className="h-4 w-4" fill={isWatched ? 'currentColor' : 'none'} />
                <span className="sr-only">{watchTitle}</span>
              </Button>
            )}
            <Badge variant={statusVariant} className="text-xs sm:text-sm">{statusLabel}</Badge>
          </div>
        </div>
        <div className="text-xl font-semibold text-primary sm:text-2xl">
          {asset.price != null ? fmtCurrency(asset.price) : '—'}
        </div>
        {asset.rentPrice != null && (
          <div className="text-xs text-sub sm:text-sm">
            שכ&ldquo;ד מבוקש: {fmtCurrency(asset.rentPrice)}
          </div>
        )}
        <div className="flex flex-wrap gap-3 text-xs text-sub sm:text-sm">
          <div className="flex items-center gap-1">
            <Bed className="h-3 w-3 sm:h-4 sm:w-4" />
            {asset.rooms ?? '—'}
          </div>
          <div className="flex items-center gap-1">
            <Bath className="h-3 w-3 sm:h-4 sm:w-4" />
            {asset.bathrooms ?? '—'}
          </div>
          <div className="flex items-center gap-1">
            <Ruler className="h-3 w-3 sm:h-4 sm:w-4" />
            {asset.area != null ? fmtNumber(asset.area) : '—'} מ״ר
            {asset.subparcelArea && ` (${fmtNumber(asset.subparcelArea)} מגרש)`}
            {asset.builtArea && ` (${fmtNumber(asset.builtArea)} בנוי)`}
          </div>
        </div>
        <div className="text-xs text-sub sm:text-sm">
          {asset.pricePerSqm != null ? `${fmtNumber(asset.pricePerSqm)} ₪/מ״ר` : '—'}
        </div>
      </div>

      <div className="mt-auto flex flex-wrap gap-2 pt-2">
        <Link
          href={`/assets/${asset.id}`}
          onClick={event => event.stopPropagation()}
        >
          <Button variant="outline" size="icon" className="min-h-[44px] min-w-[44px]">
            <Eye className="h-4 w-4" />
            <span className="sr-only">צפה בפרטים</span>
          </Button>
        </Link>
        <Button
          variant="outline"
          size="icon"
          className="min-h-[44px] min-w-[44px]"
          onClick={handleExportClick}
        >
          <FileText className="h-4 w-4" />
          <span className="sr-only">ייצוא פרטי נכס</span>
        </Button>
      </div>
    </Card>
  )
}
