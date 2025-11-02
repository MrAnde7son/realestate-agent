'use client'

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { cn, fmtCurrency } from '@/lib/utils'
import {
  pricePortfolio,
  calculateLTV,
  calculateAffordability,
  calcPrime,
  type PortfolioInput,
  type TrancheInput,
  type PortfolioResult,
  type TrackType,
  type GraceType,
  type RepaymentMethod
} from '@/lib/mortgage'
import { Loader2, Calculator, Plus, Trash2, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import { useAnalytics } from '@/hooks/useAnalytics'
import { useOptionalAuth } from '@/lib/auth-context'
interface UITranche extends TrancheInput {
  id: string
}

const createId = () => {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return Math.random().toString(36).slice(2)
}

const TRACK_OPTIONS: { value: TrackType; label: string }[] = [
  { value: 'PRIME', label: 'פריים' },
  { value: 'FIXED_UNLINKED', label: 'קבועה לא צמודה' },
  { value: 'FIXED_LINKED', label: 'קבועה צמודה למדד' },
  { value: 'VARIABLE_BOI', label: 'משתנה עוגן בנק ישראל' },
  { value: 'VARIABLE_BOND', label: 'משתנה עוגן אג״ח' }
]

const REPAYMENT_OPTIONS: { value: RepaymentMethod; label: string }[] = [
  { value: 'ANNUITY', label: 'שפיצר' },
  { value: 'EQUAL_PRINCIPAL', label: 'קרן שווה' }
]

const GRACE_OPTIONS: { value: GraceType; label: string }[] = [
  { value: 'NONE', label: 'ללא' },
  { value: 'INTEREST_ONLY', label: 'רק ריבית' },
  { value: 'FULL', label: 'דחיית תשלומים מלאה' }
]

const createDefaultTranches = (primeRate: number): UITranche[] => [
  {
    id: createId(),
    name: 'פריים (P-0.9)',
    amount: 450_000,
    termMonths: 360,
    track: 'PRIME',
    anchorAnnual: primeRate,
    marginAnnual: -0.9,
    indexation: 'NONE',
    repayment: 'ANNUITY',
    graceType: 'NONE',
    graceMonths: 0,
    feesUpfront: 1_500
  },
  {
    id: createId(),
    name: 'קבועה לא צמודה 4.7%',
    amount: 540_000,
    termMonths: 300,
    track: 'FIXED_UNLINKED',
    anchorAnnual: 4.7,
    marginAnnual: 0,
    indexation: 'NONE',
    repayment: 'ANNUITY',
    graceType: 'NONE',
    graceMonths: 0,
    feesUpfront: 1_500
  },
  {
    id: createId(),
    name: 'משתנה אג״ח +0.8% (צמוד מדד)',
    amount: 333_000,
    termMonths: 360,
    track: 'VARIABLE_BOND',
    anchorAnnual: 3.9,
    marginAnnual: 0.8,
    resetEveryMonths: 60,
    indexation: 'CPI',
    cpiAnnualAssumption: 2,
    repayment: 'ANNUITY',
    graceType: 'NONE',
    graceMonths: 0
  }
]

const stressPresets = [
  { id: 'base', label: 'בסיס', boiShock: 0, cpiShock: 0, description: 'ללא שינוי' },
  { id: 'boi_up', label: 'בנק ישראל +1%', boiShock: 1, cpiShock: 0, description: 'תרחיש עליית ריבית בנק ישראל' },
  { id: 'cpi_up', label: 'מדד המחירים +1%', boiShock: 0, cpiShock: 1, description: 'תרחיש אינפלציה גבוהה' },
  { id: 'stress', label: 'תרחיש קיצון', boiShock: 2, cpiShock: 1.5, description: 'ריבית גבוהה ואינפלציה' }
]

const DEFAULT_BOI_RATE = 4.75
const DEFAULT_PRIME_SPREAD = 1.5

export default function MortgageAnalyzePage() {
  const initialPrimeRate = calcPrime(DEFAULT_BOI_RATE, DEFAULT_PRIME_SPREAD)
  const initialTranchesRef = useRef<UITranche[] | null>(null)
  if (!initialTranchesRef.current) {
    initialTranchesRef.current = createDefaultTranches(initialPrimeRate)
  }

  const { trackCalculatorUsage, trackCalculatorCalculation } = useAnalytics()
  const auth = useOptionalAuth()
  const user = auth?.user ?? null

  const [primeRate, setPrimeRate] = useState<number>(initialPrimeRate)
  const [lastUpdated, setLastUpdated] = useState<string>('')
  const [loadingBoiRate, setLoadingBoiRate] = useState<boolean>(true)
  const [calculating, setCalculating] = useState<boolean>(false)
  const [selectedStress, setSelectedStress] = useState<string>('base')
  const [requiredEquity, setRequiredEquity] = useState<number | null>(null)
  const [isClient, setIsClient] = useState(false)
  const [userEquity, setUserEquity] = useState<number>(0)

  const [propertyValue, setPropertyValue] = useState<number>(3_500_000)
  const [monthlyIncome, setMonthlyIncome] = useState<number>(65_000)

  const [envConfig, setEnvConfig] = useState<Omit<PortfolioInput, 'tranches'>>({
    boiAnnual: DEFAULT_BOI_RATE,
    primeSpread: DEFAULT_PRIME_SPREAD,
    boiShock: 0,
    bondShock: 0,
    cpiShock: 0,
    monthlyIncome
  })

  const [tranches, setTranches] = useState<UITranche[]>(initialTranchesRef.current ?? [])
  const [expandedTranches, setExpandedTranches] = useState<Record<string, boolean>>(() => {
    const initial = initialTranchesRef.current ?? []
    return initial.reduce((acc, tranche) => {
      acc[tranche.id] = true
      return acc
    }, {} as Record<string, boolean>)
  })
  const [highlightedTrancheId, setHighlightedTrancheId] = useState<string | null>(null)
  const trancheRefs = useRef<Record<string, HTMLDivElement | null>>({})
  const scrollTimeoutRef = useRef<number | null>(null)

  const totalLoanAmount = useMemo(
    () => tranches.reduce((sum, tranche) => sum + tranche.amount, 0),
    [tranches]
  )

  const portfolioInput: PortfolioInput = useMemo(
    () => ({
      ...envConfig,
      monthlyIncome,
      tranches: tranches.map(({ id, ...rest }) => rest)
    }),
    [envConfig, monthlyIncome, tranches]
  )

  const portfolioResult: PortfolioResult = useMemo(
    () => pricePortfolio(portfolioInput),
    [portfolioInput]
  )

  const ltv = useMemo(
    () => calculateLTV(totalLoanAmount, propertyValue),
    [totalLoanAmount, propertyValue]
  )

  const affordability = useMemo(
    () => calculateAffordability(monthlyIncome, portfolioResult.blendedFirstPayment),
    [monthlyIncome, portfolioResult.blendedFirstPayment]
  )

  const registerTrancheRef = useCallback(
    (id: string) => (element: HTMLDivElement | null) => {
      trancheRefs.current[id] = element
    },
    []
  )

  const rebalanceTranches = useCallback((targetLoanAmount: number) => {
    setTranches(prev => {
      const currentTotal = prev.reduce((sum, tranche) => sum + tranche.amount, 0)
      if (prev.length === 0) return prev
      if (targetLoanAmount <= 0) {
        return prev.map(tranche => ({ ...tranche, amount: 0 }))
      }
      if (Math.abs(currentTotal - targetLoanAmount) < 1) {
        return prev
      }
      if (currentTotal === 0) {
        const equalAmount = targetLoanAmount / prev.length
        return prev.map(tranche => ({ ...tranche, amount: equalAmount }))
      }
      const factor = targetLoanAmount / currentTotal
      return prev.map(tranche => ({ ...tranche, amount: tranche.amount * factor }))
    })
  }, [])

  useEffect(() => {
    if (user?.role === 'private') {
      const equityValue = typeof user.equity === 'number' ? user.equity : 0
      setUserEquity(equityValue)
    }
  }, [user])

  useEffect(() => {
    setIsClient(true)
    fetchBOIRateFromApi()
    trackCalculatorUsage('mortgage', 'page_view')
  }, [trackCalculatorUsage])

  useEffect(() => {
    if (!isClient) return
    const urlParams = new URLSearchParams(window.location.search)
    const propertyValueParam = urlParams.get('propertyValue')
    const totalExpenses = urlParams.get('totalExpenses')

    if (propertyValueParam || totalExpenses) {
      trackCalculatorUsage('mortgage', 'prefilled_from_expenses', {
        property_value: propertyValueParam,
        total_expenses: totalExpenses
      })

      if (propertyValueParam) {
        const totalCost = Number(propertyValueParam)
        if (!Number.isNaN(totalCost)) {
          setPropertyValue(totalCost)
        }
      }

      if (totalExpenses) {
        const expensesValue = Number(totalExpenses)
        if (!Number.isNaN(expensesValue)) {
          setRequiredEquity(expensesValue)
        }
      }
    }
  }, [isClient, trackCalculatorUsage])

  useEffect(() => {
    const targetLoan = Math.max(0, propertyValue - userEquity)
    rebalanceTranches(targetLoan)
  }, [propertyValue, userEquity, rebalanceTranches])

  useEffect(() => {
    setEnvConfig(prev => ({ ...prev, monthlyIncome }))
  }, [monthlyIncome])

  useEffect(() => {
    const newPrime = calcPrime(envConfig.boiAnnual, envConfig.primeSpread)
    setPrimeRate(newPrime)
    setTranches(prev => {
      let changed = false
      const next = prev.map(tranche => {
        if (tranche.track === 'PRIME' && Math.abs(tranche.anchorAnnual - newPrime) > 0.001) {
          changed = true
          return { ...tranche, anchorAnnual: newPrime }
        }
        return tranche
      })
      return changed ? next : prev
    })
  }, [envConfig.boiAnnual, envConfig.primeSpread])

  useEffect(() => {
    if (highlightedTrancheId === null) return
    if (typeof window === 'undefined') return
    const timeout = window.setTimeout(() => setHighlightedTrancheId(null), 2000)
    return () => window.clearTimeout(timeout)
  }, [highlightedTrancheId])

  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current !== null && typeof window !== 'undefined') {
        window.clearTimeout(scrollTimeoutRef.current)
      }
    }
  }, [])

  const fetchBOIRateFromApi = async () => {
    setLoadingBoiRate(true)
    try {
      const response = await fetch('/api/boi-rate')
      const data = await response.json()
      if (data.success) {
        const baseRate = Number(data.data.baseRate)
        if (Number.isFinite(baseRate)) {
          setEnvConfig(prev => ({ ...prev, boiAnnual: baseRate }))
        }
        if (data.data.lastUpdated) {
          setLastUpdated(data.data.lastUpdated)
        }
      }
    } catch (error) {
      console.error('שגיאה בשליפת ריבית בנק ישראל:', error)
    } finally {
      setLoadingBoiRate(false)
    }
  }

  const handleAnalyzePortfolio = async () => {
    setCalculating(true)

    trackCalculatorUsage('mortgage', 'calculation_start', {
      property_value: propertyValue,
      monthly_income: monthlyIncome,
      boi_rate: envConfig.boiAnnual,
      stress: { boiShock: envConfig.boiShock, cpiShock: envConfig.cpiShock },
      tranches: tranches.map(({ id, ...tranche }) => tranche)
    })

    await new Promise(resolve => setTimeout(resolve, 400))

    const latestResult = pricePortfolio({
      ...envConfig,
      monthlyIncome,
      tranches: tranches.map(({ id, ...tranche }) => tranche)
    })

    trackCalculatorCalculation(
      'mortgage',
      {
        propertyValue,
        monthlyIncome,
        boiRate: envConfig.boiAnnual,
        stress: { boiShock: envConfig.boiShock, cpiShock: envConfig.cpiShock },
        trancheCount: tranches.length
      },
      {
        blendedFirstPayment: latestResult.blendedFirstPayment,
        blendedMaxPayment: latestResult.blendedMaxPayment,
        totalPaid: latestResult.totals.paid,
        totalInterest: latestResult.totals.interest,
        totalIndexation: latestResult.totals.indexation,
        affordability: latestResult.affordability
      }
    )

    setCalculating(false)
  }

  const handleStressPreset = (presetId: string) => {
    const preset = stressPresets.find(option => option.id === presetId)
    if (!preset) return
    setSelectedStress(presetId)
    setEnvConfig(prev => ({
      ...prev,
      boiShock: preset.boiShock,
      cpiShock: preset.cpiShock
    }))
  }

  const updateTranche = <K extends keyof TrancheInput>(id: string, field: K, value: TrancheInput[K]) => {
    setTranches(prev => prev.map(tranche => (tranche.id === id ? { ...tranche, [field]: value } : tranche)))
  }

  const addTranche = () => {
    const id = createId()
    const newTranche: UITranche = {
      id,
      name: 'מסלול חדש',
      amount: Math.max(0, propertyValue - userEquity - totalLoanAmount),
      termMonths: 360,
      track: 'FIXED_UNLINKED',
      anchorAnnual: 4.5,
      marginAnnual: 0,
      indexation: 'NONE',
      repayment: 'ANNUITY',
      graceType: 'NONE',
      graceMonths: 0,
      feesUpfront: 0
    }
    setTranches(prev => [...prev, newTranche])
    setExpandedTranches(prev => ({ ...prev, [id]: true }))

    if (scrollTimeoutRef.current !== null && typeof window !== 'undefined') {
      window.clearTimeout(scrollTimeoutRef.current)
    }

    if (typeof window !== 'undefined') {
      scrollTimeoutRef.current = window.setTimeout(() => {
        const node = trancheRefs.current[id]
        if (node) {
          node.scrollIntoView?.({ behavior: 'smooth', block: 'start' })
          setHighlightedTrancheId(id)
        }
      }, 150)
    }
  }

  const removeTranche = (id: string) => {
    setTranches(prev => prev.filter(tranche => tranche.id !== id))
    setExpandedTranches(prev => {
      const { [id]: _removed, ...rest } = prev
      return rest
    })
    delete trancheRefs.current[id]
  }

  const toggleTrancheExpanded = (id: string) => {
    setExpandedTranches(prev => ({ ...prev, [id]: !(prev[id] ?? true) }))
  }

  const monthlyAtYear = (years: number) => portfolioResult.blendedMonthlyAt(years * 12)

  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader heading="מחשבון משכנתא" text="תכנון תיק משכנתא רב-מסלולי עם תרחישי לחץ" />

        <div className="grid gap-6 xl:grid-cols-[2fr,1fr]">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>נתוני בסיס</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">שווי נכס</label>
                    <Input
                      type="number"
                      value={propertyValue}
                      onChange={event => setPropertyValue(Number(event.target.value) || 0)}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">הון עצמי</label>
                    <Input
                      type="number"
                      value={userEquity}
                      onChange={event => setUserEquity(Number(event.target.value) || 0)}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">הכנסה חודשית</label>
                    <Input
                      type="number"
                      value={monthlyIncome}
                      onChange={event => setMonthlyIncome(Number(event.target.value) || 0)}
                    />
                  </div>
                </div>
                <Separator />
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">ריבית בנק ישראל</label>
                    <div className="flex items-center gap-2">
                      {loadingBoiRate ? (
                        <Skeleton className="h-10 w-full" />
                      ) : (
                        <Input
                          type="number"
                          step="0.01"
                          value={envConfig.boiAnnual}
                          onChange={event => setEnvConfig(prev => ({ ...prev, boiAnnual: Number(event.target.value) || 0 }))}
                        />
                      )}
                      <Button variant="outline" size="icon" onClick={fetchBOIRateFromApi} aria-label="רענון ריבית בנק ישראל">
                        <Loader2 className={`h-4 w-4 ${loadingBoiRate ? 'animate-spin' : ''}`} />
                      </Button>
                    </div>
                    {lastUpdated && (
                      <p className="mt-1 text-xs text-muted-foreground">עדכון אחרון: {new Date(lastUpdated).toLocaleDateString('he-IL')}</p>
                    )}
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">מרווח פריים</label>
                    <Input
                      type="number"
                      step="0.01"
                      value={envConfig.primeSpread}
                      onChange={event => setEnvConfig(prev => ({ ...prev, primeSpread: Number(event.target.value) || 0 }))}
                    />
                    <p className="mt-1 text-xs text-muted-foreground">פריים נוכחי: {primeRate.toFixed(2)}%</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">תוספת לעוגן אג״ח</label>
                    <Input
                      type="number"
                      step="0.1"
                      value={envConfig.bondShock ?? 0}
                      onChange={event => setEnvConfig(prev => ({ ...prev, bondShock: Number(event.target.value) || 0 }))}
                    />
                  </div>
                </div>
                <Separator />
                <div>
                  <label className="text-sm font-medium text-muted-foreground">תרחישי לחץ</label>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {stressPresets.map(preset => (
                      <Button
                        key={preset.id}
                        type="button"
                        size="sm"
                        variant={selectedStress === preset.id ? 'default' : 'outline'}
                        onClick={() => handleStressPreset(preset.id)}
                      >
                        {preset.label}
                      </Button>
                    ))}
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">
                    שינוי ריבית בנק ישראל: {(envConfig.boiShock ?? 0).toFixed(2)}% · שינוי מדד: {(envConfig.cpiShock ?? 0).toFixed(2)}%
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>מסלולים</CardTitle>
                <Button type="button" onClick={addTranche} variant="outline" size="sm" className="flex items-center gap-2">
                  <Plus className="h-4 w-4" />
                  <span>הוסף מסלול</span>
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                {tranches.map(tranche => {
                  const isExpanded = expandedTranches[tranche.id] ?? true
                  const trackLabel = TRACK_OPTIONS.find(option => option.value === tranche.track)?.label ?? ''
                  return (
                    <div
                      key={tranche.id}
                      ref={registerTrancheRef(tranche.id)}
                      data-testid="tranche-editor"
                      className={cn(
                        'rounded-lg border bg-card p-4 transition-shadow',
                        highlightedTrancheId === tranche.id && 'ring-2 ring-primary/50'
                      )}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div className="flex flex-1 flex-wrap items-center gap-3">
                          <Button
                            type="button"
                            size="icon"
                            variant="ghost"
                            onClick={() => toggleTrancheExpanded(tranche.id)}
                            aria-label={isExpanded ? 'צמצום מסלול' : 'הרחבת מסלול'}
                          >
                            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                            <span className="sr-only">{isExpanded ? 'צמצום מסלול' : 'הרחבת מסלול'}</span>
                          </Button>
                          <Input
                            className="min-w-[180px] flex-1"
                            value={tranche.name}
                            onChange={event => updateTranche(tranche.id, 'name', event.target.value)}
                          />
                          <Badge variant="neutral">{trackLabel}</Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          {tranches.length > 1 && (
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() => removeTranche(tranche.id)}
                              aria-label="מחיקת מסלול"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                      {isExpanded && (
                        <div className="mt-4 space-y-4">
                          <div className="grid gap-4 md:grid-cols-3">
                            <div>
                              <label className="text-xs font-medium text-muted-foreground">מסלול</label>
                              <Select
                                value={tranche.track}
                                onValueChange={value => updateTranche(tranche.id, 'track', value as TrackType)}
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {TRACK_OPTIONS.map(option => (
                                    <SelectItem key={option.value} value={option.value}>
                                      {option.label}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                            <div>
                              <label className="text-xs font-medium text-muted-foreground">סכום</label>
                              <Input
                                type="number"
                                value={Math.round(tranche.amount)}
                                onChange={event => updateTranche(tranche.id, 'amount', Number(event.target.value) || 0)}
                              />
                            </div>
                            <div>
                              <label className="text-xs font-medium text-muted-foreground">תקופה (חודשים)</label>
                              <Input
                                type="number"
                                value={tranche.termMonths}
                                onChange={event => updateTranche(tranche.id, 'termMonths', Number(event.target.value) || 0)}
                              />
                            </div>
                          </div>
                          <div className="grid gap-4 md:grid-cols-3">
                            <div>
                              <label className="text-xs font-medium text-muted-foreground">עוגן נוכחי (%)</label>
                              <Input
                                type="number"
                                step="0.01"
                                value={tranche.anchorAnnual}
                                onChange={event => updateTranche(tranche.id, 'anchorAnnual', Number(event.target.value) || 0)}
                              />
                            </div>
                            <div>
                              <label className="text-xs font-medium text-muted-foreground">מרווח (%)</label>
                              <Input
                                type="number"
                                step="0.01"
                                value={tranche.marginAnnual}
                                onChange={event => updateTranche(tranche.id, 'marginAnnual', Number(event.target.value) || 0)}
                              />
                            </div>
                            <div>
                              <label className="text-xs font-medium text-muted-foreground">הצמדה</label>
                              <Select
                                value={tranche.indexation ?? 'NONE'}
                                onValueChange={value => updateTranche(tranche.id, 'indexation', value as 'CPI' | 'NONE')}
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="NONE">ללא</SelectItem>
                                  <SelectItem value="CPI">מדד</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                          </div>
                          <div className="grid gap-4 md:grid-cols-3">
                            <div>
                              <label className="text-xs font-medium text-muted-foreground">הנחת מדד שנתית (%)</label>
                              <Input
                                type="number"
                                step="0.1"
                                value={tranche.cpiAnnualAssumption ?? 0}
                                onChange={event => updateTranche(tranche.id, 'cpiAnnualAssumption', Number(event.target.value) || 0)}
                              />
                            </div>
                            <div>
                              <label className="text-xs font-medium text-muted-foreground">תדירות עדכון (חודשים)</label>
                              <Input
                                type="number"
                                value={tranche.resetEveryMonths ?? 0}
                                onChange={event => updateTranche(tranche.id, 'resetEveryMonths', Number(event.target.value) || undefined)}
                              />
                            </div>
                            <div>
                              <label className="text-xs font-medium text-muted-foreground">שיטת החזר</label>
                              <Select
                                value={tranche.repayment}
                                onValueChange={value => updateTranche(tranche.id, 'repayment', value as RepaymentMethod)}
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {REPAYMENT_OPTIONS.map(option => (
                                    <SelectItem key={option.value} value={option.value}>
                                      {option.label}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                          </div>
                          <div className="grid gap-4 md:grid-cols-3">
                            <div>
                              <label className="text-xs font-medium text-muted-foreground">חודשי גרייס</label>
                              <Input
                                type="number"
                                value={tranche.graceMonths ?? 0}
                                onChange={event => updateTranche(tranche.id, 'graceMonths', Number(event.target.value) || 0)}
                              />
                            </div>
                            <div>
                              <label className="text-xs font-medium text-muted-foreground">סוג גרייס</label>
                              <Select
                                value={tranche.graceType ?? 'NONE'}
                                onValueChange={value => updateTranche(tranche.id, 'graceType', value as GraceType)}
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {GRACE_OPTIONS.map(option => (
                                    <SelectItem key={option.value} value={option.value}>
                                      {option.label}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                            <div>
                              <label className="text-xs font-medium text-muted-foreground">עמלות פתיחת תיק</label>
                              <Input
                                type="number"
                                value={tranche.feesUpfront ?? 0}
                                onChange={event => updateTranche(tranche.id, 'feesUpfront', Number(event.target.value) || 0)}
                              />
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
                {tranches.length === 0 && (
                  <div className="flex items-center gap-2 rounded-md border border-dashed p-4 text-muted-foreground">
                    <AlertTriangle className="h-4 w-4" />
                    <span>לא נוספו מסלולים. הוסף לפחות מסלול אחד כדי להפיק חישוב.</span>
                  </div>
                )}
              </CardContent>
            </Card>

            <div className="flex justify-end">
              <Button
                onClick={handleAnalyzePortfolio}
                disabled={calculating || tranches.length === 0}
                className="flex items-center gap-2"
              >
                {calculating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Calculator className="h-4 w-4" />}
                <span>חשב תיק</span>
              </Button>
            </div>

            {requiredEquity !== null && (
              <Card>
                <CardHeader>
                  <CardTitle>הון עצמי מינימלי לפי הוצאות עסקה</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    סך הוצאות נוסף שנלקח מהחשבונית: {fmtCurrency(requiredEquity)}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>סיכום תיק</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">תשלום ראשון</span>
                    <span className="text-lg font-semibold">{fmtCurrency(portfolioResult.blendedFirstPayment)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">תשלום מקסימלי</span>
                    <span className="text-lg font-semibold">{fmtCurrency(portfolioResult.blendedMaxPayment)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">סה״כ הלוואה</span>
                    <span className="text-lg font-semibold">{fmtCurrency(totalLoanAmount)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">סה״כ תשלומים (כולל עמלות)</span>
                    <span className="text-lg font-semibold">{fmtCurrency(portfolioResult.totals.paid)}</span>
                  </div>
                </div>
                <Separator />
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span>ריבית</span>
                    <span>{fmtCurrency(portfolioResult.totals.interest)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>הצמדה</span>
                    <span>{fmtCurrency(portfolioResult.totals.indexation)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>עמלות</span>
                    <span>{fmtCurrency(portfolioResult.totals.fees)}</span>
                  </div>
                </div>
                <Separator />
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span>יחס החזר להכנסה</span>
                    <Badge variant={affordability.isAffordable ? 'success' : 'destructive'}>
                      {affordability.ratio.toFixed(1)}%
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>יחס מימון (LTV)</span>
                    <Badge variant={ltv <= 60 ? 'success' : ltv <= 75 ? 'neutral' : 'destructive'}>
                      {ltv.toFixed(1)}%
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>תשלומים עתידיים</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span>שנה 1</span>
                  <span>{fmtCurrency(monthlyAtYear(1))}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>שנה 5</span>
                  <span>{fmtCurrency(monthlyAtYear(5))}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>שנה 10</span>
                  <span>{fmtCurrency(monthlyAtYear(10))}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>פירוט מסלולים</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                {portfolioResult.tranches.map((tranche, index) => (
                  <div key={`${tranche.input.name}-${index}`} className="rounded-md border p-3">
                    <div className="flex items-center justify-between">
                      <div className="font-medium">{tranche.input.name}</div>
                      <Badge variant="neutral">{TRACK_OPTIONS.find(option => option.value === tranche.input.track)?.label}</Badge>
                    </div>
                    <div className="mt-2 grid gap-2">
                      <div className="flex items-center justify-between">
                        <span>תשלום ראשון</span>
                        <span>{fmtCurrency(tranche.firstPayment)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>תשלום מקסימלי</span>
                        <span>{fmtCurrency(tranche.maxPayment)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>סה״כ ריבית</span>
                        <span>{fmtCurrency(tranche.totalInterest)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>סה״כ הצמדה</span>
                        <span>{fmtCurrency(tranche.totalIndexation)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>תשואה שנתית משוערת (APR)</span>
                        <span>{tranche.aprApprox.toFixed(2)}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}
