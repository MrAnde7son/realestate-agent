'use client'
import * as React from 'react'
import { ColumnDef, flexRender, getCoreRowModel, useReactTable } from '@tanstack/react-table'
import { Listing } from '@/lib/types'
import { fmtCurrency, fmtNumber, fmtPct } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Table, THead, TBody, TR, TH, TD } from '@/components/ui/table'
import Link from 'next/link'
function RiskCell({ flags }: { flags?: string[] }){ if(!flags || flags.length===0) return <Badge variant='good'>ללא</Badge>; return <div className="flex gap-1 flex-wrap">{flags.map((f,i)=><Badge key={i} variant={f.includes('שימור')?'bad':f.includes('אנטנה')?'warn':'default'}>{f}</Badge>)}</div> }
const columns: ColumnDef<Listing>[] = [
  { header:'נכס', accessorKey:'address', cell: ({ row }) => (<div><div className="font-semibold"><Link href={`/listings/${row.original.id}`}>{row.original.address}</Link></div><div className="text-xs text-sub">{row.original.city}{row.original.neighborhood?` · ${row.original.neighborhood}`:''} · {row.original.type==='house'?'בית':'דירה'} · {row.original.netSqm??'—'} מ"ר נטו</div></div>) },
  { header:'₪', accessorKey:'price', cell: info => <span className="font-mono">{fmtCurrency(info.getValue() as number)}</span> },
  { header:'₪/מ"ר', accessorKey:'pricePerSqm', cell: info => <span className="font-mono">{fmtNumber(info.getValue() as number)}</span> },
  { header:'Δ מול איזור', accessorKey:'deltaVsAreaPct', cell: info => <Badge variant={(info.getValue() as number)>=0?'default':'bad'}>{fmtPct(info.getValue() as number)}</Badge> },
  { header:'DOM פרצנטיל', accessorKey:'domPercentile', cell: info => <Badge>{`P${info.getValue()}`}</Badge> },
  { header:'תחרות (1ק"מ)', accessorKey:'competition1km', cell: info => <Badge>{info.getValue() as string}</Badge> },
  { header:'זונינג', accessorKey:'zoning', cell: info => <Badge>{info.getValue() as string}</Badge> },
  { header:'יתרת זכויות', accessorKey:'remainingRightsSqm', cell: info => <Badge>{`~+${fmtNumber(info.getValue() as number)} מ"ר`}</Badge> },
  { header:'תכנית', accessorKey:'program', cell: info => <Badge>{info.getValue() as string}</Badge> },
  { header:'היתר עדכני', accessorKey:'lastPermitQ', cell: info => <Badge>{info.getValue() as string}</Badge> },
  { header:'קבצים', accessorKey:'docsCount', cell: info => <Badge>{fmtNumber(info.getValue() as number)}</Badge> },
  { header:'רעש', accessorKey:'noiseLevel', cell: info => <Badge>{`${info.getValue()}/5`}</Badge> },
  { header:'אנטנה (מ")', accessorKey:'antennaDistanceM', cell: info => <span className="font-mono">{fmtNumber(info.getValue() as number)}</span> },
  { header:'ירוק ≤300מ"', accessorKey:'greenWithin300m', cell: info => <Badge variant={(info.getValue() as boolean)?'good':'bad'}>{(info.getValue() as boolean)?'כן':'לא'}</Badge> },
  { header:'מקלט (מ")', accessorKey:'shelterDistanceM', cell: info => <span className="font-mono">{fmtNumber(info.getValue() as number)}</span> },
  { header:'סיכון', accessorKey:'riskFlags', cell: info => <RiskCell flags={info.getValue() as string[]}/> },
  { header:'מחיר מודל', accessorKey:'modelPrice', cell: info => <span className="font-mono">{fmtCurrency(info.getValue() as number)}</span> },
  { header:'פער למחיר', accessorKey:'priceGapPct', cell: info => <Badge variant={(info.getValue() as number)>0?'warn':'good'}>{fmtPct(info.getValue() as number)}</Badge> },
  { header:'Confidence', accessorKey:'confidencePct', cell: info => <Badge>{`${info.getValue()}%`}</Badge> },
  { header:'שכ"ד', accessorKey:'rentEstimate', cell: info => <span className="font-mono">{fmtCurrency(info.getValue() as number)}</span> },
  { header:'Cap-rate', accessorKey:'capRatePct', cell: info => <Badge>{`${(info.getValue() as number)?.toFixed(1)}%`}</Badge> },
  { header:'—', id:'actions', cell: ({ row }) => (<div className="flex gap-2"><Link className="underline" href={`/listings/${row.original.id}`}>👁️</Link><a className="underline" href="/alerts">🔔</a></div>) }
]
export default function ListingTable(){
  const [data, setData] = React.useState<Listing[]>([])
  React.useEffect(()=>{ fetch('/api/listings').then(r=>r.json()).then(res=>setData(res.rows)) },[])
  const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel() })
  return (<div className="rounded-xl border border-[var(--border)] bg-[linear-gradient(180deg,var(--panel),var(--card))] overflow-x-auto">
    <Table>
      <THead><TR>{table.getFlatHeaders().map((h,idx)=>(<TH key={h.id} className={idx===0?'sticky right-0 bg-[linear-gradient(180deg,var(--panel),var(--card))]':''}>{flexRender(h.column.columnDef.header, h.getContext())}</TH>))}</TR></THead>
      <TBody>{table.getRowModel().rows.map(row=>(<TR key={row.id}>{row.getVisibleCells().map((cell,idx)=>(<TD key={cell.id} className={idx===0?'sticky right-0 bg-[linear-gradient(180deg,var(--panel),var(--card))]':''}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TD>))}</TR>))}</TBody>
    </Table>
  </div>)
}
