'use client'

import React from 'react'
import { Loader2, AlertTriangle } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import type { Asset } from '@/lib/normalizers/asset'

type AssetStatus = Asset['assetStatus']
type AssetStatusValue = Extract<AssetStatus, string>

const STATUS_LABELS: Record<AssetStatusValue, string> = {
  done: 'מוכן',
  failed: 'שגיאה באיסוף',
  enriching: 'אוסף נתונים על הנכס',
  pending: 'מכין נתונים על הנכס',
  syncing: 'מסנכרן נתונים',
}

interface AssetStatusIndicatorProps {
  status?: AssetStatus
  size?: 'sm' | 'md'
}

export function AssetStatusIndicator({ status, size = 'md' }: AssetStatusIndicatorProps) {
  if (!status || status === 'done') return null

  const label = STATUS_LABELS[status as AssetStatusValue]

  if (!label) return null
  const iconSize = size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'
  const textSize = size === 'sm' ? 'text-[11px]' : 'text-xs'

  if (status === 'failed') {
    return (
      <Badge
        variant="error"
        className={`inline-flex items-center gap-1 ${textSize}`}
      >
        <AlertTriangle className={`${iconSize}`} aria-hidden="true" />
        <span>{label}</span>
      </Badge>
    )
  }

  return (
    <div className={`inline-flex items-center gap-1 text-muted-foreground ${textSize}`} aria-live="polite">
      <Loader2 className={`${iconSize} animate-spin`} aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}

export default AssetStatusIndicator
