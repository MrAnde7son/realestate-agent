'use client'
import * as React from 'react'
import { ColumnDef, flexRender, getCoreRowModel, useReactTable } from '@tanstack/react-table'
import type { Asset } from '@/lib/normalizers/asset'
import { fmtCurrency, fmtNumber, fmtPct } from '@/lib/utils'
import { Badge } from '@/components/ui/Badge'
import { Table, THead, TBody, TR, TH, TD } from '@/components/ui/table'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Trash2, Download, Bell, Eye, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuContent, DropdownMenuCheckboxItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import AssetCard from './AssetCard'
import AlertRulesManager from '@/components/alerts/alert-rules-manager'

function RiskCell({ flags }: { flags?: string[] }){
  if(!flags || flags.length===0) return <Badge variant='success'>ללא</Badge>;
  return <div className="flex gap-1 flex-wrap">{flags.map((f,i)=><Badge key={i} variant={f.includes('שימור')?'error':f.includes('אנטנה')?'warning':'neutral'}>{f}</Badge>)}</div>
}

function exportAssetsCsv(assets: Asset[], visibleColumns?: any[]) {
  if (assets.length === 0) return
  
  // If visibleColumns is provided, use them; otherwise fall back to default columns
  const headers = visibleColumns ? 
    visibleColumns
      .filter(col => col.getCanHide() !== false && col.id !== 'select' && col.id !== 'actions')
      .map(col => col.columnDef.header as string)
    : ['id', 'address', 'city', 'type', 'price', 'pricePerSqm']
  
  const accessorKeys = visibleColumns ?
    visibleColumns
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

function createColumns(onDelete?: (id: number) => void, onExport?: (asset: Asset) => void, onOpenAlert?: (assetId: number) => void): ColumnDef<Asset>[] {
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
    enableHiding: false
  },
  {
    header:'נכס',
    accessorKey:'address',
    cell: ({ row }) => (
      <div>
        <div className="font-semibold">
          <Link href={`/assets/${row.original.id}`}>{row.original.address}</Link>
        </div>
        <div className="text-xs text-sub">
            {row.original.city ?? '—'}
            {row.original.neighborhood ? ` · ${row.original.neighborhood}` : ''}
            {row.original.gush ? ` · גוש ${row.original.gush}` : ''}
            {row.original.helka ? ` חלקה ${row.original.helka}` : ''}
            {row.original.subhelka ? ` תת חלקה ${row.original.subhelka}` : ''}
            · {row.original.type ?? '—'} · {row.original.area !== undefined && row.original.area !== null ? `${fmtNumber(row.original.area)} מ"ר נטו` : '—'}
        </div>
      </div>
    )
  },
  { header:'₪', accessorKey:'price', cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : fmtCurrency(v)}</span>
    } },
  { header:'₪/מ"ר', accessorKey:'pricePerSqm', cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : fmtNumber(v)}</span>
    } },
  { header:'Δ מול איזור', accessorKey:'deltaVsAreaPct', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge variant={typeof value === 'number' && value < 0 ? 'error' : 'neutral'}>{fmtPct(value)}</Badge>
    } },
  { header:'ימי שוק (אחוזון)', accessorKey:'domPercentile', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge>{!!value ? `P${value}` : '—'}</Badge>
    } },
  { header:'תחרות (1ק"מ)', accessorKey:'competition1km', cell: info => {
      const value = info.getValue() as string | undefined
      return <Badge>{value ?? '—'}</Badge>
    } },
  { header:'ייעוד', accessorKey:'zoning', cell: info => {
      const value = info.getValue() as string | undefined
      return <Badge>{value ?? '—'}</Badge>
    } },
  { header:'יתרת זכויות', accessorKey:'remainingRightsSqm', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge>{value !== undefined && value !== null ? `~+${fmtNumber(value)} מ"ר` : '—'}</Badge>
    } },
  { header:'תכנית', accessorKey:'program', cell: info => {
      const value = info.getValue() as string | undefined
      return <Badge>{value ?? '—'}</Badge>
    } },
  { header:'היתר עדכני', accessorKey:'lastPermitQ', cell: info => {
      const value = info.getValue() as string | undefined
      return <Badge>{value ?? '—'}</Badge>
    } },
  { header:'קבצים', id:'docsCount', accessorFn: row => row.documents?.length ?? 0, cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge>{fmtNumber(value)}</Badge>
    } },
  { header:'רעש', accessorKey:'noiseLevel', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge>{!!value ? `${value}/5` : '—'}</Badge>
    } },
  { header:'אנטנה (מ")', accessorKey:'antennaDistanceM', cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : fmtNumber(v)}</span>
    } },
  { header:'שטחי ציבור ≤300מ"', accessorKey:'greenWithin300m', cell: info => {
      const value = info.getValue() as boolean | undefined
      return <Badge variant={value === undefined ? 'neutral' : value ? 'success' : 'error'}>{value === undefined ? '—' : value ? 'כן' : 'לא'}</Badge>
    } },
  { header:'מקלט (מ")', accessorKey:'shelterDistanceM', cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : fmtNumber(v)}</span>
    } },
  { header:'סיכון', accessorKey:'riskFlags', cell: info => <RiskCell flags={info.getValue() as string[]}/> },
  { header:'סטטוס נכס', accessorKey:'assetStatus', cell: info => {
    const status = info.getValue() as string
    if (!status) return <Badge variant="neutral">—</Badge>
    const variant = status === 'done' ? 'success' : status === 'failed' ? 'error' : 'warning'
    const label = status === 'done' ? 'מוכן' : status === 'failed' ? 'שגיאה' : status === 'enriching' ? 'מתעשר' : 'ממתין'
    return <Badge variant={variant}>{label}</Badge>
  }},
  { header:'מחיר מודל', accessorKey:'modelPrice', cell: info => <span className="font-mono">{fmtCurrency(info.getValue() as number)}</span> },
  { header:'פער למחיר', accessorKey:'priceGapPct', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge variant={typeof value === 'number' && value > 0 ? 'warning' : 'success'}>{fmtPct(value)}</Badge>
    } },
  { header:'רמת ביטחון', accessorKey:'confidencePct', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge>{!!value ? `${value}%` : '—'}</Badge>
    } },
  { header:'שכ"ד', accessorKey:'rentEstimate', cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : fmtCurrency(v)}</span>
    } },
    { header:'תשואה', accessorKey:'capRatePct', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge>{typeof value === 'number' ? `${value.toFixed(1)}%` : '—'}</Badge>
    } },
    { header:'—', id:'actions', cell: ({ row }) => (
      <div className="flex gap-2">
        <Link 
          className="text-blue-600 hover:text-blue-800 underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded p-1"
          href={`/assets/${row.original.id}`}
          aria-label={`צפה בפרטי נכס ${row.original.address}`}
          title="צפה בפרטי נכס"
        >
          <Eye className="h-4 w-4" />
        </Link>
        {onOpenAlert && (
          <button
            onClick={e => { e.stopPropagation(); onOpenAlert(row.original.id) }}
            className="text-amber-600 hover:text-amber-800 underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded p-1"
            title="הגדר התראות לנכס זה"
            aria-label={`הגדר התראות לנכס ${row.original.address}`}
          >
            <Bell className="h-4 w-4" />
          </button>
        )}
        {onExport && (
          <button
            onClick={e => { e.stopPropagation(); onExport(row.original) }}
            className="text-green-600 hover:text-green-800 underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded p-1"
            aria-label={`ייצא נכס ${row.original.address}`}
            title="ייצא נכס"
          >
            <Download className="h-4 w-4" />
          </button>
        )}
        {onDelete && (
          <button 
            onClick={e => { e.stopPropagation(); onDelete(row.original.id) }} 
            className="text-red-600 hover:text-red-800 underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded p-1"
            aria-label={`מחק נכס ${row.original.address}`}
            title="מחק נכס"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        )}
      </div>
    ) }
  ]
}

interface AssetsTableProps {
    data?: Asset[]
    loading?: boolean
    onDelete?: (id: number) => void
  }

const COLUMN_PREFERENCES_KEY = 'assets-table-column-preferences'

export default function AssetsTable({ data = [], loading = false, onDelete }: AssetsTableProps){
  const router = useRouter()
  const [rowSelection, setRowSelection] = React.useState({})
  const [columnVisibility, setColumnVisibility] = React.useState<Record<string, boolean>>(() => {
    // Load saved column preferences from localStorage on component mount
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem(COLUMN_PREFERENCES_KEY)
        return saved ? JSON.parse(saved) : {}
      } catch (error) {
        console.warn('Failed to load column preferences:', error)
        return {}
      }
    }
    return {}
  })
  const [alertModalOpen, setAlertModalOpen] = React.useState(false)
  const [selectedAssetId, setSelectedAssetId] = React.useState<number | null>(null)

  const handleExportSingle = (asset: Asset) => exportAssetsCsv([asset], table?.getVisibleLeafColumns())

  const handleOpenAlertModal = (assetId: number) => {
    setSelectedAssetId(assetId)
    setAlertModalOpen(true)
  }

  // Save column preferences to localStorage whenever they change
  const handleColumnVisibilityChange = React.useCallback((updaterOrValue: any) => {
    setColumnVisibility(prev => {
      const newVisibility = typeof updaterOrValue === 'function' ? updaterOrValue(prev) : updaterOrValue
      
      // Save to localStorage
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem(COLUMN_PREFERENCES_KEY, JSON.stringify(newVisibility))
        } catch (error) {
          console.warn('Failed to save column preferences:', error)
        }
      }
      
      return newVisibility
    })
  }, [])

  const columns = React.useMemo(() => createColumns(onDelete, handleExportSingle, handleOpenAlertModal), [onDelete])

  const table = useReactTable({
    data,
    columns,
    state: { 
      rowSelection,
      columnVisibility 
    },
    enableRowSelection: true,
    onRowSelectionChange: setRowSelection,
    onColumnVisibilityChange: handleColumnVisibilityChange,
    getCoreRowModel: getCoreRowModel()
  })

  const handleRowClick = (asset: Asset) => {
    router.push(`/assets/${asset.id}`)
  }

  const handleExportSelected = () => {
    const selected = table.getSelectedRowModel().rows.map(r => r.original)
    exportAssetsCsv(selected, table.getVisibleLeafColumns())
  }

  const anySelected = table.getSelectedRowModel().rows.length > 0

  return (
    <>
      <div className="hidden sm:block">
        <div className="rounded-xl border border-border bg-card overflow-x-auto">
          <div className="p-3 border-b border-border bg-muted/30">
            <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
              {/* Left side - Column selection */}
              <div className="flex items-center gap-2">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" aria-label="בחר עמודות">
                      <Settings className="h-4 w-4 me-2" />
                      <span className="hidden sm:inline">עמודות</span>
                      <span className="sm:hidden">עמודות</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-56 max-h-80 overflow-y-auto z-[100]">
                    {table.getAllColumns()
                      .filter(column => column.getCanHide())
                      .map(column => (
                        <DropdownMenuCheckboxItem
                          key={column.id}
                          className="capitalize"
                          checked={column.getIsVisible()}
                          onCheckedChange={value => column.toggleVisibility(!!value)}
                          onSelect={(e) => e.preventDefault()}
                        >
                          {column.columnDef.header as string}
                        </DropdownMenuCheckboxItem>
                      ))}
                  </DropdownMenuContent>
                </DropdownMenu>
                <span className="text-sm text-muted-foreground hidden sm:inline">
                  {table.getVisibleLeafColumns().length} מתוך {table.getAllColumns().length} עמודות
                </span>
              </div>
              
              {/* Right side - Export actions */}
              <div className="flex items-center gap-2">
                <Button 
                  onClick={handleExportSelected} 
                  disabled={!anySelected} 
                  variant="outline"
                  size="sm"
                  aria-label="ייצא נכסים נבחרים"
                >
                  <Download className="h-4 w-4 me-2" />
                  <span className="hidden sm:inline">ייצוא נבחרים</span>
                  <span className="sm:hidden">ייצוא</span>
                  {anySelected && (
                    <span className="ml-1 px-1.5 py-0.5 text-xs bg-primary text-primary-foreground rounded-full">
                      {table.getSelectedRowModel().rows.length}
                    </span>
                  )}
                </Button>
              </div>
            </div>
          </div>
          <div className="overflow-x-auto" role="region" aria-label="טבלת נכסים">
            <Table>
              <THead>
                <TR>
                  {table.getFlatHeaders().map(h=>(
                    <TH 
                      key={h.id} 
                      className={h.column.id==='address'?'sticky right-0 bg-card z-10':''}
                    >
                      {flexRender(h.column.columnDef.header, h.getContext())}
                    </TH>
                  ))}
                </TR>
              </THead>
              <TBody>
                {table.getRowModel().rows.map(row=>(
                  <TR 
                    key={row.id} 
                    className="clickable-row focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" 
                    onClick={() => handleRowClick(row.original)}
                    tabIndex={0}
                    role="button"
                    aria-label={`נכס ${row.original.address} - לחץ לפרטים`}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        handleRowClick(row.original)
                      }
                    }}
                  >
                    {row.getVisibleCells().map(cell=>(
                      <TD 
                        key={cell.id} 
                        className={cell.column.id==='address'?'sticky right-0 bg-card z-10':''}
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </TD>
                    ))}
                  </TR>
                ))}
              </TBody>
            </Table>
          </div>
        </div>
      </div>
      <div className="sm:hidden space-y-2">
        {data.map(asset => (
          <AssetCard key={asset.id} asset={asset} />
        ))}
      </div>

      {/* Alert Modal */}
      <Dialog open={alertModalOpen} onOpenChange={setAlertModalOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>הגדרת התראות לנכס</DialogTitle>
          </DialogHeader>
          {selectedAssetId && (
            <AlertRulesManager assetId={selectedAssetId} />
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
