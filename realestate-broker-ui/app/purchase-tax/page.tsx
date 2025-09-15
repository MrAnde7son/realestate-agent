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
import { Buyer, Fees, calculatePurchaseTax, calculateTotalCost } from '@/lib/purchase-tax'

export default function PurchaseTaxPage() {
  const [price, setPrice] = useState<number>(3000000)
  const [size, setSize] = useState<number>(100)
  const [buyers, setBuyers] = useState<Buyer[]>([{ share: 100, firstApartment: true }])
  const [fees, setFees] = useState<Fees>({})
  const [vatRate, setVatRate] = useState<number>(0.17)

  useEffect(() => {
    fetch('/api/vat-rate').then(res => res.json()).then(d => {
      if (d.success && typeof d.data.rate === 'number') {
        setVatRate(d.data.rate)
      }
    }).catch(err => console.error('VAT fetch error', err))
  }, [])

  const updateBuyer = (index: number, field: Partial<Buyer>) => {
    setBuyers(prev => prev.map((b, i) => i === index ? { ...b, ...field } : b))
  }

  const addBuyer = () => {
    setBuyers(prev => [...prev, { share: 0, firstApartment: false }])
  }

  const tax = calculatePurchaseTax(price, buyers)
  const { total, feesWithVat } = calculateTotalCost(price, tax, fees, vatRate)
  const pricePerSqm = size > 0 ? total / size : 0

  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader heading="מחשבון מס רכישה" text="הערכת עלויות עסקה כולל מע"מ" />

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>פרטי העסקה</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">מחיר הנכס</label>
                <Input type="number" value={price} onChange={e => setPrice(parseInt(e.target.value) || 0)} />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">גודל במ"ר</label>
                <Input type="number" value={size} onChange={e => setSize(parseInt(e.target.value) || 0)} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>הוצאות נוספות</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {['broker','lawyer','appraiser','renovation','furniture'].map((field) => (
                <div key={field}>
                  <label className="block text-sm font-medium mb-2">{field}</label>
                  <Input type="number" value={(fees as any)[field] || ''} onChange={e => setFees({ ...fees, [field]: parseInt(e.target.value) || 0 })} />
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>רוכשים</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {buyers.map((buyer, idx) => (
              <div key={idx} className="p-4 border rounded-md space-y-2">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm mb-2">אחוז בעלות</label>
                    <Input type="number" value={buyer.share} onChange={e => updateBuyer(idx, { share: parseInt(e.target.value) || 0 })} />
                  </div>
                  <div className="flex items-center space-x-2 rtl:space-x-reverse">
                    <Switch checked={buyer.firstApartment} onCheckedChange={v => updateBuyer(idx, { firstApartment: v })} />
                    <Label>דירה יחידה</Label>
                  </div>
                </div>
                <div className="flex flex-wrap gap-4">
                  <div className="flex items-center space-x-2 rtl:space-x-reverse">
                    <Switch checked={buyer.oleh || false} onCheckedChange={v => updateBuyer(idx, { oleh: v })} />
                    <Label>עולה חדש</Label>
                  </div>
                  <div className="flex items-center space-x-2 rtl:space-x-reverse">
                    <Switch checked={buyer.disabled || false} onCheckedChange={v => updateBuyer(idx, { disabled: v })} />
                    <Label>נכות</Label>
                  </div>
                  <div className="flex items-center space-x-2 rtl:space-x-reverse">
                    <Switch checked={buyer.bereavedFamily || false} onCheckedChange={v => updateBuyer(idx, { bereavedFamily: v })} />
                    <Label>משפחה שכולה</Label>
                  </div>
                </div>
              </div>
            ))}
            <Button variant="outline" onClick={addBuyer}>הוסף רוכש</Button>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>סיכום</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between"><span>מחיר הנכס</span><span>{fmtCurrency(price)}</span></div>
            <div className="flex justify-between"><span>מס רכישה</span><span>{fmtCurrency(tax)}</span></div>
            <div className="flex justify-between"><span>הוצאות נוספות (כולל מע"מ { (vatRate*100).toFixed(1)}%)</span><span>{fmtCurrency(feesWithVat)}</span></div>
            <div className="flex justify-between font-bold"><span>מחיר כולל</span><span>{fmtCurrency(total)}</span></div>
            <div className="flex justify-between"><span>מחיר למ"ר</span><span>{fmtCurrency(pricePerSqm)}</span></div>
          </CardContent>
        </Card>

      </DashboardShell>
    </DashboardLayout>
  )
}
