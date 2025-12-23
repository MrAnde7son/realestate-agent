'use client'

import * as React from 'react'
import { Row, Table as TanstackTable } from '@tanstack/react-table'
import { Virtualizer } from '@tanstack/react-virtual'
import type { Asset } from '@/lib/normalizers/asset'
import { flexRender } from '@tanstack/react-table'
import { TR, TD } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'

interface TableBodyProps {
  table: TanstackTable<Asset>
  tableRows: Row<Asset>[]
  loading: boolean
  shouldUseVirtualization: boolean
  virtualizer?: Virtualizer<HTMLDivElement, Element> | null
  onRowClick: (asset: Asset) => void
}

export function TableBody({
  table,
  tableRows,
  loading,
  shouldUseVirtualization,
  virtualizer,
  onRowClick,
}: TableBodyProps) {
  if (loading) {
    return (
      <>
        {Array.from({ length: 5 }).map((_, index) => (
          <TR key={`loading-${index}`}>
            {table.getFlatHeaders().map((header, headerIndex) => (
              <TD key={`loading-${index}-${headerIndex}`} className="py-4">
                {headerIndex === 0 ? (
                  // First column: checkbox + content
                  <div className="flex items-center gap-3">
                    <Skeleton className="h-4 w-4 rounded" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-3 w-24" />
                    </div>
                  </div>
                ) : headerIndex === 1 ? (
                  // Second column: image + address
                  <div className="flex items-center gap-3">
                    <Skeleton className="h-12 w-12 rounded-md" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-40" />
                      <Skeleton className="h-3 w-28" />
                    </div>
                  </div>
                ) : (
                  // Other columns: simple skeleton
                  <Skeleton className="h-4 w-20" />
                )}
              </TD>
            ))}
          </TR>
        ))}
      </>
    )
  }

  if (shouldUseVirtualization && virtualizer) {
    const virtualItems = virtualizer.getVirtualItems()
    
    return (
      <>
        {virtualItems.map((virtualRow) => {
          const row = tableRows[virtualRow.index]
          if (!row) return null
          
          return (
            <TR
              key={row.id}
              role="row"
              aria-rowindex={virtualRow.index + 1}
              className="clickable-row focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none"
              onClick={() => onRowClick(row.original)}
              tabIndex={0}
              aria-label={`נכס ${row.original.address || row.original.id} - לחץ Enter או רווח לפרטים`}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onRowClick(row.original)
                }
                // Arrow key navigation for virtualized rows
                if (e.key === 'ArrowDown' && virtualRow.index < tableRows.length - 1) {
                  e.preventDefault()
                  const nextRow = tableRows[virtualRow.index + 1]
                  if (nextRow) {
                    const nextElement = document.querySelector(`[aria-rowindex="${virtualRow.index + 2}"]`) as HTMLElement
                    nextElement?.focus()
                  }
                }
                if (e.key === 'ArrowUp' && virtualRow.index > 0) {
                  e.preventDefault()
                  const prevRow = tableRows[virtualRow.index - 1]
                  if (prevRow) {
                    const prevElement = document.querySelector(`[aria-rowindex="${virtualRow.index}"]`) as HTMLElement
                    prevElement?.focus()
                  }
                }
              }}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              {row.getVisibleCells().map((cell) => (
                <TD 
                  key={cell.id}
                  role="gridcell"
                  className={`whitespace-nowrap py-4 ${cell.column.id==='address'?'sticky end-0 bg-card z-10':''} ${cell.column.id === 'actions' ? 'w-full' : ''}`}
                  style={{ 
                    width: cell.column.id === 'actions' ? 'auto' : cell.column.getSize(),
                    minWidth: cell.column.id === 'address' ? '200px' : cell.column.id === 'select' ? '48px' : '80px'
                  }}
                >
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TD>
              ))}
            </TR>
          )
        })}
      </>
    )
  }

  // Regular rendering (non-virtualized)
  return (
    <>
      {tableRows.map((row, rowIndex) => (
        <TR
          key={row.id}
          role="row"
          aria-rowindex={rowIndex + 1}
          className="clickable-row focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none"
          onClick={() => onRowClick(row.original)}
          tabIndex={0}
          aria-label={`נכס ${row.original.address || row.original.id} - לחץ Enter או רווח לפרטים`}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              onRowClick(row.original)
            }
            // Arrow key navigation for regular rows
            if (e.key === 'ArrowDown' && rowIndex < tableRows.length - 1) {
              e.preventDefault()
              const nextRow = tableRows[rowIndex + 1]
              if (nextRow) {
                const nextElement = document.querySelector(`[aria-rowindex="${rowIndex + 2}"]`) as HTMLElement
                nextElement?.focus()
              }
            }
            if (e.key === 'ArrowUp' && rowIndex > 0) {
              e.preventDefault()
              const prevRow = tableRows[rowIndex - 1]
              if (prevRow) {
                const prevElement = document.querySelector(`[aria-rowindex="${rowIndex}"]`) as HTMLElement
                prevElement?.focus()
              }
            }
          }}
        >
          {row.getVisibleCells().map((cell) => (
            <TD 
              key={cell.id}
              role="gridcell"
              className={`whitespace-nowrap py-4 ${cell.column.id==='address'?'sticky end-0 bg-card z-10':''} ${cell.column.id === 'actions' ? 'w-full' : ''}`}
              style={{ 
                width: cell.column.id === 'actions' ? 'auto' : cell.column.getSize(),
                minWidth: cell.column.id === 'address' ? '200px' : cell.column.id === 'select' ? '48px' : '80px'
              }}
            >
              {flexRender(cell.column.columnDef.cell, cell.getContext())}
            </TD>
          ))}
        </TR>
      ))}
    </>
  )
}

