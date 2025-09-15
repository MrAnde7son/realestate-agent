'use client'

import React, { useState, useEffect } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { fmtCurrency } from '@/lib/utils'
import { Buyer, calculatePurchaseTax } from '@/lib/purchase-tax'
import { calculateServiceCosts, type ServiceInput } from '@/lib/deal-expenses'

export default function DealExpensesPage() {
  const [price, setPrice] = useState(3_000_000)
  const [area, setArea] = useState(100)
  const [buyers, setBuyers] = useState<Buyer[]>([{ name: '', sharePct: 100, isFirstHome: true }])
  const [vatRate, setVatRate] = useState(0.18)
  const [vatUpdated, setVatUpdated] = useState('')

  type ServiceKey = 'broker' | 'lawyer' | 'appraiser' | 'renovation' | 'furniture'
  type ServiceState = Record<ServiceKey, { percent?: number; amount?: number; includesVat: boolean }>
  const [services, setServices] = useState<ServiceState>({
    broker: { percent: 0, amount: 0, includesVat: false },
    lawyer: { percent: 0, amount: 0, includesVat: false },
    appraiser: { percent: 0, amount: 0, includesVat: false },
    renovation: { percent: 0, amount: 0, includesVat: false },
    furniture: { percent: 0, amount: 0, includesVat: false },
  })

  const [result, setResult] = useState<null | {
    totalTax: number
    breakdown: { buyer: Buyer; tax: number; track: string }[]
    serviceTotal: number
    serviceBreakdown: { label: string; cost: number }[]
    total: number
    pricePerSqBefore: number
    pricePerSqAfter: number
  }>(null)

  useEffect(() => {
    fetch('/api/vat')
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setVatRate(data.data.rate)
          setVatUpdated(data.data.updatedAt)
        }
      })
      .catch(() => {})
  }, [])

  function handleBuyerChange(index: number, field: keyof Buyer, value: any) {
    const list = [...buyers]
    ;(list[index] as any)[field] = value
    setBuyers(list)
  }

  function addBuyer() {
    setBuyers([...buyers, { name: '', sharePct: 0 }])
  }

  function removeBuyer(index: number) {
    setBuyers(buyers.filter((_, i) => i !== index))
  }

  function handleServiceChange(key: ServiceKey, field: string, value: any) {
    setServices(prev => ({ ...prev, [key]: { ...prev[key], [field]: value } }))
  }

  function calculate() {
    const { totalTax, breakdown } = calculatePurchaseTax(price, buyers)
    const serviceInputs: ServiceInput[] = (
      Object.keys(services) as ServiceKey[]
    ).map((k) => ({ label: labelMap[k], ...services[k] }))
    const { total: serviceTotal, breakdown: serviceBreakdown } = calculateServiceCosts(price, serviceInputs, vatRate)
    const total = price + totalTax + serviceTotal
    const pricePerSqBefore = area > 0 ? price / area : 0
    const pricePerSqAfter = area > 0 ? total / area : 0
    setResult({ totalTax, breakdown, serviceTotal, serviceBreakdown, total, pricePerSqBefore, pricePerSqAfter })
  }

  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader heading="מחשבון הוצאות עסקה" text={`מע"מ נוכחי ${(vatRate * 100).toFixed(1)}%`} />

        {/* Transaction details & Buyers */}
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>פרטי עסקה</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="price">מחיר הנכס</Label>
                <Input id="price" type="number" value={price} onChange={e => setPrice(parseInt(e.target.value) || 0)} />
              </div>
              <div>
                <Label htmlFor="area">שטח (מ&quot;ר)</Label>
                <Input id="area" type="number" value={area} onChange={e => setArea(parseInt(e.target.value) || 0)} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>רוכשים</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {buyers.map((b, i) => (
                <div key={i} className="border rounded p-2 space-y-2">
                  <div className="flex gap-2">
                    <Input placeholder="שם" value={b.name} onChange={e => handleBuyerChange(i, 'name', e.target.value)} />
                    <Input placeholder="%" type="number" value={b.sharePct} onChange={e => handleBuyerChange(i, 'sharePct', parseFloat(e.target.value) || 0)} />
                    {buyers.length > 1 && (
                      <Button variant="destructive" onClick={() => removeBuyer(i)}>
                        X
                      </Button>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-4">
                    <label className="flex items-center space-x-2 space-x-reverse">
                      <Switch checked={b.isFirstHome} onCheckedChange={v => handleBuyerChange(i, 'isFirstHome', v)} />
                      <span>דירה יחידה</span>
                    </label>
                    <label className="flex items-center space-x-2 space-x-reverse">
                      <Switch checked={b.isReplacementHome} onCheckedChange={v => handleBuyerChange(i, 'isReplacementHome', v)} />
                      <span>דירה חלופית</span>
                    </label>
                    <label className="flex items-center space-x-2 space-x-reverse">
                      <Switch checked={b.oleh} onCheckedChange={v => handleBuyerChange(i, 'oleh', v)} />
                      <span>עולה חדש</span>
                    </label>
                    <label className="flex items-center space-x-2 space-x-reverse">
                      <Switch checked={b.disabled} onCheckedChange={v => handleBuyerChange(i, 'disabled', v)} />
                      <span>נכה/עיוור</span>
                    </label>
                    <label className="flex items-center space-x-2 space-x-reverse">
                      <Switch checked={b.bereavedFamily} onCheckedChange={v => handleBuyerChange(i, 'bereavedFamily', v)} />
                      <span>משפחה שכולה</span>
                    </label>
                  </div>
                </div>
              ))}
              <Button onClick={addBuyer} variant="secondary">
                הוסף רוכש
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Service costs */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>עלויות נלוות</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {(Object.keys(services) as ServiceKey[]).map((key) => (
              <div key={key} className="grid gap-2">
                <div className="font-medium">{labelMap[key]}</div>
                <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
                  <Input
                    placeholder="%"
                    type="number"
                    value={services[key].percent ?? ''}
                    onChange={e => handleServiceChange(key, 'percent', parseFloat(e.target.value) || 0)}
                  />
                  <Input
                    placeholder="₪"
                    type="number"
                    value={services[key].amount ?? ''}
                    onChange={e => handleServiceChange(key, 'amount', parseFloat(e.target.value) || 0)}
                  />
                  <label className="flex items-center space-x-2 space-x-reverse col-span-2 md:col-span-1">
                    <Switch
                      checked={services[key].includesVat}
                      onCheckedChange={v => handleServiceChange(key, 'includesVat', v)}
                    />
                      <span>כולל מע&quot;מ?</span>
                  </label>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="flex justify-end mt-4">
          <Button onClick={calculate}>חשב</Button>
        </div>

        {result && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>תוצאות</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="font-semibold">מס רכישה כולל: {fmtCurrency(result.totalTax)}</div>
              <ul className="pl-4 list-disc space-y-1">
                {result.breakdown.map((b, i) => (
                  <li key={i}>
                    {(b.buyer.name || `רוכש ${i + 1}`)}: {fmtCurrency(b.tax)} ({b.track})
                  </li>
                ))}
              </ul>
              <div className="font-semibold mt-2">הוצאות שירות ושיפוץ: {fmtCurrency(result.serviceTotal)}</div>
                <div className="font-semibold">סה&quot;כ לתשלום: {fmtCurrency(result.total)}</div>
                <div>מחיר למ&quot;ר לפני: {fmtCurrency(result.pricePerSqBefore)}</div>
                <div>מחיר למ&quot;ר אחרי: {fmtCurrency(result.pricePerSqAfter)}</div>
                {vatUpdated && (
                  <div className="text-sm text-muted-foreground">עדכון מע&quot;מ: {new Date(vatUpdated).toLocaleDateString('he-IL')}</div>
                )}
            </CardContent>
          </Card>
        )}
      </DashboardShell>
    </DashboardLayout>
  )
}

const labelMap: Record<string, string> = {
  broker: 'מתווך',
  lawyer: 'עו"ד',
  appraiser: 'שמאי',
  renovation: 'שיפוץ',
  furniture: 'ריהוט',
}
