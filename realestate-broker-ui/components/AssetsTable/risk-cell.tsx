'use client'

import { Badge } from '@/components/ui/Badge'

export function RiskCell({ flags }: { flags?: string[] }) {
  if (!flags || flags.length === 0) {
    return <Badge variant="success">ללא</Badge>
  }
  
  return (
    <div className="flex gap-1 flex-wrap">
      {flags.map((flag, index) => (
        <Badge
          key={index}
          variant={
            flag.includes('שימור')
              ? 'error'
              : flag.includes('אנטנה')
              ? 'warning'
              : 'neutral'
          }
        >
          {flag}
        </Badge>
      ))}
    </div>
  )
}

