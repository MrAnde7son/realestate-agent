'use client'
import * as React from 'react'
import { ColumnDef, flexRender, getCoreRowModel, useReactTable } from '@tanstack/react-table'
import { Asset } from '@/lib/data'
import { fmtCurrency, fmtNumber, fmtPct } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Table, THead, TBody, TR, TH, TD } from '@/components/ui/table'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Trash2 } from 'lucide-react'

function RiskCell({ flags }: { flags?: string[] }){ 
  if(!flags || flags.length===0) return <Badge variant='good'>ללא</Badge>; 
  return <div className="flex gap-1 flex-wrap">{flags.map((f,i)=><Badge key={i} variant={f.includes('שימור')?'bad':f.includes('אנטנה')?'warn':'default'}>{f}</Badge>)}</div> 
}

function createColumns(onDelete?: (id: number) => void): ColumnDef<Asset>[] {
  return [
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
  { header:'₪', accessorKey:'price', cell: info => <span className="font-mono">{fmtCurrency(info.getValue() as number)}</span> },
  { header:'₪/מ"ר', accessorKey:'pricePerSqm', cell: info => <span className="font-mono">{fmtNumber(info.getValue() as number)}</span> },
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
  { header:'אנטנה (מ")', accessorKey:'antennaDistanceM', cell: info => <span className="font-mono">{fmtNumber(info.getValue() as number)}</span> },
  { header:'שטחי ציבור ≤300מ"', accessorKey:'greenWithin300m', cell: info => {
      const value = info.getValue() as boolean | undefined
      return <Badge variant={value === undefined ? 'default' : value ? 'good' : 'bad'}>{value === undefined ? '—' : value ? 'כן' : 'לא'}</Badge>
    } },
  { header:'מקלט (מ")', accessorKey:'shelterDistanceM', cell: info => <span className="font-mono">{fmtNumber(info.getValue() as number)}</span> },
  { header:'סיכון', accessorKey:'riskFlags', cell: info => <RiskCell flags={info.getValue() as string[]}/> },
  { header:'סטטוס נכס', accessorKey:'assetStatus', cell: info => {
    const status = info.getValue() as string
    if (!status) return <Badge variant="default">—</Badge>
    const variant = status === 'ready' ? 'good' : status === 'error' ? 'bad' : 'warn'
    const label = status === 'ready' ? 'מוכן' : status === 'error' ? 'שגיאה' : status === 'enriching' ? 'מתעשר' : 'ממתין'
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
  { header:'שכ"ד', accessorKey:'rentEstimate', cell: info => <span className="font-mono">{fmtCurrency(info.getValue() as number)}</span> },
    { header:'תשואה', accessorKey:'capRatePct', cell: info => {
      const value = info.getValue() as number | undefined
      return <Badge>{typeof value === 'number' ? `${value.toFixed(1)}%` : '—'}</Badge>
    } },
    { header:'—', id:'actions', cell: ({ row }) => (
      <div className="flex gap-2">
        <Link className="underline" href={`/assets/${row.original.id}`}>👁️</Link>
        <a className="underline" href="/alerts">🔔</a>
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
  const columns = React.useMemo(() => createColumns(onDelete), [onDelete])
  const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel() })
  
  const handleRowClick = (asset: Asset) => {
    router.push(`/assets/${asset.id}`)
  }
  
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[linear-gradient(180deg,var(--panel),var(--card))] overflow-x-auto">
      <Table>
        <THead>
          <TR>
            {table.getFlatHeaders().map((h,idx)=>(
              <TH key={h.id} className={idx===0?'sticky right-0 bg-[linear-gradient(180deg,var(--panel),var(--card))]':''}>
                {flexRender(h.column.columnDef.header, h.getContext())}
              </TH>
            ))}
          </TR>
        </THead>
        <TBody>
          {table.getRowModel().rows.map(row=>(
            <TR key={row.id} className="cursor-pointer hover:bg-blue-50/50 hover:shadow-sm transition-all duration-200 !hover:bg-blue-50" onClick={() => handleRowClick(row.original)}>
              {row.getVisibleCells().map((cell,idx)=>(
                <TD key={cell.id} className={idx===0?'sticky right-0 bg-[linear-gradient(180deg,var(--panel),var(--card))]':''}>
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
