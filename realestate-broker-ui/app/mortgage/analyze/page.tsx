'use client'

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
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
import { Loader2, Calculator, Plus, Trash2, AlertTriangle, ChevronDown, ChevronUp, Settings, ChevronLeft } from 'lucide-react'
import { useAnalytics } from '@/hooks/useAnalytics'
import { useOptionalAuth } from '@/lib/auth-context'
import { StickyActionBar } from '@/components/layout/sticky-action-bar'
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

type ScenarioType = 'even' | 'conservative' | 'aggressive'

interface MortgageScenario {
  id: ScenarioType
  name: string
  description: string
  tranches: UITranche[]
}

const createMortgageScenarios = (primeRate: number, totalLoanAmount: number): MortgageScenario[] => {
  // Scenario 1: Evenly distributed (חלוקה שווה)
  const evenAmount = totalLoanAmount / 3
  const evenScenario: MortgageScenario = {
    id: 'even',
    name: 'חלוקה שווה',
    description: 'חלוקה שווה בין שלושת המסלולים',
    tranches: [
      {
        id: createId(),
        name: 'פריים (P-0.9)',
        amount: Math.round(evenAmount),
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
        amount: Math.round(evenAmount),
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
        amount: Math.round(totalLoanAmount - evenAmount * 2),
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
  }

  // Scenario 2: Conservative (שמרני) - More fixed, less variable
  const conservativeScenario: MortgageScenario = {
    id: 'conservative',
    name: 'שמרני',
    description: 'דגש על מסלולים קבועים ויציבים',
    tranches: [
      {
        id: createId(),
        name: 'פריים (P-0.9)',
        amount: Math.round(totalLoanAmount * 0.2),
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
        amount: Math.round(totalLoanAmount * 0.5),
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
        amount: Math.round(totalLoanAmount * 0.3),
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
  }

  // Scenario 3: Aggressive/Prime-focused (אגרסיבי) - More prime and variable
  const aggressiveScenario: MortgageScenario = {
    id: 'aggressive',
    name: 'אגרסיבי',
    description: 'דגש על פריים ומסלולים משתנים',
    tranches: [
      {
        id: createId(),
        name: 'פריים (P-0.9)',
        amount: Math.round(totalLoanAmount * 0.5),
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
        amount: Math.round(totalLoanAmount * 0.2),
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
        amount: Math.round(totalLoanAmount * 0.3),
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
  }

  return [evenScenario, conservativeScenario, aggressiveScenario]
}

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

const parseNumberParam = (value: string | null): number | null => {
  if (value === null) return null
  const trimmed = value.trim()
  if (trimmed === '') return null
  const parsed = Number(trimmed)
  return Number.isFinite(parsed) ? parsed : null
}

export default function MortgageAnalyzePage() {
  const router = useRouter()
  const searchParams = useSearchParams()
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
  const [selectedStress, setSelectedStress] = useState<string>(() => {
    const param = searchParams.get('stress')
    return param || 'base'
  })
  const [requiredEquity, setRequiredEquity] = useState<number | null>(null)
  const [isClient, setIsClient] = useState(false)
  const [userEquity, setUserEquity] = useState<number | null>(() => parseNumberParam(searchParams.get('userEquity')))

  const [propertyValue, setPropertyValue] = useState<number | null>(() => parseNumberParam(searchParams.get('propertyValue')))
  const [monthlyIncome, setMonthlyIncome] = useState<number | null>(() => parseNumberParam(searchParams.get('monthlyIncome')))

  const [envConfig, setEnvConfig] = useState<Omit<PortfolioInput, 'tranches'>>(() => {
    const boiAnnualParam = searchParams.get('boiAnnual')
    const primeSpreadParam = searchParams.get('primeSpread')
    const boiShockParam = searchParams.get('boiShock')
    const bondShockParam = searchParams.get('bondShock')
    const cpiShockParam = searchParams.get('cpiShock')
    const monthlyIncomeParam = parseNumberParam(searchParams.get('monthlyIncome'))
    
    return {
      boiAnnual: boiAnnualParam ? Number(boiAnnualParam) || DEFAULT_BOI_RATE : DEFAULT_BOI_RATE,
      primeSpread: primeSpreadParam ? Number(primeSpreadParam) || DEFAULT_PRIME_SPREAD : DEFAULT_PRIME_SPREAD,
      boiShock: boiShockParam ? Number(boiShockParam) || 0 : 0,
      bondShock: bondShockParam ? Number(bondShockParam) || 0 : 0,
      cpiShock: cpiShockParam ? Number(cpiShockParam) || 0 : 0,
      monthlyIncome: monthlyIncomeParam ?? 0
    }
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
  const [selectedScenarioId, setSelectedScenarioId] = useState<ScenarioType | null>(() => {
    const param = searchParams.get('scenario')
    return (param && (param === 'even' || param === 'conservative' || param === 'aggressive')) ? param as ScenarioType : null
  })
  const [showAdvancedSettings, setShowAdvancedSettings] = useState<boolean>(false)
  const hasClearedTranchesRef = useRef(false)
  const hasInitializedFromProfileRef = useRef({ equity: false, monthlyIncome: false, userId: null as string | number | null })
  
  // Default to compare mode if we have loan amount (scenarios will be generated), otherwise edit mode
  const getInitialViewMode = (): 'compare' | 'edit' => {
    const targetLoan = Math.max(0, (propertyValue ?? 0) - (userEquity ?? 0))
    return targetLoan > 0 ? 'compare' : 'edit'
  }
  const [viewMode, setViewMode] = useState<'compare' | 'edit'>(() => {
    // Check initial values - if we have property value without equity, start in compare mode
    const targetLoan = Math.max(0, (propertyValue ?? 0) - (userEquity ?? 0))
    return targetLoan > 0 ? 'compare' : 'edit'
  })

  const numericPropertyValue = propertyValue ?? 0
  const numericUserEquity = userEquity ?? 0
  const numericMonthlyIncome = monthlyIncome ?? 0
  const isMissingBasicInputs =
    propertyValue === null || propertyValue <= 0 ||
    monthlyIncome === null || monthlyIncome <= 0 ||
    userEquity === null
  const isCalculateDisabled = calculating || tranches.length === 0 || isMissingBasicInputs

  const trancheRefs = useRef<Record<string, HTMLDivElement | null>>({})
  const scrollTimeoutRef = useRef<number | null>(null)

  const totalLoanAmount = useMemo(
    () => tranches.reduce((sum, tranche) => sum + tranche.amount, 0),
    [tranches]
  )

  const scenarios = useMemo(() => {
    const targetLoan = Math.max(0, numericPropertyValue - numericUserEquity)
    if (targetLoan <= 0) return []
    return createMortgageScenarios(primeRate, targetLoan)
  }, [numericPropertyValue, numericUserEquity, primeRate])

  const scenarioResults = useMemo(() => {
    return scenarios.map(scenario => {
      const input: PortfolioInput = {
        ...envConfig,
        monthlyIncome: numericMonthlyIncome,
        tranches: scenario.tranches.map(({ id, ...rest }) => rest)
      }
      return {
        scenario,
        result: pricePortfolio(input)
      }
    })
  }, [scenarios, envConfig, numericMonthlyIncome])

  const portfolioInput: PortfolioInput = useMemo(
    () => ({
      ...envConfig,
      monthlyIncome: numericMonthlyIncome,
      tranches: tranches.map(({ id, ...rest }) => rest)
    }),
    [envConfig, numericMonthlyIncome, tranches]
  )

  const portfolioResult: PortfolioResult = useMemo(
    () => pricePortfolio(portfolioInput),
    [portfolioInput]
  )

  const ltv = useMemo(
    () => calculateLTV(totalLoanAmount, numericPropertyValue),
    [totalLoanAmount, numericPropertyValue]
  )

  const affordability = useMemo(
    () => calculateAffordability(numericMonthlyIncome, portfolioResult.blendedFirstPayment),
    [numericMonthlyIncome, portfolioResult.blendedFirstPayment]
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
        const allZero = prev.every(tranche => tranche.amount === 0)
        return allZero ? prev : prev.map(tranche => ({ ...tranche, amount: 0 }))
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

  // Fill equity from profile if available and not already set
  useEffect(() => {
    // Reset initialization flags if user changed
    const currentUserId = user?.id ?? null
    if (hasInitializedFromProfileRef.current.userId !== currentUserId) {
      hasInitializedFromProfileRef.current = { equity: false, monthlyIncome: false, userId: currentUserId }
    }
    
    // Only initialize if not already done and user has equity value
    if (hasInitializedFromProfileRef.current.equity) return
    
    // Fill from profile if field is null and profile has a value
    if (userEquity === null && user?.equity !== undefined && user.equity !== null) {
      const equityValue = typeof user.equity === 'number' ? user.equity : Number(user.equity)
      if (Number.isFinite(equityValue) && equityValue > 0) {
        setUserEquity(equityValue)
        hasInitializedFromProfileRef.current.equity = true
      }
    }
  }, [user, userEquity])

  // Fill monthly income from profile if available and not already set
  useEffect(() => {
    // Reset initialization flags if user changed
    const currentUserId = user?.id ?? null
    if (hasInitializedFromProfileRef.current.userId !== currentUserId) {
      hasInitializedFromProfileRef.current = { equity: false, monthlyIncome: false, userId: currentUserId }
    }
    
    // Only initialize if not already done and user has monthly income value
    if (hasInitializedFromProfileRef.current.monthlyIncome) return
    
    // Fill from profile if field is null and profile has a value
    if (monthlyIncome === null && user?.monthly_income !== undefined && user.monthly_income !== null) {
      const incomeValue = typeof user.monthly_income === 'number' ? user.monthly_income : Number(user.monthly_income)
      if (Number.isFinite(incomeValue) && incomeValue > 0) {
        setMonthlyIncome(incomeValue)
        hasInitializedFromProfileRef.current.monthlyIncome = true
      }
    }
  }, [monthlyIncome, user])

  useEffect(() => {
    setIsClient(true)
    fetchBOIRateFromApi()
    trackCalculatorUsage('mortgage', 'page_view')
  }, [trackCalculatorUsage])

  // Read URL parameters on initial load
  useEffect(() => {
    if (!isClient) return
    
    // Handle prefilled parameters from other pages
    const totalExpenses = searchParams.get('totalExpenses')
    if (totalExpenses) {
      const expensesValue = Number(totalExpenses)
      if (!Number.isNaN(expensesValue)) {
        setRequiredEquity(expensesValue)
        trackCalculatorUsage('mortgage', 'prefilled_from_expenses', {
          total_expenses: totalExpenses
        })
      }
    }
  }, [isClient, trackCalculatorUsage, searchParams])

  // Sync state to URL parameters
  useEffect(() => {
    if (!isClient) return
    
    const params = new URLSearchParams()
    
    // Update or remove propertyValue
    if (propertyValue !== null) {
      params.set('propertyValue', propertyValue.toString())
    }
    
    // Update or remove userEquity
    if (userEquity !== null) {
      params.set('userEquity', userEquity.toString())
    }
    
    // Update or remove monthlyIncome
    if (monthlyIncome !== null) {
      params.set('monthlyIncome', monthlyIncome.toString())
    }
    
    // Update or remove boiAnnual
    if (envConfig.boiAnnual && envConfig.boiAnnual !== DEFAULT_BOI_RATE) {
      params.set('boiAnnual', envConfig.boiAnnual.toString())
    }
    
    // Update or remove primeSpread
    if (envConfig.primeSpread && envConfig.primeSpread !== DEFAULT_PRIME_SPREAD) {
      params.set('primeSpread', envConfig.primeSpread.toString())
    }
    
    // Update or remove boiShock
    if (envConfig.boiShock && envConfig.boiShock !== 0) {
      params.set('boiShock', envConfig.boiShock.toString())
    }
    
    // Update or remove bondShock
    if (envConfig.bondShock && envConfig.bondShock !== 0) {
      params.set('bondShock', envConfig.bondShock.toString())
    }
    
    // Update or remove cpiShock
    if (envConfig.cpiShock && envConfig.cpiShock !== 0) {
      params.set('cpiShock', envConfig.cpiShock.toString())
    }
    
    // Update or remove stress
    if (selectedStress && selectedStress !== 'base') {
      params.set('stress', selectedStress)
    }
    
    // Update or remove scenario
    if (selectedScenarioId) {
      params.set('scenario', selectedScenarioId)
    }
    
    // Preserve other params (like totalExpenses) from current URL
    if (typeof window !== 'undefined') {
      const currentParams = new URLSearchParams(window.location.search)
      currentParams.forEach((value, key) => {
        if (!params.has(key) && key !== 'propertyValue' && key !== 'userEquity' && 
            key !== 'monthlyIncome' && key !== 'boiAnnual' && key !== 'primeSpread' &&
            key !== 'boiShock' && key !== 'bondShock' && key !== 'cpiShock' &&
            key !== 'stress' && key !== 'scenario') {
          params.set(key, value)
        }
      })
    }
    
    // Update URL without causing a navigation
    const newQueryString = params.toString()
    const currentQueryString = typeof window !== 'undefined' ? window.location.search.slice(1) : '' // Remove leading '?'
    
    if (newQueryString !== currentQueryString) {
      const newUrl = typeof window !== 'undefined' 
        ? `${window.location.pathname}${newQueryString ? `?${newQueryString}` : ''}`
        : ''
      if (newUrl) {
        router.replace(newUrl, { scroll: false })
      }
    }
  }, [
    isClient,
    propertyValue,
    userEquity,
    monthlyIncome,
    envConfig.boiAnnual,
    envConfig.primeSpread,
    envConfig.boiShock,
    envConfig.bondShock,
    envConfig.cpiShock,
    selectedStress,
    selectedScenarioId,
    router
  ])

  // Sync state from URL parameters when URL changes externally (e.g., shared links, browser navigation)
  useEffect(() => {
    if (!isClient) return
    
    const urlPropertyValue = searchParams.get('propertyValue')
    const urlUserEquity = searchParams.get('userEquity')
    const urlMonthlyIncome = searchParams.get('monthlyIncome')
    const urlBoiAnnual = searchParams.get('boiAnnual')
    const urlPrimeSpread = searchParams.get('primeSpread')
    const urlBoiShock = searchParams.get('boiShock')
    const urlBondShock = searchParams.get('bondShock')
    const urlCpiShock = searchParams.get('cpiShock')
    const urlStress = searchParams.get('stress')
    const urlScenario = searchParams.get('scenario')
    
    // Update propertyValue if URL param differs from state
    if (urlPropertyValue !== null) {
      const parsedPropertyValue = parseNumberParam(urlPropertyValue)
      if (parsedPropertyValue !== propertyValue) {
        setPropertyValue(parsedPropertyValue)
      }
    }
    
    // Update userEquity if URL param differs from state
    if (urlUserEquity !== null) {
      const parsedUserEquity = parseNumberParam(urlUserEquity)
      if (parsedUserEquity !== userEquity) {
        setUserEquity(parsedUserEquity)
      }
    }
    
    // Update monthlyIncome if URL param differs from state
    if (urlMonthlyIncome !== null) {
      const parsedMonthlyIncome = parseNumberParam(urlMonthlyIncome)
      if (parsedMonthlyIncome !== monthlyIncome) {
        setMonthlyIncome(parsedMonthlyIncome)
      }
    }
    
    // Update envConfig if URL params differ from state
    if (urlBoiAnnual) {
      const urlValue = Number(urlBoiAnnual)
      if (!Number.isNaN(urlValue) && urlValue !== envConfig.boiAnnual) {
        setEnvConfig(prev => ({ ...prev, boiAnnual: urlValue }))
      }
    }
    
    if (urlPrimeSpread) {
      const urlValue = Number(urlPrimeSpread)
      if (!Number.isNaN(urlValue) && urlValue !== envConfig.primeSpread) {
        setEnvConfig(prev => ({ ...prev, primeSpread: urlValue }))
      }
    }
    
    if (urlBoiShock !== null) {
      const urlValue = Number(urlBoiShock)
      if (!Number.isNaN(urlValue) && urlValue !== envConfig.boiShock) {
        setEnvConfig(prev => ({ ...prev, boiShock: urlValue }))
      }
    }
    
    if (urlBondShock !== null) {
      const urlValue = Number(urlBondShock)
      if (!Number.isNaN(urlValue) && urlValue !== envConfig.bondShock) {
        setEnvConfig(prev => ({ ...prev, bondShock: urlValue }))
      }
    }
    
    if (urlCpiShock !== null) {
      const urlValue = Number(urlCpiShock)
      if (!Number.isNaN(urlValue) && urlValue !== envConfig.cpiShock) {
        setEnvConfig(prev => ({ ...prev, cpiShock: urlValue }))
      }
    }
    
    // Update stress if URL param differs from state
    if (urlStress && urlStress !== selectedStress) {
      setSelectedStress(urlStress)
    }
    
    // Update scenario if URL param differs from state
    if (urlScenario && (urlScenario === 'even' || urlScenario === 'conservative' || urlScenario === 'aggressive')) {
      if (urlScenario !== selectedScenarioId) {
        // Use selectScenario to properly load the scenario (includes tranches, view mode, etc.)
        const targetLoan = Math.max(0, numericPropertyValue - numericUserEquity)
        if (targetLoan > 0) {
          const scenarioScenarios = createMortgageScenarios(primeRate, targetLoan)
          const scenario = scenarioScenarios.find(s => s.id === urlScenario)
          if (scenario) {
            setSelectedScenarioId(urlScenario as ScenarioType)
            setTranches(scenario.tranches.map(t => ({ ...t })))
            setExpandedTranches(
              scenario.tranches.reduce((acc, tranche) => {
                acc[tranche.id] = true
                return acc
              }, {} as Record<string, boolean>)
            )
            setViewMode('edit')
          } else {
            setSelectedScenarioId(urlScenario as ScenarioType)
          }
        } else {
          setSelectedScenarioId(urlScenario as ScenarioType)
        }
      }
    } else if (!urlScenario && selectedScenarioId) {
      // Clear scenario if URL doesn't have it
      setSelectedScenarioId(null)
    }
  }, [isClient, searchParams, numericPropertyValue, numericUserEquity, numericMonthlyIncome, envConfig.boiAnnual, envConfig.primeSpread, envConfig.boiShock, envConfig.bondShock, envConfig.cpiShock, selectedStress, selectedScenarioId, primeRate])

  useEffect(() => {
    const targetLoan = Math.max(0, numericPropertyValue - numericUserEquity)
    if (viewMode === 'edit') {
      rebalanceTranches(targetLoan)
    }
    // Always switch to compare mode if we have property value entered (whether scenarios exist or not)
    // This ensures we show either scenarios or the empty state message
    if (numericPropertyValue > 0 && !selectedScenarioId && viewMode === 'edit') {
      setViewMode('compare')
      // Clear tranches when switching to compare mode so scenarios are the focus
      if (scenarios.length > 0 && !hasClearedTranchesRef.current && tranches.length > 0) {
        setTranches([])
        hasClearedTranchesRef.current = true
      }
    }
    // Switch to edit mode only if we don't have property value entered
    if (numericPropertyValue <= 0 && viewMode === 'compare' && !selectedScenarioId) {
      setViewMode('edit')
      setSelectedScenarioId(null)
      hasClearedTranchesRef.current = false
    }
  }, [numericPropertyValue, numericUserEquity, rebalanceTranches, viewMode, selectedScenarioId, scenarios.length, tranches.length])

  const selectScenario = (scenarioId: ScenarioType) => {
    const scenario = scenarios.find(s => s.id === scenarioId)
    if (scenario) {
      setSelectedScenarioId(scenarioId)
      setTranches(scenario.tranches.map(t => ({ ...t })))
      setExpandedTranches(
        scenario.tranches.reduce((acc, tranche) => {
          acc[tranche.id] = true
          return acc
        }, {} as Record<string, boolean>)
      )
      setViewMode('edit')
    }
  }

  const resetToCompare = () => {
    setSelectedScenarioId(null)
    setViewMode('compare')
  }

  useEffect(() => {
    setEnvConfig(prev => {
      if (prev.monthlyIncome === numericMonthlyIncome) return prev
      return { ...prev, monthlyIncome: numericMonthlyIncome }
    })
  }, [numericMonthlyIncome])

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
      property_value: numericPropertyValue,
      monthly_income: numericMonthlyIncome,
      boi_rate: envConfig.boiAnnual,
      stress: { boiShock: envConfig.boiShock, cpiShock: envConfig.cpiShock },
      tranches: tranches.map(({ id, ...tranche }) => tranche)
    })

    await new Promise(resolve => setTimeout(resolve, 400))

    const latestResult = pricePortfolio({
      ...envConfig,
      monthlyIncome: numericMonthlyIncome,
      tranches: tranches.map(({ id, ...tranche }) => tranche)
    })

    trackCalculatorCalculation(
      'mortgage',
      {
        propertyValue: numericPropertyValue,
        monthlyIncome: numericMonthlyIncome,
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
      amount: Math.max(0, numericPropertyValue - numericUserEquity - totalLoanAmount),
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

  const handleBasicNumberChange = (value: string, setter: (value: number | null) => void) => {
    if (value === '') {
      setter(null)
      return
    }
    const numeric = Number(value)
    setter(Number.isFinite(numeric) ? numeric : null)
  }

  const monthlyAtYear = (years: number) => portfolioResult.blendedMonthlyAt(years * 12)

  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader heading="מחשבון משכנתא" text="תכנון תיק משכנתא רב-מסלולי עם תרחישי לחץ" />

        <StickyActionBar description="בצע חישוב תיק משכנתא גם בזמן גלילה" className="mb-4">
          <Button
            onClick={handleAnalyzePortfolio}
            disabled={isCalculateDisabled}
            size="lg"
            className="h-11 sm:h-12 rounded-full px-4 sm:px-6 flex items-center justify-center gap-2 text-sm sm:text-base font-medium shadow-sm w-full sm:w-auto"
          >
            {calculating ? (
              <Loader2 className="h-4 w-4 sm:h-5 sm:w-5 shrink-0 animate-spin" />
            ) : (
              <Calculator className="h-4 w-4 sm:h-5 sm:w-5 shrink-0" />
            )}
            <span className="hidden sm:inline">חשב תיק</span>
            <span className="sm:hidden">חשב</span>
          </Button>
        </StickyActionBar>

        <div className="grid gap-6 lg:grid-cols-[1fr,400px] xl:grid-cols-[2fr,1fr]">
          {/* Main Content Column */}
          <div className="space-y-6">
            {/* Basic Data - Compact at top */}
            <Card className="border-primary/10">
              <CardHeader className="pb-3">
                <CardTitle className="text-xl">נתוני בסיס</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {isMissingBasicInputs && (
                  <div className="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                    <AlertTriangle className="h-4 w-4 mt-0.5" />
                    <div className="space-y-0.5">
                      <p className="font-semibold">השלימו את שווי הנכס, ההון העצמי וההכנסה החודשית כדי להתחיל.</p>
                      <p className="text-[11px] leading-tight">נמלא עבורך נתונים ששמרת בפרופיל או שהעברת מדפים אחרים אם קיימים.</p>
                    </div>
                  </div>
                )}
                {/* Essential Fields - Always Visible */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <div>
                    <label htmlFor="property-value" className="text-xs font-medium text-muted-foreground mb-1 block">שווי נכס</label>
                    <Input
                      id="property-value"
                      type="number"
                      value={propertyValue ?? ''}
                      onChange={event => handleBasicNumberChange(event.target.value, setPropertyValue)}
                      className="h-9"
                      placeholder="הזינו את שווי הנכס"
                    />
                  </div>
                  <div>
                    <label htmlFor="user-equity" className="text-xs font-medium text-muted-foreground mb-1 block">הון עצמי</label>
                    <Input
                      id="user-equity"
                      type="number"
                      value={userEquity ?? ''}
                      onChange={event => handleBasicNumberChange(event.target.value, setUserEquity)}
                      className="h-9"
                      placeholder="הון עצמי מהפרופיל או הזינו ידנית"
                    />
                  </div>
                  <div>
                    <label htmlFor="monthly-income" className="text-xs font-medium text-muted-foreground mb-1 block">הכנסה חודשית</label>
                    <Input
                      id="monthly-income"
                      type="number"
                      value={monthlyIncome ?? ''}
                      onChange={event => handleBasicNumberChange(event.target.value, setMonthlyIncome)}
                      className="h-9"
                      placeholder="נמלא אם נשמר בפרופיל, אחרת הזינו"
                    />
                  </div>
                  <div className="flex items-end">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                      className="w-full justify-between"
                    >
                      <Settings className="h-4 w-4" />
                      <span className="text-xs">הגדרות מתקדמות</span>
                      {showAdvancedSettings ? (
                        <ChevronUp className="h-3 w-3" />
                      ) : (
                        <ChevronDown className="h-3 w-3" />
                      )}
                    </Button>
                  </div>
                </div>

                {/* Advanced Settings - Collapsible */}
                {showAdvancedSettings && (
                  <>
                    <Separator />
                    <div className="space-y-4">
                      <div>
                        <label className="text-xs font-medium text-muted-foreground mb-2 block">ריביות וסביבה</label>
                        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                          <div>
                            <label className="text-xs text-muted-foreground mb-1 block">ריבית בנק ישראל</label>
                            <div className="flex items-center gap-2">
                              {loadingBoiRate ? (
                                <Skeleton className="h-9 w-full" />
                              ) : (
                                <Input
                                  type="number"
                                  step="0.01"
                                  value={envConfig.boiAnnual}
                                  onChange={event => setEnvConfig(prev => ({ ...prev, boiAnnual: Number(event.target.value) || 0 }))}
                                  className="h-9"
                                />
                              )}
                              <Button 
                                variant="outline" 
                                size="icon" 
                                onClick={fetchBOIRateFromApi} 
                                aria-label="רענון ריבית בנק ישראל"
                                className="h-9 w-9"
                              >
                                <Loader2 className={`h-3 w-3 ${loadingBoiRate ? 'animate-spin' : ''}`} />
                              </Button>
                            </div>
                            {lastUpdated && (
                              <p className="mt-1 text-xs text-muted-foreground">עדכון אחרון: {new Date(lastUpdated).toLocaleDateString('he-IL')}</p>
                            )}
                          </div>
                          <div>
                            <label className="text-xs text-muted-foreground mb-1 block">מרווח פריים</label>
                            <Input
                              type="number"
                              step="0.01"
                              value={envConfig.primeSpread}
                              onChange={event => setEnvConfig(prev => ({ ...prev, primeSpread: Number(event.target.value) || 0 }))}
                              className="h-9"
                            />
                            <p className="mt-1 text-xs text-muted-foreground">פריים: {primeRate.toFixed(2)}%</p>
                          </div>
                          <div>
                            <label className="text-xs text-muted-foreground mb-1 block">תוספת לעוגן אג״ח</label>
                            <Input
                              type="number"
                              step="0.1"
                              value={envConfig.bondShock ?? 0}
                              onChange={event => setEnvConfig(prev => ({ ...prev, bondShock: Number(event.target.value) || 0 }))}
                              className="h-9"
                            />
                          </div>
                        </div>
                      </div>
                      <Separator />
                      <div>
                        <label className="text-xs font-medium text-muted-foreground mb-2 block">תרחישי לחץ</label>
                        <div className="flex flex-wrap gap-2">
                          {stressPresets.map(preset => (
                            <Button
                              key={preset.id}
                              type="button"
                              size="sm"
                              variant={selectedStress === preset.id ? 'default' : 'outline'}
                              onClick={() => handleStressPreset(preset.id)}
                              className="h-8 text-xs"
                            >
                              {preset.label}
                            </Button>
                          ))}
                        </div>
                        <p className="mt-2 text-xs text-muted-foreground">
                          שינוי ריבית בנק ישראל: {(envConfig.boiShock ?? 0).toFixed(2)}% · שינוי מדד: {(envConfig.cpiShock ?? 0).toFixed(2)}%
                        </p>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Scenarios Comparison - Show right below basic data */}
            {viewMode === 'compare' && scenarios.length > 0 && (
              <Card className="border-primary/20 shadow-lg">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-2xl">השוואת תרחישים</CardTitle>
                      <p className="text-sm text-muted-foreground mt-1">
                        בחר תרחיש כדי לראות פרטים נוספים ולערוך את המסלולים
                      </p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 grid-cols-1 sm:grid-cols-1 md:grid-cols-3">
                    {scenarioResults.map(({ scenario, result }) => {
                      const affordability = calculateAffordability(numericMonthlyIncome, result.blendedFirstPayment)
                      const ltv = calculateLTV(
                        scenario.tranches.reduce((sum, t) => sum + t.amount, 0),
                        numericPropertyValue
                      )
                      const isSelected = selectedScenarioId === scenario.id
                      return (
                        <Card 
                          key={scenario.id} 
                          className={cn(
                            "relative transition-all duration-200 cursor-pointer hover:shadow-md",
                            isSelected && "border-primary ring-2 ring-primary/20 shadow-lg scale-[1.01]",
                            !isSelected && "hover:border-primary/30",
                            "border-2"
                          )}
                          onClick={() => selectScenario(scenario.id)}
                        >
                          <CardHeader className="pb-3">
                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-1 gap-2">
                              <CardTitle className="text-lg font-bold">{scenario.name}</CardTitle>
                              {isSelected && (
                                <Badge variant="default" className="w-fit">✓ נבחר</Badge>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">{scenario.description}</p>
                          </CardHeader>
                          <CardContent className="space-y-3 pt-0">
                            <div className="space-y-2">
                              <div className="flex items-center justify-between">
                                <span className="text-xs text-muted-foreground">תשלום ראשון</span>
                                <span className="text-base font-bold">{fmtCurrency(result.blendedFirstPayment)}</span>
                              </div>
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">תשלום מקסימלי</span>
                                <span className="font-semibold">{fmtCurrency(result.blendedMaxPayment)}</span>
                              </div>
                              <Separator className="my-2" />
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">סה״כ תשלומים</span>
                                <span className="font-semibold">{fmtCurrency(result.totals.paid)}</span>
                              </div>
                              <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                                <div>
                                  <span className="text-muted-foreground block">ריבית</span>
                                  <span className="font-medium">{fmtCurrency(result.totals.interest)}</span>
                                </div>
                                <div>
                                  <span className="text-muted-foreground block">הצמדה</span>
                                  <span className="font-medium">{fmtCurrency(result.totals.indexation)}</span>
                                </div>
                              </div>
                              <Separator className="my-2" />
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">יחס החזר להכנסה</span>
                                <Badge variant={affordability.isAffordable ? 'success' : 'destructive'} className="text-xs">
                                  {affordability.ratio.toFixed(1)}%
                                </Badge>
                              </div>
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">יחס מימון (LTV)</span>
                                <Badge variant={ltv <= 60 ? 'success' : ltv <= 75 ? 'neutral' : 'destructive'} className="text-xs">
                                  {ltv.toFixed(1)}%
                                </Badge>
                              </div>
                            </div>
                            <Button
                              className="w-full mt-4"
                              onClick={(e) => {
                                e.stopPropagation()
                                selectScenario(scenario.id)
                              }}
                              variant={isSelected ? 'default' : 'outline'}
                              size="sm"
                            >
                              {isSelected ? '✓ נבחר' : 'בחר תרחיש זה'}
                            </Button>
                          </CardContent>
                        </Card>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Empty State - when no loan amount or equity >= property value */}
            {viewMode === 'compare' && scenarios.length === 0 && (
              <Card className="border-2 border-dashed">
                <CardContent className="flex flex-col items-center justify-center py-12 px-4">
                  <div className="rounded-full bg-muted p-4 mb-4">
                    <Calculator className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2 text-center">
                    {numericPropertyValue > 0 && numericUserEquity >= numericPropertyValue 
                      ? 'הון עצמי גדול משווי הנכס - לא נדרש מימון'
                      : 'הכנס נתונים כדי לראות תרחישים'}
                  </h3>
                  <p className="text-sm text-muted-foreground text-center max-w-sm">
                    {numericPropertyValue > 0 && numericUserEquity >= numericPropertyValue
                      ? 'כאשר ההון העצמי גדול או שווה לשווי הנכס, לא ניתן ליצור תרחישי משכנתא'
                      : 'הזן שווי נכס והון עצמי (כאשר ההון העצמי קטן משווי הנכס) כדי לראות 3 תרחישי משכנתא אפשריים'}
                  </p>
                </CardContent>
              </Card>
            )}

            {/* Selected Scenario Header */}
            {viewMode === 'edit' && selectedScenarioId && (
              <Card className="border-primary/20 bg-primary/5">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-xl">תרחיש נבחר: {scenarios.find(s => s.id === selectedScenarioId)?.name}</CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">
                      {scenarios.find(s => s.id === selectedScenarioId)?.description}
                    </p>
                  </div>
                  <Button onClick={resetToCompare} variant="outline" size="sm">
                    ← חזרה להשוואה
                  </Button>
                </CardHeader>
              </Card>
            )}


            {/* Tranches section - Only show when a scenario is selected (which switches to edit mode) */}
            {viewMode === 'edit' && selectedScenarioId && (
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
            )}

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

          {/* Sidebar Column - Summary & Details - Only show when scenario selected */}
          {((viewMode === 'compare' && selectedScenarioId) || (viewMode === 'edit' && selectedScenarioId)) && (
            <div className="space-y-6">
              {/* Summary Panel - Compare mode */}
              {viewMode === 'compare' && selectedScenarioId && (
                <>
                  <Card className="top-6">
                    <CardHeader>
                      <CardTitle className="text-lg">סיכום תרחיש נבחר</CardTitle>
                      <p className="text-sm text-muted-foreground mt-1">
                        {scenarios.find(s => s.id === selectedScenarioId)?.name}
                      </p>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {(() => {
                        const selectedResult = scenarioResults.find(sr => sr.scenario.id === selectedScenarioId)
                        if (!selectedResult) return null
                        const { result } = selectedResult
                        const selectedScenario = scenarios.find(s => s.id === selectedScenarioId)
                        const loanAmount = selectedScenario
                          ? selectedScenario.tranches.reduce((sum, t) => sum + t.amount, 0)
                          : 0
                        const ltvValue = calculateLTV(loanAmount, numericPropertyValue)
                        const affordabilityValue = calculateAffordability(numericMonthlyIncome, result.blendedFirstPayment)
                        return (
                          <>
                            <div className="grid gap-3">
                              <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">תשלום ראשון</span>
                                <span className="text-lg font-semibold">{fmtCurrency(result.blendedFirstPayment)}</span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">תשלום מקסימלי</span>
                                <span className="text-lg font-semibold">{fmtCurrency(result.blendedMaxPayment)}</span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">סה״כ הלוואה</span>
                                <span className="text-lg font-semibold">{fmtCurrency(loanAmount)}</span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">סה״כ תשלומים (כולל עמלות)</span>
                                <span className="text-lg font-semibold">{fmtCurrency(result.totals.paid)}</span>
                              </div>
                            </div>
                            <Separator />
                            <div className="space-y-2 text-sm">
                              <div className="flex items-center justify-between">
                                <span>ריבית</span>
                                <span>{fmtCurrency(result.totals.interest)}</span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span>הצמדה</span>
                                <span>{fmtCurrency(result.totals.indexation)}</span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span>עמלות</span>
                                <span>{fmtCurrency(result.totals.fees)}</span>
                              </div>
                            </div>
                            <Separator />
                            <div className="space-y-2 text-sm">
                              <div className="flex items-center justify-between">
                                <span>יחס החזר להכנסה</span>
                                <Badge variant={affordabilityValue.isAffordable ? 'success' : 'destructive'}>
                                  {affordabilityValue.ratio.toFixed(1)}%
                                </Badge>
                              </div>
                              <div className="flex items-center justify-between">
                                <span>יחס מימון (LTV)</span>
                                <Badge variant={ltvValue <= 60 ? 'success' : ltvValue <= 75 ? 'neutral' : 'destructive'}>
                                  {ltvValue.toFixed(1)}%
                                </Badge>
                              </div>
                            </div>
                          </>
                        )
                      })()}
                    </CardContent>
                  </Card>

                  {/* Future Payments - Compare mode */}
                  {viewMode === 'compare' && selectedScenarioId && (() => {
                    const selectedResult = scenarioResults.find(sr => sr.scenario.id === selectedScenarioId)
                    if (!selectedResult) return null
                    const { result } = selectedResult
                    const monthlyAtYear = (years: number) => result.blendedMonthlyAt(years * 12)
                    return (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-lg">תשלומים עתידיים</CardTitle>
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
                    )
                  })()}

                  {/* Tranche Details - Compare mode */}
                  {viewMode === 'compare' && selectedScenarioId && (() => {
                    const selectedResult = scenarioResults.find(sr => sr.scenario.id === selectedScenarioId)
                    if (!selectedResult) return null
                    const { result } = selectedResult
                    return (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-lg">פירוט מסלולים</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4 text-sm">
                          {result.tranches.map((tranche, index) => (
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
                                  <span>תשואה שנתית משוערת</span>
                                  <span>{tranche.aprApprox.toFixed(2)}%</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </CardContent>
                      </Card>
                    )
                  })()}
                </>
              )}

              {/* Summary Panel - Edit mode */}
              {viewMode === 'edit' && selectedScenarioId && tranches.length > 0 && (
                <>
                  <Card className="top-6">
                    <CardHeader>
                      <CardTitle className="text-lg">סיכום תיק</CardTitle>
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

                  {/* Future Payments - Edit mode */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">תשלומים עתידיים</CardTitle>
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

                  {/* Tranche Details - Edit mode */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">פירוט מסלולים</CardTitle>
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
                              <span>תשואה שנתית משוערת</span>
                              <span>{tranche.aprApprox.toFixed(2)}%</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </>
              )}
            </div>
          )}
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}
