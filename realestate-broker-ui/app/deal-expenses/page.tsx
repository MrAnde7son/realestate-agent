'use client'

import React, { useState, useEffect } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/Card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/Badge'
import { Separator } from '@/components/ui/separator'
import { fmtCurrency } from '@/lib/utils'
import { Buyer, calculatePurchaseTax } from '@/lib/purchase-tax'
import { calculateServiceCosts, type ServiceInput } from '@/lib/deal-expenses'
import { 
  Calculator, 
  Home, 
  Users, 
  Percent, 
  Plus, 
  Trash2, 
  Building, 
  Scale, 
  Hammer, 
  Sofa,
  FileText,
  TrendingUp,
  Info,
  Download,
  FileSpreadsheet,
  FileImage
} from 'lucide-react'

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

  function exportToCSV() {
    if (!result) return

    const csvData = [
      ['מחשבון הוצאות עסקה', ''],
      ['תאריך', new Date().toLocaleDateString('he-IL')],
      ['', ''],
      ['פרטי הנכס', ''],
      ['מחיר הנכס', fmtCurrency(price)],
      ['שטח הנכס', `${area} מ"ר`],
      ['', ''],
      ['מס רכישה', ''],
      ...result.breakdown.map((item, index) => [
        `מס רכישה - ${item.buyer.name || `רוכש ${index + 1}`} (${item.track === 'regular' ? 'רגיל' : 
         item.track === 'oleh' ? 'עולה חדש' :
         item.track === 'disabled' ? 'נכה/עיוור' :
         item.track === 'bereaved' ? 'משפחה שכולה' : item.track})`,
        fmtCurrency(item.tax)
      ]),
      ['סה"כ מס רכישה', fmtCurrency(result.totalTax)],
      ['', ''],
      ['הוצאות שירות', ''],
      ...result.serviceBreakdown.map(item => [item.label, fmtCurrency(item.cost)]),
      ['סה"כ הוצאות שירות', fmtCurrency(result.serviceTotal)],
      ['', ''],
      ['סיכום', ''],
      ['מחיר הנכס', fmtCurrency(price)],
      ['מס רכישה', fmtCurrency(result.totalTax)],
      ['הוצאות שירות', fmtCurrency(result.serviceTotal)],
      ['סה"כ לתשלום', fmtCurrency(result.total)],
      ['', ''],
      ['מחיר למ"ר לפני הוצאות', fmtCurrency(result.pricePerSqBefore)],
      ['מחיר למ"ר אחרי הוצאות', fmtCurrency(result.pricePerSqAfter)]
    ]

    const csvContent = csvData.map(row => row.join(',')).join('\n')
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `חישוב_הוצאות_עסקה_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
  }

  function exportToPDF() {
    if (!result) return

    // Create a new window for PDF generation
    const printWindow = window.open('', '_blank')
    if (!printWindow) return

    const htmlContent = `
      <!DOCTYPE html>
      <html dir="rtl" lang="he">
      <head>
        <meta charset="UTF-8">
        <title>חישוב הוצאות עסקה</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; direction: rtl; }
          .header { text-align: center; margin-bottom: 30px; }
          .header h1 { color: #2563eb; margin-bottom: 10px; }
          .section { margin-bottom: 25px; }
          .section h2 { color: #374151; border-bottom: 2px solid #e5e7eb; padding-bottom: 5px; }
          .row { display: flex; justify-content: space-between; margin: 8px 0; padding: 5px 0; }
          .row:nth-child(even) { background-color: #f9fafb; }
          .label { font-weight: bold; }
          .value { color: #059669; font-weight: bold; }
          .total { background-color: #dbeafe; padding: 15px; border-radius: 8px; margin: 20px 0; }
          .total .value { font-size: 1.2em; color: #1d4ed8; }
          .badge { background-color: #e5e7eb; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-right: 10px; }
          .footer { margin-top: 30px; text-align: center; color: #6b7280; font-size: 0.9em; }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>מחשבון הוצאות עסקה</h1>
          <p>תאריך: ${new Date().toLocaleDateString('he-IL')}</p>
        </div>

        <div class="section">
          <h2>פרטי הנכס</h2>
          <div class="row">
            <span class="label">מחיר הנכס:</span>
            <span class="value">${fmtCurrency(price)}</span>
          </div>
          <div class="row">
            <span class="label">שטח הנכס:</span>
            <span class="value">${area} מ"ר</span>
          </div>
        </div>

        <div class="section">
          <h2>מס רכישה</h2>
          ${result.breakdown.map((item, index) => `
            <div class="row">
              <span class="label">
                מס רכישה - ${item.buyer.name || `רוכש ${index + 1}`}
                <span class="badge">${item.track === 'regular' ? 'רגיל' : 
                 item.track === 'oleh' ? 'עולה חדש' :
                 item.track === 'disabled' ? 'נכה/עיוור' :
                 item.track === 'bereaved' ? 'משפחה שכולה' : item.track}</span>
              </span>
              <span class="value">${fmtCurrency(item.tax)}</span>
            </div>
          `).join('')}
          <div class="row" style="border-top: 1px solid #d1d5db; margin-top: 10px; padding-top: 10px;">
            <span class="label">סה"כ מס רכישה:</span>
            <span class="value">${fmtCurrency(result.totalTax)}</span>
          </div>
        </div>

        <div class="section">
          <h2>הוצאות שירות</h2>
          ${result.serviceBreakdown.map(item => `
            <div class="row">
              <span class="label">${item.label}:</span>
              <span class="value">${fmtCurrency(item.cost)}</span>
            </div>
          `).join('')}
          <div class="row" style="border-top: 1px solid #d1d5db; margin-top: 10px; padding-top: 10px;">
            <span class="label">סה"כ הוצאות שירות:</span>
            <span class="value">${fmtCurrency(result.serviceTotal)}</span>
          </div>
        </div>

        <div class="total">
          <div class="row">
            <span class="label">סה"כ לתשלום:</span>
            <span class="value">${fmtCurrency(result.total)}</span>
          </div>
        </div>

        <div class="section">
          <h2>מחיר למ"ר</h2>
          <div class="row">
            <span class="label">לפני הוצאות:</span>
            <span class="value">${fmtCurrency(result.pricePerSqBefore)}</span>
          </div>
          <div class="row">
            <span class="label">אחרי הוצאות:</span>
            <span class="value">${fmtCurrency(result.pricePerSqAfter)}</span>
          </div>
        </div>

        <div class="footer">
          <p>נוצר על ידי מחשבון הוצאות עסקה - ${new Date().toLocaleDateString('he-IL')}</p>
        </div>
      </body>
      </html>
    `

    printWindow.document.write(htmlContent)
    printWindow.document.close()
    printWindow.focus()
    
    // Wait for content to load then print
    setTimeout(() => {
      printWindow.print()
    }, 500)
  }

  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader 
          heading="מחשבון הוצאות עסקה" 
          text="חישוב מדויק של כל העלויות הכרוכות ברכישת נכס"
        />

        {/* VAT Rate Display */}
        <Card className="mb-6">
          <CardContent className="flex items-center justify-between p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                <Info className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <div className="text-sm text-muted-foreground">מע&quot;מ נוכחי</div>
                <div className="text-2xl font-bold">{(vatRate * 100).toFixed(1)}%</div>
              </div>
            </div>
            {vatUpdated && (
              <Badge variant="neutral">
                עדכון אחרון: {new Date(vatUpdated).toLocaleDateString('he-IL')}
              </Badge>
            )}
          </CardContent>
        </Card>

        {/* Transaction details & Buyers */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Transaction Details */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                  <Home className="h-5 w-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <CardTitle>פרטי הנכס</CardTitle>
                  <CardDescription>הזן את פרטי הנכס לרכישה</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="price" className="text-sm font-medium">
                  מחיר הנכס
                </Label>
                <div className="relative">
                  <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground font-medium">₪</span>
                  <Input 
                    id="price" 
                    type="number" 
                    value={price} 
                    onChange={e => setPrice(parseInt(e.target.value) || 0)}
                    className="pr-10"
                    placeholder="3,000,000"
                  />
                </div>
                <div className="text-xs text-muted-foreground">
                  {fmtCurrency(price)}
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="area" className="text-sm font-medium">
                  שטח הנכס
                </Label>
                <div className="relative">
                  <Building className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input 
                    id="area" 
                    type="number" 
                    value={area} 
                    onChange={e => setArea(parseInt(e.target.value) || 0)}
                    className="pr-10"
                    placeholder="100"
                  />
                </div>
                <div className="text-xs text-muted-foreground">
                  {area} מ&quot;ר
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Buyers */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
                    <Users className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <CardTitle>רוכשים</CardTitle>
                    <CardDescription>הגדר את פרטי הרוכשים</CardDescription>
                  </div>
                </div>
                <Button onClick={addBuyer} size="sm" variant="outline">
                  <Plus className="h-4 w-4" />
                  הוסף רוכש
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {buyers.map((buyer, index) => (
                <Card key={index} variant="outlined" className="p-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium text-sm">רוכש {index + 1}</h4>
                      {buyers.length > 1 && (
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => removeBuyer(index)}
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-2">
                        <Label className="text-xs">שם הרוכש</Label>
                        <Input 
                          placeholder="שם מלא" 
                          value={buyer.name} 
                          onChange={e => handleBuyerChange(index, 'name', e.target.value)} 
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs">אחוז בעלות</Label>
                        <div className="relative">
                          <Percent className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input 
                            placeholder="100" 
                            type="number" 
                            value={buyer.sharePct} 
                            onChange={e => handleBuyerChange(index, 'sharePct', parseFloat(e.target.value) || 0)}
                            className="pr-10"
                          />
                        </div>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <Label className="text-xs text-muted-foreground">הטבות מיוחדות</Label>
                      <div className="grid grid-cols-2 gap-3">
                        <label className="flex items-center space-x-2 space-x-reverse cursor-pointer">
                          <Switch 
                            checked={buyer.isFirstHome} 
                            onCheckedChange={v => handleBuyerChange(index, 'isFirstHome', v)} 
                          />
                          <span className="text-sm">דירה יחידה</span>
                        </label>
                        <label className="flex items-center space-x-2 space-x-reverse cursor-pointer">
                          <Switch 
                            checked={buyer.isReplacementHome} 
                            onCheckedChange={v => handleBuyerChange(index, 'isReplacementHome', v)} 
                          />
                          <span className="text-sm">דירה חלופית</span>
                        </label>
                        <label className="flex items-center space-x-2 space-x-reverse cursor-pointer">
                          <Switch 
                            checked={buyer.oleh} 
                            onCheckedChange={v => handleBuyerChange(index, 'oleh', v)} 
                          />
                          <span className="text-sm">עולה חדש</span>
                        </label>
                        <label className="flex items-center space-x-2 space-x-reverse cursor-pointer">
                          <Switch 
                            checked={buyer.disabled} 
                            onCheckedChange={v => handleBuyerChange(index, 'disabled', v)} 
                          />
                          <span className="text-sm">נכה/עיוור</span>
                        </label>
                        <label className="flex items-center space-x-2 space-x-reverse cursor-pointer col-span-2">
                          <Switch 
                            checked={buyer.bereavedFamily} 
                            onCheckedChange={v => handleBuyerChange(index, 'bereavedFamily', v)} 
                          />
                          <span className="text-sm">משפחה שכולה</span>
                        </label>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Service costs */}
        <Card className="mt-6">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 dark:bg-orange-900/20 rounded-lg">
                <Calculator className="h-5 w-5 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <CardTitle>עלויות נלוות</CardTitle>
                <CardDescription>הוסף עלויות שירות ושיפוץ</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              {(Object.keys(services) as ServiceKey[]).map((key) => (
                <Card key={key} variant="outlined" className="p-4">
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      {getServiceIcon(key)}
                      <span className="font-medium">{labelMap[key]}</span>
                    </div>
                    
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-2">
                          <Label className="text-xs">אחוז מהמחיר</Label>
                          <div className="relative">
                            <Percent className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                              placeholder="0"
                              type="number"
                              value={services[key].percent ?? ''}
                              onChange={e => handleServiceChange(key, 'percent', parseFloat(e.target.value) || 0)}
                              className="pr-10"
                            />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label className="text-xs">סכום קבוע</Label>
                          <div className="relative">
                            <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground font-medium">₪</span>
                            <Input
                              placeholder="0"
                              type="number"
                              value={services[key].amount ?? ''}
                              onChange={e => handleServiceChange(key, 'amount', parseFloat(e.target.value) || 0)}
                              className="pr-10"
                            />
                          </div>
                        </div>
                      </div>
                      
                      <label className="flex items-center space-x-2 space-x-reverse cursor-pointer">
                        <Switch
                          checked={services[key].includesVat}
                          onCheckedChange={v => handleServiceChange(key, 'includesVat', v)}
                        />
                        <span className="text-sm">כולל מע&quot;מ</span>
                      </label>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Calculate Button */}
        <div className="flex justify-center mt-8">
          <Button onClick={calculate} size="lg" className="px-8">
            <Calculator className="h-5 w-5 ml-2" />
            חשב הוצאות
          </Button>
        </div>

        {/* Export Buttons */}
        {result && (
          <div className="flex justify-center gap-4 mt-4">
            <Button onClick={exportToCSV} variant="outline" size="sm">
              <FileSpreadsheet className="h-4 w-4 ml-2" />
              ייצא ל-CSV
            </Button>
            <Button onClick={exportToPDF} variant="outline" size="sm">
              <FileImage className="h-4 w-4 ml-2" />
              ייצא ל-PDF
            </Button>
          </div>
        )}

        {/* Results */}
        {result && (
          <Card className="mt-8">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                  <TrendingUp className="h-5 w-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <CardTitle>תוצאות החישוב</CardTitle>
                  <CardDescription>סיכום מפורט של כל העלויות</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">

              {/* Detailed Breakdown */}
              <div className="space-y-4">
                <h4 className="font-semibold">פירוט הוצאות העסקה</h4>
                <div className="space-y-2">
                  {/* Property Price */}
                  <div className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Home className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">מחיר הנכס</span>
                    </div>
                    <span className="font-semibold">{fmtCurrency(price)}</span>
                  </div>

                  {/* Purchase Tax Breakdown */}
                  {result.breakdown.map((item, index) => (
                    <div key={`tax-${index}`} className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Scale className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">
                          מס רכישה - {item.buyer.name || `רוכש ${index + 1}`}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {item.track === 'regular' ? 'רגיל' : 
                           item.track === 'oleh' ? 'עולה חדש' :
                           item.track === 'disabled' ? 'נכה/עיוור' :
                           item.track === 'bereaved' ? 'משפחה שכולה' : item.track}
                        </Badge>
                      </div>
                      <span className="font-semibold">{fmtCurrency(item.tax)}</span>
                    </div>
                  ))}

                  {/* Service Costs Breakdown */}
                  {result.serviceBreakdown.map((item, index) => (
                    <div key={`service-${index}`} className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Calculator className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{item.label}</span>
                      </div>
                      <span className="font-semibold">{fmtCurrency(item.cost)}</span>
                    </div>
                  ))}

                  {/* Total */}
                  <div className="flex justify-between items-center p-4 bg-primary/10 rounded-lg border-2 border-primary/20">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-primary" />
                      <span className="font-bold text-lg">סה&quot;כ לתשלום</span>
                    </div>
                    <span className="font-bold text-xl text-primary">{fmtCurrency(result.total)}</span>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Price per square meter */}
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm">מחיר למ&quot;ר לפני הוצאות</h4>
                  <div className="text-2xl font-bold text-muted-foreground">
                    {fmtCurrency(result.pricePerSqBefore)}
                  </div>
                </div>
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm">מחיר למ&quot;ר אחרי הוצאות</h4>
                  <div className="text-2xl font-bold text-primary">
                    {fmtCurrency(result.pricePerSqAfter)}
                  </div>
                </div>
              </div>

              {vatUpdated && (
                <div className="text-xs text-muted-foreground text-center pt-4 border-t">
                  עדכון מע&quot;מ אחרון: {new Date(vatUpdated).toLocaleDateString('he-IL')}
                </div>
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

const getServiceIcon = (key: string) => {
  const iconMap: Record<string, React.ReactNode> = {
    broker: <Users className="h-4 w-4 text-blue-600 dark:text-blue-400" />,
    lawyer: <FileText className="h-4 w-4 text-purple-600 dark:text-purple-400" />,
    appraiser: <Scale className="h-4 w-4 text-green-600 dark:text-green-400" />,
    renovation: <Hammer className="h-4 w-4 text-orange-600 dark:text-orange-400" />,
    furniture: <Sofa className="h-4 w-4 text-pink-600 dark:text-pink-400" />,
  }
  return iconMap[key] || <Calculator className="h-4 w-4 text-muted-foreground" />
}
