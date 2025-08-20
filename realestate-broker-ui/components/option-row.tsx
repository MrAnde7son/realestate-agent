import React from 'react'
import { cn } from '@/lib/utils'

interface OptionRowProps {
  title: string
  description?: string
  action: React.ReactNode
  className?: string
}

export default function OptionRow({ title, description, action, className }: OptionRowProps) {
  return (
    <div className={cn('flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2', className)}>
      <div className="space-y-1 text-center sm:text-left">
        <p className="font-medium">{title}</p>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {action}
    </div>
  )
}
