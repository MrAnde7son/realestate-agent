'use client'
import React, { useState, useEffect } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/skeleton'
import { fmtCurrency, fmtNumber } from '@/lib/utils'
import { calculateAllScenarios, calculateLTV, calculateAffordability, type MortgageInput, type MortgageCalculation } from '@/lib/mortgage'
import { Loader2, Calculator } from 'lucide-react'
import { useAnalytics } from '@/hooks/useAnalytics'
import { useOptionalAuth } from '@/lib/auth-context'

export default function MortgageAnalyzePage() {
  const { trackCalculatorUsage, trackCalculatorCalculation } = useAnalytics()
  const auth = useOptionalAuth()
  const user = auth?.user ?? null
  
  const [input, setInput] = useState<MortgageInput>({
    loanAmount: 2800000,
    loanTermYears: 25,
    propertyValue: 3500000
  })
  
  const [monthlyIncome, setMonthlyIncome] = useState<number>(35000)
  const [calculations, setCalculations] = useState<MortgageCalculation[]>([])
  const [boiRate, setBOIRate] = useState<number>(0)
  const [lastUpdated, setLastUpdated] = useState<string>('')
  const [loadingBoiRate, setLoadingBoiRate] = useState<boolean>(true)
  const [calculating, setCalculating] = useState<boolean>(false)
  const [requiredEquity, setRequiredEquity] = useState<number | null>(null)
  const [isClient, setIsClient] = useState(false)
  const [userEquity, setUserEquity] = useState<number>(0)

  useEffect(() => {
    if (user?.role === 'private') {
      const equityValue = typeof user.equity === 'number' ? user.equity : 0
      setUserEquity(equityValue)
    }
  }, [user])

  useEffect(() => {
    // Set client-side flag
    setIsClient(true)
    
    // Fetch current BOI rate on component mount
    fetchBOIRate()
    // Track calculator page view
    trackCalculatorUsage('mortgage', 'page_view')
  }, [trackCalculatorUsage])

  useEffect(() => {
    // Check for URL parameters from expenses calculator (only on client side)
    if (isClient) {
      const urlParams = new URLSearchParams(window.location.search)
      const propertyValue = urlParams.get('propertyValue')
      const totalExpenses = urlParams.get('totalExpenses')
      
      if (propertyValue || totalExpenses) {
        // Track that data was pre-filled from expenses calculator
        trackCalculatorUsage('mortgage', 'prefilled_from_expenses', {
          property_value: propertyValue,
          total_expenses: totalExpenses
        })
        
        // Update input with pre-filled values
        // propertyValue now contains the total cost (property + expenses)
        if (propertyValue) {
          const totalCost = parseInt(propertyValue)
          setInput(prev => ({
            ...prev,
            propertyValue: totalCost,
            loanAmount: totalCost, // Default to full amount, user can adjust
            loanTermYears: prev.loanTermYears // Keep default term
          }))
        }
        
        // Set total expenses for display
        if (totalExpenses) {
          setRequiredEquity(parseInt(totalExpenses))
        }
      }
    }
  }, [isClient, trackCalculatorUsage])

  useEffect(() => {
    // Calculate loan amount based on user equity
    const loanAmount = Math.max(0, input.propertyValue - userEquity)
    setInput(prev => ({ ...prev, loanAmount }))
  }, [userEquity, input.propertyValue])

  useEffect(() => {
    const results = calculateAllScenarios(input, boiRate)
    setCalculations(results)
  }, [input, boiRate])

  const fetchBOIRate = async () => {
    setLoadingBoiRate(true)
    try {
      const response = await fetch('/api/boi-rate')
      const data = await response.json()
      if (data.success) {
        setBOIRate(data.data.baseRate)
        setLastUpdated(data.data.lastUpdated)
      }
    } catch (error) {
      console.error('Error fetching BOI rate:', error)
    } finally {
      setLoadingBoiRate(false)
    }
  }

  const calculateMortgage = async () => {
    setCalculating(true)
    
    // Track calculation start
    trackCalculatorUsage('mortgage', 'calculation_start', {
      input_data: {
        loanAmount: input.loanAmount,
        loanTermYears: input.loanTermYears,
        propertyValue: input.propertyValue,
        monthlyIncome,
        boiRate
      }
    })
    
    // Add small delay to show loading state
    await new Promise(resolve => setTimeout(resolve, 500))
    const results = calculateAllScenarios(input, boiRate)
    setCalculations(results)
    
    // Track calculation completion
    trackCalculatorCalculation('mortgage', {
      loanAmount: input.loanAmount,
      loanTermYears: input.loanTermYears,
      propertyValue: input.propertyValue,
      monthlyIncome,
      boiRate
    }, {
      scenariosCount: results.length,
      ltv: calculateLTV(input.loanAmount, input.propertyValue),
      minMonthlyPayment: Math.min(...results.map(r => r.monthlyPayment)),
      maxMonthlyPayment: Math.max(...results.map(r => r.monthlyPayment))
    })
    
    setCalculating(false)
  }

  const ltv = calculateLTV(input.loanAmount, input.propertyValue)

  // Input change handlers with analytics
  const handleInputChange = (field: keyof MortgageInput, value: number) => {
    const newInput = { ...input, [field]: value }
    setInput(newInput)
    trackCalculatorUsage('mortgage', 'input_change', {
      field,
      value,
      input_data: newInput
    })
  }

  const handleMonthlyIncomeChange = (value: number) => {
    setMonthlyIncome(value)
    trackCalculatorUsage('mortgage', 'input_change', {
      field: 'monthlyIncome',
      value,
      input_data: { ...input, monthlyIncome: value }
    })
  }

  // Custom scenarios for comparison
  const customScenarios = [
    { name: 'תרחיש אופטימי', rate: 5.8, color: 'bg-green-50 dark:bg-green-950' },
    { name: 'תרחיש ריאלי', rate: 6.3, color: 'bg-blue-50 dark:bg-blue-950' }, 
    { name: 'תרחיש שמרני', rate: 7.0, color: 'bg-red-50 dark:bg-red-950' }
  ]

  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader heading="מחשבון משכנתא" text="חישוב ריבית בהתבסס על נתוני בנק ישראל בזמן אמת" />
        
        {/* Bank of Israel Rate Display */}
        <Card className="mb-6">
          <CardContent className="flex items-center justify-between p-4">
            <div>
              <div className="text-sm text-muted-foreground">ריבית בנק ישראל נוכחית</div>
              {loadingBoiRate ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <div className="text-2xl font-bold">{boiRate}%</div>
              )}
            </div>
            <div className="text-left">
              {loadingBoiRate ? (
                <Skeleton className="h-6 w-40" />
              ) : (
                <Badge variant="neutral">עדכון אחרון: {new Date(lastUpdated).toLocaleDateString('he-IL')}</Badge>
              )}
              <div className="text-xs text-muted-foreground mt-1">
                <a href="https://www.boi.org.il/" target="_blank" rel="noopener noreferrer" className="underline">
                  מקור: בנק ישראל
                </a>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Input Form */}
          <Card>
            <CardHeader>
              <CardTitle>פרטי המשכנתא</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">מחיר הנכס</label>
                <Input 
                  type="number" 
                  value={input.propertyValue}
                  onChange={(e) => handleInputChange('propertyValue', parseInt(e.target.value) || 0)}
                  placeholder="3,500,000" 
                />
              </div>
              
              {/* User Equity Input */}
              <div>
                <label className="block text-sm font-medium mb-2">הון עצמי</label>
                <Input 
                  type="number" 
                  value={userEquity}
                  onChange={(e) => setUserEquity(parseInt(e.target.value) || 0)}
                  placeholder="500,000" 
                />
                <div className="text-xs text-muted-foreground mt-1">
                  סכום ההון העצמי שלך (יופחת מהמחיר הכולל)
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">סכום הלוואה</label>
                <div className="relative">
                  <Input 
                    type="number" 
                    value={input.loanAmount}
                    readOnly
                    className="bg-muted pe-10"
                    placeholder="2,800,000" 
                  />
                  <div className="absolute start-3 top-1/2 transform -translate-y-1/2 text-muted-foreground text-sm">
                    מחושב אוטומטית
                  </div>
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {fmtCurrency(input.propertyValue)} - {fmtCurrency(userEquity)} = {fmtCurrency(input.loanAmount)}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">תקופת הלוואה (שנים)</label>
                <Input 
                  type="number" 
                  value={input.loanTermYears}
                  onChange={(e) => handleInputChange('loanTermYears', parseInt(e.target.value) || 0)}
                  placeholder="25" 
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">הכנסה חודשית נטו</label>
                <Input 
                  type="number" 
                  value={monthlyIncome}
                  onChange={(e) => handleMonthlyIncomeChange(parseInt(e.target.value) || 0)}
                  placeholder="35,000" 
                />
              </div>
              
              {/* LTV Display */}
              <div className="p-3 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">יחס המימון (LTV)</div>
                <div className="text-lg font-semibold">{ltv.toFixed(1)}%</div>
                <Badge variant={ltv <= 75 ? 'success' : ltv <= 85 ? 'warning' : 'error'}>
                  {ltv <= 75 ? 'יחס טוב' : ltv <= 85 ? 'יחס בינוני' : 'יחס גבוה'}
                </Badge>
              </div>

              {/* Info from Expenses Calculator */}
              {isClient && requiredEquity && (
                <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <div className="text-xs text-blue-600 dark:text-blue-400 p-2 bg-blue-100 dark:bg-blue-800/30 rounded">
                    💡 <strong>טיפ:</strong> המחיר הכולל כולל את הנכס + כל ההוצאות. הזן את ההון העצמי שלך למעלה כדי לחשב את המשכנתא הנדרשת.
                  </div>
                </div>
              )}
              
              <Button 
                className="w-full" 
                onClick={calculateMortgage}
                disabled={!input.loanAmount || !input.propertyValue || !input.loanTermYears || calculating}
              >
                {calculating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    מחשב תרחישים...
                  </>
                ) : (
                  <>
                    <Calculator className="h-4 w-4" />
                    חשב תרחישי משכנתא
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Bank Scenarios Results */}
          <div className="space-y-4">
            {calculations.length > 0 && (
              <>
                <h3 className="text-lg font-semibold">תרחישי בנקים (מבוסס על בנק ישראל {boiRate}%)</h3>
                {calculations.map((calc, index) => {
                  const affordability = calculateAffordability(monthlyIncome, calc.monthlyPayment)
                  
                  return (
                    <Card key={index} className="relative">
                      <CardHeader className="pb-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <CardTitle className="text-base">{calc.scenario.name}</CardTitle>
                            <p className="text-sm text-muted-foreground">{calc.scenario.description}</p>
                          </div>
                          <Badge variant={index === 0 ? 'default' : index === 1 ? 'accent' : 'neutral'}>
                            {calc.scenario.totalRate.toFixed(2)}%
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <div className="text-sm text-muted-foreground">תשלום חודשי</div>
                            <div className="text-lg font-bold">{fmtCurrency(calc.monthlyPayment)}</div>
                          </div>
                          <div>
                            <div className="text-sm text-muted-foreground">סה״כ תשלומים</div>
                            <div className="text-lg font-bold">{fmtCurrency(calc.totalPayment)}</div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <div className="text-sm text-muted-foreground">ריבית בלבד</div>
                            <div className="font-semibold text-red-600">{fmtCurrency(calc.totalInterest)}</div>
                          </div>
                          <div>
                            <div className="text-sm text-muted-foreground">מרווח הבנק</div>
                            <div className="font-semibold">{calc.scenario.bankMargin}%</div>
                          </div>
                        </div>

                        {/* Affordability Indicator */}
                        <div className="pt-2 border-t">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-muted-foreground">
                              יחס תשלום להכנסה: {affordability.ratio.toFixed(1)}%
                            </span>
                            <Badge variant={affordability.isAffordable ? 'success' : 'error'}>
                              {affordability.isAffordable ? 'בר השגה' : 'מעבר ליכולת'}
                            </Badge>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </>
            )}
          </div>
        </div>

        {/* Custom Scenarios Comparison */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>השוואת תרחישי ריבית</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {customScenarios.map((scenario) => {
                const monthlyRate = scenario.rate / 100 / 12
                const monthsTotal = input.loanTermYears * 12
                const payment = input.loanAmount > 0 
                  ? (input.loanAmount * monthlyRate * Math.pow(1 + monthlyRate, monthsTotal)) / (Math.pow(1 + monthlyRate, monthsTotal) - 1)
                  : 0
                
                return (
                  <div key={scenario.name} className={`p-4 rounded-lg ${scenario.color}`}>
                    <h3 className="font-medium text-center">{scenario.name}</h3>
                    <div className="text-center text-sm text-muted-foreground">{scenario.rate}% שנתי</div>
                    <div className="text-center text-xl font-bold mt-2">
                      {fmtCurrency(payment)}
                    </div>
                    <div className="text-center text-sm">לחודש</div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Comparison Summary */}
        {calculations.length > 1 && (
          <Card>
            <CardHeader>
              <CardTitle>השוואה בין הבנקים</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>הפרש תשלום חודשי (מקסימום vs מינימום):</span>
                  <span className="font-bold">
                    {fmtCurrency(Math.max(...calculations.map(c => c.monthlyPayment)) - Math.min(...calculations.map(c => c.monthlyPayment)))}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>הפרש סה״כ ריבית (מקסימום vs מינימום):</span>
                  <span className="font-bold text-red-600">
                    {fmtCurrency(Math.max(...calculations.map(c => c.totalInterest)) - Math.min(...calculations.map(c => c.totalInterest)))}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tips */}
        <Card>
          <CardHeader>
            <CardTitle>טיפים למשכנתא</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <h3 className="font-medium mb-2">📈 השפעת ריבית בנק ישראל</h3>
                <p className="text-sm text-muted-foreground">
                  ריבית בנק ישראל מהווה בסיס לחישוב ריביות המשכנתא בכל הבנקים. שינוי של 0.25% יכול להשפיע על מאות שקלים בתשלום החודשי.
                </p>
              </div>
              <div>
                <h3 className="font-medium mb-2">💡 הון עצמי מומלץ</h3>
                <p className="text-sm text-muted-foreground">
                  מומלץ להכין הון עצמי של לפחות 30% ממחיר הנכס כדי לקבל תנאי מימון טובים יותר ומרווחים נמוכים מהבנק.
                </p>
    </div>
    <div>
                <h3 className="font-medium mb-2">📊 יחס הכנסה להחזר</h3>
                <p className="text-sm text-muted-foreground">
                  ודאו שההחזר החודשי לא עולה על 30% מההכנסה הנטו המשפחתית כדי לשמור על איכות חיים טובה.
                </p>
    </div>
      </div>
          </CardContent>
        </Card>
      </DashboardShell>
    </DashboardLayout>
  )
}
