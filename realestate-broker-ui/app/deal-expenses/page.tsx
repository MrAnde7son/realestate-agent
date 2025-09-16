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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { fmtCurrency } from '@/lib/utils'
import { Buyer, calculatePurchaseTax } from '@/lib/purchase-tax'
import { calculateServiceCosts, type ServiceInput } from '@/lib/deal-expenses'
import type { Asset } from '@/lib/normalizers/asset'
import { useAnalytics } from '@/hooks/useAnalytics'

type PropertyType = 'residential' | 'land'
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
  FileSpreadsheet,
  FileImage,
  Search,
  X,
  MapPin,
  LandPlot,
  PiggyBank,
  ClipboardCheck,
  Receipt
} from 'lucide-react'

export default function DealExpensesPage() {
  const { trackCalculatorUsage, trackCalculatorCalculation, trackCalculatorExport } = useAnalytics()
  
  const [price, setPrice] = useState(3_000_000)
  const [area, setArea] = useState(100)
  const [propertyType, setPropertyType] = useState<PropertyType>('residential')
  const [buyers, setBuyers] = useState<Buyer[]>([{ name: '', sharePct: 100, isFirstHome: true }])
  const [vatRate, setVatRate] = useState(0.18)
  const [vatUpdated, setVatUpdated] = useState('')

  // Default construction cost per sqm
  const defaultConstructionCost = 8000 // ₪8,000 per sqm including VAT

  const [constructionArea, setConstructionArea] = useState(0)
  const [constructionCostPerSqm, setConstructionCostPerSqm] = useState(defaultConstructionCost)
  const [constructionIncludesVat, setConstructionIncludesVat] = useState(true) // Default to including VAT
  
  // Asset selection state
  const [assets, setAssets] = useState<Asset[]>([])
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null)
  const [assetSearchQuery, setAssetSearchQuery] = useState('')
  const [showAssetDropdown, setShowAssetDropdown] = useState(false)
  const [loadingAssets, setLoadingAssets] = useState(false)

  type ServiceKey =
    | 'broker'
    | 'mortgage'
    | 'inspection'
    | 'lawyer'
    | 'appraiser'
    | 'renovation'
    | 'furniture'
  type ServiceState = Record<ServiceKey, { percent?: number; amount?: number; includesVat: boolean }>
  
  // Default values based on industry standards
  const defaultValues: ServiceState = {
    lawyer: { percent: 1, amount: 0, includesVat: false }, // 1% + VAT
    appraiser: { percent: 0, amount: 3000, includesVat: true }, // ₪3,000 including VAT
    inspection: { percent: 0, amount: 2500, includesVat: true }, // ₪2,500 including VAT
    broker: { percent: 2, amount: 0, includesVat: false }, // 2% + VAT
    mortgage: { percent: 0, amount: 8000, includesVat: true }, // ₪8,000 including VAT
    renovation: { percent: 0, amount: 1500, includesVat: true }, // ₪1,500 per sqm including VAT
    furniture: { percent: 0, amount: 100000, includesVat: true }, // ₪100,000 including VAT
  }
  
  // Initialize services with default values, calculating renovation based on initial area
  const getInitialServices = (): ServiceState => {
    const initialServices = { ...defaultValues }
    if (area > 0) {
      initialServices.renovation = {
        percent: 0,
        amount: defaultValues.renovation.amount! * area,
        includesVat: defaultValues.renovation.includesVat
      }
    }
    return initialServices
  }

  const [services, setServices] = useState<ServiceState>(getInitialServices())

  const isLand = propertyType === 'land'
  const baseConstructionEstimate = isLand ? (constructionArea || 0) * (constructionCostPerSqm || 0) : 0
  const effectiveConstructionCost = isLand
    ? (constructionIncludesVat ? baseConstructionEstimate : baseConstructionEstimate * (1 + vatRate))
    : 0

  const [result, setResult] = useState<null | {
    totalTax: number
    breakdown: { buyer: Buyer; tax: number; track: string }[]
    serviceTotal: number
    serviceBreakdown: { label: string; cost: number }[]
    total: number
    pricePerSqBefore: number
    pricePerSqAfter: number
    constructionCost: number
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
    
    // Track calculator page view
    trackCalculatorUsage('expense', 'page_view')
  }, [trackCalculatorUsage])

  // Load assets when component mounts
  useEffect(() => {
    loadAssets()
  }, [])

  // Update renovation cost when area changes (since it's calculated per sqm)
  useEffect(() => {
    if (area > 0) {
      setServices(prev => ({
        ...prev,
        renovation: {
          percent: 0,
          amount: defaultValues.renovation.amount! * area,
          includesVat: defaultValues.renovation.includesVat
        }
      }))
    }
  }, [area])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Element
      if (showAssetDropdown && !target.closest('.asset-dropdown-container')) {
        setShowAssetDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showAssetDropdown])

  async function loadAssets() {
    setLoadingAssets(true)
    try {
      const response = await fetch('/api/assets')
      if (response.ok) {
        const data = await response.json()
        setAssets(data.rows || [])
      }
    } catch (error) {
      console.error('Error loading assets:', error)
    } finally {
      setLoadingAssets(false)
    }
  }

  function handleAssetSelect(asset: Asset) {
    setSelectedAsset(asset)
    setAssetSearchQuery('')
    setShowAssetDropdown(false)

    // Track asset selection
    trackCalculatorUsage('expense', 'asset_selected', {
      asset_id: asset.id,
      asset_address: asset.address,
      asset_city: asset.city,
      asset_price: asset.price,
      asset_area: asset.area
    })
    
    // Populate price and area from selected asset
    if (asset.price) {
      setPrice(asset.price)
    }
    if (asset.area) {
      setArea(asset.area)
    }

    if (asset.type) {
      const normalizedType = asset.type.toLowerCase()
      const assetIsLand = normalizedType.includes('קרקע') || normalizedType.includes('land')
      setPropertyType(assetIsLand ? 'land' : 'residential')
      trackCalculatorUsage('expense', 'input_change', {
        field: 'propertyType',
        value: assetIsLand ? 'land' : 'residential',
        selected_asset_id: asset.id,
        source: 'asset_select'
      })
    }
  }

  function handleAssetClear() {
    setSelectedAsset(null)
    setAssetSearchQuery('')
    setShowAssetDropdown(false)
  }

  function getFilteredAssets() {
    if (!assetSearchQuery.trim()) return assets.slice(0, 10) // Show first 10 if no search
    
    const query = assetSearchQuery.toLowerCase()
    return assets.filter(asset => 
      asset.address?.toLowerCase().includes(query) ||
      asset.city?.toLowerCase().includes(query) ||
      asset.street?.toLowerCase().includes(query) ||
      asset.neighborhood?.toLowerCase().includes(query)
    ).slice(0, 10)
  }

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
    
    // Track service input change
    trackCalculatorUsage('expense', 'service_input_change', {
      service_key: key,
      field,
      value,
      includes_vat: field === 'includesVat' ? value : services[key].includesVat
    })
  }

  function applyDefaultValue(key: ServiceKey) {
    const defaultValue = defaultValues[key]
    
    // Special handling for renovation - calculate based on area
    if (key === 'renovation' && area > 0) {
      const renovationAmount = defaultValue.amount! * area
      setServices(prev => ({ 
        ...prev, 
        [key]: { 
          percent: 0, 
          amount: renovationAmount, 
          includesVat: defaultValue.includesVat 
        } 
      }))
    } else {
      setServices(prev => ({ ...prev, [key]: { ...defaultValue } }))
    }
    
    // Track default value application
    trackCalculatorUsage('expense', 'default_value_applied', {
      service_key: key,
      default_value: defaultValue,
      area: key === 'renovation' ? area : undefined
    })
  }

  function applyAllDefaults() {
    const updatedServices = { ...defaultValues }
    
    // Special handling for renovation - calculate based on area
    if (area > 0) {
      updatedServices.renovation = {
        percent: 0,
        amount: defaultValues.renovation.amount! * area,
        includesVat: defaultValues.renovation.includesVat
      }
    }
    
    setServices(updatedServices)
    
    // Track all defaults application
    trackCalculatorUsage('expense', 'all_defaults_applied', {
      default_values: updatedServices,
      area: area
    })
  }

  function clearAllServices() {
    const clearedServices: ServiceState = {
      broker: { percent: 0, amount: 0, includesVat: false },
      mortgage: { percent: 0, amount: 0, includesVat: false },
      inspection: { percent: 0, amount: 0, includesVat: false },
      lawyer: { percent: 0, amount: 0, includesVat: false },
      appraiser: { percent: 0, amount: 0, includesVat: false },
      renovation: { percent: 0, amount: 0, includesVat: false },
      furniture: { percent: 0, amount: 0, includesVat: false },
    }
    setServices(clearedServices)
    
    // Track clear all
    trackCalculatorUsage('expense', 'all_services_cleared')
  }

  function applyDefaultConstructionCost() {
    setConstructionCostPerSqm(defaultConstructionCost)
    setConstructionIncludesVat(true)
    
    // Track default construction cost application
    trackCalculatorUsage('expense', 'default_construction_cost_applied', {
      default_cost: defaultConstructionCost,
      includes_vat: true
    })
  }

  // Input change handlers with analytics
  const handlePriceChange = (value: number) => {
    setPrice(value)
    trackCalculatorUsage('expense', 'input_change', {
      field: 'price',
      value,
      selected_asset_id: selectedAsset?.id
    })
  }

  const handleAreaChange = (value: number) => {
    setArea(value)
    trackCalculatorUsage('expense', 'input_change', {
      field: 'area',
      value,
      selected_asset_id: selectedAsset?.id
    })
  }

  const handlePropertyTypeChange = (value: PropertyType) => {
    setPropertyType(value)
    trackCalculatorUsage('expense', 'input_change', {
      field: 'propertyType',
      value,
      selected_asset_id: selectedAsset?.id
    })
  }

  const handleConstructionAreaChange = (value: number) => {
    setConstructionArea(value)
    trackCalculatorUsage('expense', 'input_change', {
      field: 'constructionArea',
      value,
      property_type: propertyType,
      selected_asset_id: selectedAsset?.id
    })
  }

  const handleConstructionCostChange = (value: number) => {
    setConstructionCostPerSqm(value)
    trackCalculatorUsage('expense', 'input_change', {
      field: 'constructionCostPerSqm',
      value,
      property_type: propertyType,
      selected_asset_id: selectedAsset?.id
    })
  }

  const handleConstructionVatChange = (value: boolean) => {
    setConstructionIncludesVat(value)
    trackCalculatorUsage('expense', 'input_change', {
      field: 'constructionIncludesVat',
      value,
      property_type: propertyType,
      selected_asset_id: selectedAsset?.id
    })
  }

  function calculate() {
    // Track calculation start
    trackCalculatorUsage('expense', 'calculation_start', {
      input_data: {
        price,
        area,
        propertyType,
        buyers_count: buyers.length,
        vatRate,
        constructionArea,
        constructionCostPerSqm,
        constructionIncludesVat,
        selected_asset_id: selectedAsset?.id,
        services: Object.keys(services).filter(key => {
          const service = services[key as ServiceKey]
          return service && ((service.percent ?? 0) > 0 || (service.amount ?? 0) > 0)
        })
      }
    })

    const { totalTax, breakdown } = calculatePurchaseTax(price, buyers, { propertyType })
    const serviceInputs: ServiceInput[] = (
      Object.keys(services) as ServiceKey[]
    ).map((k) => ({ label: labelMap[k], ...services[k] }))
    const { total: serviceTotal, breakdown: serviceBreakdown } = calculateServiceCosts(price, serviceInputs, vatRate)
    const constructionCost = effectiveConstructionCost
    const total = price + totalTax + serviceTotal + constructionCost
    const pricePerSqBefore = area > 0 ? price / area : 0
    const pricePerSqAfter = area > 0 ? total / area : 0

    const result = {
      totalTax,
      breakdown,
      serviceTotal,
      serviceBreakdown,
      total,
      pricePerSqBefore,
      pricePerSqAfter,
      constructionCost
    }
    setResult(result)

    // Track calculation completion
    trackCalculatorCalculation('expense', {
      price,
      area,
      propertyType,
      buyers_count: buyers.length,
      vatRate,
      constructionArea,
      constructionCostPerSqm,
      constructionIncludesVat,
      selected_asset_id: selectedAsset?.id
    }, {
      totalTax,
      serviceTotal,
      constructionCost,
      total,
      pricePerSqBefore,
      pricePerSqAfter,
      breakdown_count: breakdown.length,
      service_breakdown_count: serviceBreakdown.length
    })
  }

  function exportToCSV() {
    if (!result) return

    // Track export action
    trackCalculatorExport('expense', 'csv', {
      total_amount: result.total,
      price: price,
      area: area,
      buyers_count: buyers.length
    })

    const propertyTypeLabel = isLand ? 'קרקע' : 'נכס בנוי'

    const csvData = [
      ['מחשבון הוצאות עסקה', ''],
      ['תאריך', new Date().toLocaleDateString('he-IL')],
      ['', ''],
      ['פרטי הנכס', ''],
      ['סוג הנכס', propertyTypeLabel],
      ['מחיר הנכס', fmtCurrency(price)],
      ['שטח הנכס', `${area} מ&quot;ר`],
    ]

    if (isLand) {
      csvData.push(
        ['שטח בנוי מתוכנן', `${constructionArea} מ&quot;ר`],
        ['עלות בנייה למ&quot;ר', fmtCurrency(constructionCostPerSqm)],
        ['האם העלות שהוזנה כוללת מע"מ', constructionIncludesVat ? 'כן' : 'לא']
      )
    }

    csvData.push(
      ['', ''],
      ['מס רכישה', ''],
      ...result.breakdown.map((item, index) => [
        `מס רכישה - ${item.buyer.name || `רוכש ${index + 1}`} (${item.track === 'regular' ? 'רגיל' :
         item.track === 'oleh' ? 'עולה חדש' :
         item.track === 'disabled' ? 'נכה/עיוור' :
         item.track === 'bereaved' ? 'משפחה שכולה' : item.track === 'land' ? 'קרקע' : item.track})`,
        fmtCurrency(item.tax)
      ]),
      ['סה&quot;כ מס רכישה', fmtCurrency(result.totalTax)]
    )

    if (isLand) {
      csvData.push(
        ['', ''],
        ['עלויות בנייה', ''],
        ['סה&quot;כ עלות בנייה', fmtCurrency(result.constructionCost)]
      )
    }

    csvData.push(
      ['', ''],
      ['הוצאות עיסקה', ''],
      ...result.serviceBreakdown.map(item => [item.label, fmtCurrency(item.cost)]),
      ['סה&quot;כ הוצאות עיסקה', fmtCurrency(result.serviceTotal)],
      ['', ''],
      ['סיכום', ''],
      ['מחיר הנכס', fmtCurrency(price)],
      ['מס רכישה', fmtCurrency(result.totalTax)],
      ['הוצאות עיסקה', fmtCurrency(result.serviceTotal)]
    )

    if (isLand) {
      csvData.push(['עלות בנייה', fmtCurrency(result.constructionCost)])
    }

    csvData.push(
      ['סה&quot;כ לתשלום', fmtCurrency(result.total)],
      ['', ''],
      ['מחיר למ&quot;ר לפני הוצאות', fmtCurrency(result.pricePerSqBefore)],
      ['מחיר למ&quot;ר אחרי הוצאות', fmtCurrency(result.pricePerSqAfter)]
    )

    const csvContent = csvData.map(row => row.join(',')).join('\n')
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `חישוב_הוצאות_עסקה_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
  }

  function exportToPDF() {
    if (!result) return

    // Track export action
    trackCalculatorExport('expense', 'pdf', {
      total_amount: result.total,
      price: price,
      area: area,
      buyers_count: buyers.length
    })

    // Create a new window for PDF generation
    const printWindow = window.open('', '_blank')
    if (!printWindow) return

    const propertyTypeLabel = isLand ? 'קרקע' : 'נכס בנוי'

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
            <span class="label">סוג הנכס:</span>
            <span class="value">${propertyTypeLabel}</span>
          </div>
          <div class="row">
            <span class="label">מחיר הנכס:</span>
            <span class="value">${fmtCurrency(price)}</span>
          </div>
          <div class="row">
            <span class="label">שטח הנכס:</span>
            <span class="value">${area} מ&quot;ר</span>
          </div>
          ${isLand ? `
          <div class="row">
            <span class="label">שטח בנוי מתוכנן:</span>
            <span class="value">${constructionArea} מ&quot;ר</span>
          </div>
          <div class="row">
            <span class="label">עלות בנייה למ&quot;ר:</span>
            <span class="value">${fmtCurrency(constructionCostPerSqm)}</span>
          </div>
          <div class="row">
            <span class="label">האם העלות שהוזנה כוללת מע"מ:</span>
            <span class="value">${constructionIncludesVat ? 'כן' : 'לא'}</span>
          </div>
          ` : ''}
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
                 item.track === 'bereaved' ? 'משפחה שכולה' :
                 item.track === 'land' ? 'קרקע' : item.track}</span>
              </span>
              <span class="value">${fmtCurrency(item.tax)}</span>
            </div>
          `).join('')}
          <div class="row" style="border-top: 1px solid #d1d5db; margin-top: 10px; padding-top: 10px;">
            <span class="label">סה&quot;כ מס רכישה:</span>
            <span class="value">${fmtCurrency(result.totalTax)}</span>
          </div>
        </div>

        ${isLand ? `
        <div class="section">
          <h2>עלויות בנייה</h2>
          <div class="row">
            <span class="label">סה&quot;כ עלות בנייה:</span>
            <span class="value">${fmtCurrency(result.constructionCost)}</span>
          </div>
        </div>
        ` : ''}

        <div class="section">
          <h2>הוצאות עיסקה</h2>
          ${result.serviceBreakdown.map(item => `
            <div class="row">
              <span class="label">${item.label}:</span>
              <span class="value">${fmtCurrency(item.cost)}</span>
            </div>
          `).join('')}
          <div class="row" style="border-top: 1px solid #d1d5db; margin-top: 10px; padding-top: 10px;">
            <span class="label">סה&quot;כ הוצאות עיסקה:</span>
            <span class="value">${fmtCurrency(result.serviceTotal)}</span>
          </div>
        </div>

        <div class="total">
          <div class="row">
            <span class="label">סה&quot;כ לתשלום:</span>
            <span class="value">${fmtCurrency(result.total)}</span>
          </div>
        </div>

        <div class="section">
          <h2>מחיר למ&quot;ר</h2>
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
                <Label htmlFor="property-type" className="text-sm font-medium">
                  סוג הנכס
                </Label>
                <Select value={propertyType} onValueChange={value => handlePropertyTypeChange(value as PropertyType)}>
                  <SelectTrigger id="property-type" className="w-full">
                    <SelectValue placeholder="בחר סוג נכס" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="residential">נכס בנוי</SelectItem>
                    <SelectItem value="land">קרקע</SelectItem>
                  </SelectContent>
                </Select>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  {isLand ? (
                    <LandPlot className="h-3.5 w-3.5" />
                  ) : (
                    <Home className="h-3.5 w-3.5" />
                  )}
                  <span>סוג הנכס משפיע על מס הרכישה ועל העלויות הנלוות</span>
                </div>
              </div>

              <Separator />

              {/* Asset Selection */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">
                  בחר נכס קיים (אופציונלי)
                </Label>
                <div className="relative">
                  {selectedAsset ? (
                    <div className="flex items-center justify-between p-3 border rounded-lg bg-muted/50">
                      <div className="flex items-center gap-3">
                        <MapPin className="h-4 w-4 text-muted-foreground" />
                        <div className="flex-1">
                          <div className="font-medium">{selectedAsset.address}</div>
                          <div className="text-sm text-muted-foreground">
                            {selectedAsset.city}
                            {selectedAsset.neighborhood && ` • ${selectedAsset.neighborhood}`}
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {selectedAsset.area} מ&quot;ר • {fmtCurrency(selectedAsset.price || 0)}
                            {selectedAsset.rooms && ` • ${selectedAsset.rooms} חדרים`}
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleAssetClear}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ) : (
                    <div className="relative asset-dropdown-container">
                      <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="חפש נכס לפי כתובת, עיר או שכונה..."
                        value={assetSearchQuery}
                        onChange={e => {
                          setAssetSearchQuery(e.target.value)
                          setShowAssetDropdown(true)
                        }}
                        onFocus={() => setShowAssetDropdown(true)}
                        className="pr-10"
                      />
                      {showAssetDropdown && (
                        <div className="absolute top-full left-0 right-0 z-50 mt-1 bg-background border rounded-lg shadow-lg max-h-60 overflow-y-auto">
                          {loadingAssets ? (
                            <div className="p-3 text-center text-muted-foreground">
                              טוען נכסים...
                            </div>
                          ) : getFilteredAssets().length > 0 ? (
                            getFilteredAssets().map(asset => (
                              <button
                                key={asset.id}
                                className="w-full text-right p-3 hover:bg-muted/50 border-b last:border-b-0"
                                onClick={() => handleAssetSelect(asset)}
                              >
                                <div className="font-medium">{asset.address}</div>
                                <div className="text-sm text-muted-foreground">
                                  {asset.city}
                                  {asset.neighborhood && ` • ${asset.neighborhood}`}
                                </div>
                                <div className="text-xs text-muted-foreground mt-1">
                                  {asset.area} מ&quot;ר • {fmtCurrency(asset.price || 0)}
                                  {asset.rooms && ` • ${asset.rooms} חדרים`}
                                </div>
                              </button>
                            ))
                          ) : (
                            <div className="p-3 text-center text-muted-foreground">
                              לא נמצאו נכסים
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">
                  בחירת נכס תמלא אוטומטית את המחיר והשטח
                </div>
              </div>

              <Separator />

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
                    onChange={e => handlePriceChange(parseInt(e.target.value) || 0)}
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
                    onChange={e => handleAreaChange(parseInt(e.target.value) || 0)}
                    className="pr-10"
                    placeholder="100"
                  />
                </div>
                <div className="text-xs text-muted-foreground">
                  {area} מ&quot;ר
                </div>
              </div>

              {isLand && (
                <>
                  <Separator />
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <Label className="text-sm font-medium">עלויות בנייה משוערות</Label>
                        <p className="text-xs text-muted-foreground">
                          הזן את שטח הבנייה המתוכנן ועלות הבנייה למטר כדי לחשב את ההשקעה הכוללת בפרויקט
                        </p>
                      </div>
                      <Button 
                        onClick={applyDefaultConstructionCost} 
                        size="sm" 
                        variant="outline"
                        className="text-xs"
                      >
                        <TrendingUp className="h-4 w-4 ml-2" />
                        ברירת מחדל
                      </Button>
                    </div>
                    
                    {/* Default construction cost hint */}
                    <div className="text-xs text-muted-foreground bg-muted/50 p-2 rounded">
                      <strong>ברירת מחדל:</strong> {fmtCurrency(defaultConstructionCost)} למ&quot;ר כולל מע&quot;מ
                    </div>
                    
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="construction-area" className="text-xs">
                          שטח בנוי מתוכנן (מ&quot;ר)
                        </Label>
                        <div className="relative">
                          <LandPlot className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            id="construction-area"
                            type="number"
                            value={constructionArea}
                            onChange={e => handleConstructionAreaChange(parseFloat(e.target.value) || 0)}
                            className="pr-10"
                            placeholder="200"
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="construction-cost" className="text-xs">
                          עלות בנייה למ&quot;ר
                        </Label>
                        <div className="relative">
                          <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground font-medium">₪</span>
                          <Input
                            id="construction-cost"
                            type="number"
                            value={constructionCostPerSqm}
                            onChange={e => handleConstructionCostChange(parseFloat(e.target.value) || 0)}
                            className="pr-10"
                            placeholder="5,000"
                          />
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {fmtCurrency(constructionCostPerSqm)} למ&quot;ר
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between gap-3">
                      <label className="flex items-center space-x-2 space-x-reverse cursor-pointer">
                        <Switch
                          checked={constructionIncludesVat}
                          onCheckedChange={handleConstructionVatChange}
                        />
                        <span className="text-sm">העלות שהוזנה כוללת מע&quot;מ</span>
                      </label>
                      <div className="text-xs text-muted-foreground text-right">
                        {constructionIncludesVat
                          ? 'העלות תיקח בחשבון את הסכום שהוזן ככולל מע&quot;מ'
                          : `הסכום יחושב בהתאם למע"מ הנוכחי (${(vatRate * 100).toFixed(1)}%)`}
                      </div>
                    </div>
                    <div className="flex items-center justify-between rounded-lg border bg-muted/40 p-3">
                      <div className="flex items-center gap-2 text-sm font-medium">
                        <Hammer className="h-4 w-4 text-orange-500" />
                        <span>סה&quot;כ עלות בנייה משוערת</span>
                      </div>
                      <span className="font-semibold text-primary">{fmtCurrency(effectiveConstructionCost)}</span>
                    </div>
                  </div>
                </>
              )}
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
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-100 dark:bg-orange-900/20 rounded-lg">
                  <Receipt className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                </div>
                <div>
                  <CardTitle>עלויות נלוות</CardTitle>
                  <CardDescription>הוסף עלויות עיסקה כמו עורך דין, עמלת תיווך, יועץ משכנתא ועוד</CardDescription>
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={applyAllDefaults} size="sm" variant="outline">
                  <TrendingUp className="h-4 w-4 ml-2" />
                  ברירות מחדל
                </Button>
                <Button onClick={clearAllServices} size="sm" variant="outline">
                  <X className="h-4 w-4 ml-2" />
                  נקה הכל
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              {(Object.keys(services) as ServiceKey[]).map((key) => {
                const defaultValue = defaultValues[key]
                const isUsingDefault = 
                  services[key].percent === defaultValue.percent && 
                  services[key].amount === defaultValue.amount && 
                  services[key].includesVat === defaultValue.includesVat
                
                return (
                  <Card key={key} variant="outlined" className="p-4">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getServiceIcon(key)}
                          <span className="font-medium">{labelMap[key]}</span>
                        </div>
                        <Button 
                          onClick={() => applyDefaultValue(key)} 
                          size="sm" 
                          variant={isUsingDefault ? "default" : "outline"}
                          className="text-xs"
                        >
                          {isUsingDefault ? "ברירת מחדל" : "החל ברירת מחדל"}
                        </Button>
                      </div>
                      
                      {/* Default value hint */}
                      <div className="text-xs text-muted-foreground bg-muted/50 p-2 rounded">
                        <strong>ברירת מחדל:</strong> {
                          (defaultValue.percent ?? 0) > 0 
                            ? `${defaultValue.percent}% מהמחיר${defaultValue.includesVat ? ' (כולל מע"מ)' : ' + מע"מ'}`
                            : key === 'renovation' 
                              ? `${fmtCurrency(defaultValue.amount ?? 0)} למ"ר${defaultValue.includesVat ? ' (כולל מע"מ)' : ' + מע"מ'}`
                              : `${fmtCurrency(defaultValue.amount ?? 0)}${defaultValue.includesVat ? ' (כולל מע"מ)' : ' + מע"מ'}`
                        }
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
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Calculate Button */}
        <div className="flex justify-center mt-8">
          <Button onClick={calculate} size="lg" className="px-8">
            <Receipt className="h-5 w-5 ml-2" />
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
                      <Badge variant="outline" className="text-xs">
                        {isLand ? 'קרקע' : 'נכס בנוי'}
                      </Badge>
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
                           item.track === 'bereaved' ? 'משפחה שכולה' :
                           item.track === 'land' ? 'קרקע' : item.track}
                        </Badge>
                      </div>
                      <span className="font-semibold">{fmtCurrency(item.tax)}</span>
                    </div>
                  ))}

                  {/* Construction Costs */}
                  {isLand && (
                    <div className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Hammer className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">סה&quot;כ עלות בנייה</span>
                      </div>
                      <span className="font-semibold">{fmtCurrency(result.constructionCost)}</span>
                    </div>
                  )}

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
  broker: 'עמלת תיווך',
  mortgage: 'יועץ משכנתא',
  inspection: 'בדק בית',
  lawyer: 'עו"ד',
  appraiser: 'שמאי',
  renovation: 'שיפוץ',
  furniture: 'ריהוט',
}

const getServiceIcon = (key: string) => {
  const iconMap: Record<string, React.ReactNode> = {
    broker: <Users className="h-4 w-4 text-blue-600 dark:text-blue-400" />,
    mortgage: <PiggyBank className="h-4 w-4 text-amber-600 dark:text-amber-400" />,
    inspection: <ClipboardCheck className="h-4 w-4 text-teal-600 dark:text-teal-400" />,
    lawyer: <FileText className="h-4 w-4 text-purple-600 dark:text-purple-400" />,
    appraiser: <Scale className="h-4 w-4 text-green-600 dark:text-green-400" />,
    renovation: <Hammer className="h-4 w-4 text-orange-600 dark:text-orange-400" />,
    furniture: <Sofa className="h-4 w-4 text-pink-600 dark:text-pink-400" />,
  }
  return iconMap[key] || <Calculator className="h-4 w-4 text-muted-foreground" />
}
