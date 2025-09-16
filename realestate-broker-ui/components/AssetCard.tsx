'use client'

import React from 'react'
import Link from 'next/link'
import { Asset } from '@/lib/normalizers/asset'
import { fmtCurrency, fmtNumber } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/button'
import { Bed, Bath, Ruler, Eye, FileText } from 'lucide-react'
import ImageGallery from './ImageGallery'

function exportAssetCsv(asset: Asset) {
  // Export all available fields from the Asset type
  const headers = [
    'id', 'address', 'city', 'neighborhood', 'street', 'number', 'type', 'bedrooms', 'rooms', 'bathrooms',
    'area', 'totalArea', 'balconyArea', 'parkingSpaces', 'price', 'pricePerSqm', 'pricePerSqmDisplay',
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
}

export default function AssetCard({ asset }: AssetCardProps) {
  const status = asset.assetStatus
  const statusVariant = status === 'done' ? 'success' : status === 'failed' ? 'error' : 'warning'
  const statusLabel =
    status === 'done' ? 'מוכן' : status === 'failed' ? 'שגיאה' : status === 'enriching' ? 'מתעשר' : 'ממתין'

  return (
    <Card className="p-4 space-y-3">
      {/* Images */}
      {asset.images && asset.images.length > 0 && (
        <ImageGallery 
          images={asset.images} 
          size="md" 
          maxDisplay={2}
          className="mb-2"
        />
      )}
      
      <div className="flex justify-between items-start gap-2">
        <div className="font-bold truncate flex-1">{asset.address ?? '—'}</div>
        <Badge variant={statusVariant}>{statusLabel}</Badge>
      </div>
      <div className="text-2xl font-semibold text-primary">
        {asset.price != null ? fmtCurrency(asset.price) : '—'}
      </div>
      <div className="flex gap-4 text-sm text-sub">
        <div className="flex items-center gap-1">
          <Bed className="h-4 w-4" />
          {asset.rooms ?? '—'}
        </div>
        <div className="flex items-center gap-1">
          <Bath className="h-4 w-4" />
          {asset.bathrooms ?? '—'}
        </div>
        <div className="flex items-center gap-1">
          <Ruler className="h-4 w-4" />
          {asset.area != null ? fmtNumber(asset.area) : '—'} מ&quot;ר
        </div>
      </div>
      <div className="text-sm text-sub">
        {asset.pricePerSqm != null ? `${fmtNumber(asset.pricePerSqm)} ₪/מ&quot;ר` : '—'}
      </div>
      <div className="flex gap-2 pt-2">
        <Link href={`/assets/${asset.id}`}> 
          <Button variant="outline" size="icon">
            <Eye className="h-4 w-4" />
            <span className="sr-only">צפה בפרטים</span>
          </Button>
        </Link>
        <Button variant="outline" size="icon" onClick={() => exportAssetCsv(asset)}>
          <FileText className="h-4 w-4" />
            <span className="sr-only">ייצוא פרטי נכס</span>
        </Button>
      </div>
    </Card>
  )
}

