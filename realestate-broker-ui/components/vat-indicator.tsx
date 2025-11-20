import React from 'react'
import { Info } from 'lucide-react'

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
      <div className="inline-flex items-center gap-2 rounded-full border bg-muted/50 px-3 py-2 shadow-sm">
        <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" aria-hidden />
        <div className="flex flex-col leading-tight">
          <span className="text-[11px] font-medium text-muted-foreground">מע״מ נוכחי</span>
          <span className="text-sm font-semibold">{(vatRate * 100).toFixed(1)}%</span>
        </div>
      </div>
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
