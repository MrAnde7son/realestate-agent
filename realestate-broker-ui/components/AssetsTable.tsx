'use client'
import * as React from 'react'
import { ColumnDef, flexRender, getCoreRowModel, useReactTable } from '@tanstack/react-table'
import type { Asset } from '@/lib/normalizers/asset'
import { fmtCurrency, fmtNumber, fmtPct } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Table, THead, TBody, TR, TH, TD } from '@/components/ui/table'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Trash2, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'

function RiskCell({ flags }: { flags?: string[] }){ 
  if(!flags || flags.length===0) return <Badge variant='good'>ללא</Badge>; 
  return <div className="flex gap-1 flex-wrap">{flags.map((f,i)=><Badge key={i} variant={f.includes('שימור')?'bad':f.includes('אנטנה')?'warn':'default'}>{f}</Badge>)}</div> 
}

function exportAssetsCsv(assets: Asset[]) {
  if (assets.length === 0) return
  const headers = ['id', 'address', 'city', 'type', 'price', 'pricePerSqm'] as const
  const csv = [
    headers.join(','),
    ...assets.map(a =>
      headers
        .map(k => JSON.stringify((a as any)[k] ?? ''))
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

function createColumns(onDelete?: (id: number) => void, onExport?: (asset: Asset) => void): ColumnDef<Asset>[] {
  return [
  {
    id: 'select',
    header: ({ table }) => (
      <input
        type="checkbox"
        checked={table.getIsAllRowsSelected()}
        onChange={table.getToggleAllRowsSelectedHandler()}
        aria-label="Select all"
        className="size-4"
      />
    ),
    cell: ({ row }) => (
      <input
        type="checkbox"
        checked={row.getIsSelected()}
        onClick={e => e.stopPropagation()}
        onChange={row.getToggleSelectedHandler()}
        aria-label="Select row"
        className="size-4"
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
            {row.original.city ?? '—'}{row.original.neighborhood?` · ${row.original.neighborhood}`:''} · {row.original.type ?? '—'} · {row.original.netSqm !== undefined && row.original.netSqm !== null ? `${fmtNumber(row.original.netSqm)} מ"ר נטו` : '—'}
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
      return <Badge variant={typeof value === 'number' && value < 0 ? 'bad' : 'default'}>{fmtPct(value)}</Badge>
    } },
  { header:'ימי שוק (אחוזון)', accessorKey:'domPercentile', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge>{value !== undefined ? `P${value}` : '—'}</Badge>
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
      return <Badge>{value !== undefined ? `${value}/5` : '—'}</Badge>
    } },
  { header:'אנטנה (מ")', accessorKey:'antennaDistanceM', cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : fmtNumber(v)}</span>
    } },
  { header:'שטחי ציבור ≤300מ"', accessorKey:'greenWithin300m', cell: info => {
      const value = info.getValue() as boolean | undefined
      return <Badge variant={value === undefined ? 'default' : value ? 'good' : 'bad'}>{value === undefined ? '—' : value ? 'כן' : 'לא'}</Badge>
    } },
  { header:'מקלט (מ")', accessorKey:'shelterDistanceM', cell: info => {
      const v = info.getValue() as number | null | undefined
      return <span className="font-mono">{v == null ? '—' : fmtNumber(v)}</span>
    } },
  { header:'סיכון', accessorKey:'riskFlags', cell: info => <RiskCell flags={info.getValue() as string[]}/> },
  { header:'סטטוס נכס', accessorKey:'assetStatus', cell: info => {
    const status = info.getValue() as string
    if (!status) return <Badge variant="default">—</Badge>
    const variant = status === 'done' ? 'good' : status === 'failed' ? 'bad' : 'warn'
    const label = status === 'done' ? 'מוכן' : status === 'failed' ? 'שגיאה' : status === 'enriching' ? 'מתעשר' : 'ממתין'
    return <Badge variant={variant}>{label}</Badge>
  }},
  { header:'מחיר מודל', accessorKey:'modelPrice', cell: info => <span className="font-mono">{fmtCurrency(info.getValue() as number)}</span> },
  { header:'פער למחיר', accessorKey:'priceGapPct', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge variant={typeof value === 'number' && value > 0 ? 'warn' : 'good'}>{fmtPct(value)}</Badge>
    } },
  { header:'רמת ביטחון', accessorKey:'confidencePct', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge>{value !== undefined ? `${value}%` : '—'}</Badge>
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
        <Link className="underline" href={`/assets/${row.original.id}`}>👁️</Link>
        <a className="underline" href="/alerts">🔔</a>
        {onExport && (
          <button
            onClick={e => { e.stopPropagation(); onExport(row.original) }}
            className="underline">
            <Download className="h-4 w-4" />
          </button>
        )}
        {onDelete && (
          <button onClick={e => { e.stopPropagation(); onDelete(row.original.id) }} className="underline">
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

export default function AssetsTable({ data = [], loading = false, onDelete }: AssetsTableProps){
  const router = useRouter()
  const [rowSelection, setRowSelection] = React.useState({})

  const handleExportSingle = (asset: Asset) => exportAssetsCsv([asset])

  const columns = React.useMemo(() => createColumns(onDelete, handleExportSingle), [onDelete])

  const table = useReactTable({
    data,
    columns,
    state: { rowSelection },
    enableRowSelection: true,
    onRowSelectionChange: setRowSelection,
    getCoreRowModel: getCoreRowModel()
  })

  const handleRowClick = (asset: Asset) => {
    router.push(`/assets/${asset.id}`)
  }

  const handleExportSelected = () => {
    const selected = table.getSelectedRowModel().rows.map(r => r.original)
    exportAssetsCsv(selected)
  }

  const anySelected = table.getSelectedRowModel().rows.length > 0

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[linear-gradient(180deg,var(--panel),var(--card))] overflow-x-auto">
      <div className="p-2 flex justify-end">
        <Button onClick={handleExportSelected} disabled={!anySelected} variant="outline">
          <Download className="h-4 w-4" /> ייצוא נבחרים
        </Button>
      </div>
      <Table>
        <THead>
          <TR>
            {table.getFlatHeaders().map(h=>(
              <TH key={h.id} className={h.column.id==='address'?'sticky right-0 bg-[linear-gradient(180deg,var(--panel),var(--card))]':''}>
                {flexRender(h.column.columnDef.header, h.getContext())}
              </TH>
            ))}
          </TR>
        </THead>
        <TBody>
          {table.getRowModel().rows.map(row=>(
            <TR key={row.id} className="cursor-pointer hover:bg-blue-50/50 hover:shadow-sm transition-all duration-200 !hover:bg-blue-50" onClick={() => handleRowClick(row.original)}>
              {row.getVisibleCells().map(cell=>(
                <TD key={cell.id} className={cell.column.id==='address'?'sticky right-0 bg-[linear-gradient(180deg,var(--panel),var(--card))]':''}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TD>
              ))}
            </TR>
          ))}
        </TBody>
      </Table>
    </div>
  )
}
