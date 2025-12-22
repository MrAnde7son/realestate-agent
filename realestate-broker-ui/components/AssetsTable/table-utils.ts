'use client'

import type { Asset } from '@/lib/normalizers/asset'

/**
 * Export assets to CSV
 */
export function exportAssetsCsv(assets: Asset[], visibleColumns?: any[]) {
  if (assets.length === 0) return
  
  const headers = visibleColumns
    ? visibleColumns
        .filter(col => col.getCanHide() !== false && col.id !== 'select' && col.id !== 'actions')
        .map(col => col.columnDef.header as string)
    : ['id', 'address', 'city', 'type', 'price', 'pricePerSqm']
  
  const accessorKeys = visibleColumns
    ? visibleColumns
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

/**
 * Column visibility constants
 */
export const COLUMN_PREFERENCES_KEY = 'assets-table-column-preferences'
export const COLUMN_SIZING_KEY = 'assets-table-column-sizing'

export const DEFAULT_VISIBLE_COLUMNS = new Set([
  'select',
  'address',
  'price',
  'area',
  'rentPrice',
  'modelPrice',
  'rentEstimate',
  'actions'
])

export const ALL_COLUMN_IDS = [
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
  'sellerType',
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
  'priceGapPct',
  'confidencePct',
  'capRatePct',
  'priceDropped',
  'previousPrice',
  'shelter',
  'accessibility',
  'buildingClass',
  'generalCondition',
  'investmentYield',
  'approximateRent',
  'commuteTime',
  'publishedDays',
  'tagBestSchool',
  'tagSafety',
  'tagFamilyFriendly',
  'tagLightRail',
  'exclusive',
  'actions',
  'videoUrl'
] as const

export const DEFAULT_COLUMN_VISIBILITY = ALL_COLUMN_IDS.reduce<Record<string, boolean>>(
  (acc, columnId) => {
    if (!DEFAULT_VISIBLE_COLUMNS.has(columnId)) {
      acc[columnId] = false
    }
    return acc
  },
  {}
)

