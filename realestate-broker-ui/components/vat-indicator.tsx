import React from 'react'

import { Badge } from '@/components/ui/Badge'
import { cn } from '@/lib/utils'

interface VatIndicatorProps extends React.HTMLAttributes<HTMLDivElement> {
  vatRate: number
  vatUpdated?: string
}

export function VatIndicator({ vatRate, vatUpdated, className, ...props }: VatIndicatorProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-end gap-2 text-end sm:flex-row sm:items-center sm:justify-end',
        className
      )}
      {...props}
    >
      <Badge
        variant="outline"
        className="h-auto px-2 py-1 text-[11px] leading-tight text-muted-foreground"
      >
        מע״מ נוכחי: {(vatRate * 100).toFixed(1)}%
      </Badge>
      {vatUpdated && (
        <Badge
          variant="outline"
          className="h-auto px-2 py-1 text-[11px] leading-tight text-muted-foreground"
        >
          עדכון אחרון: {new Date(vatUpdated).toLocaleDateString('he-IL')}
        </Badge>
      )}
    </div>
  )
}
