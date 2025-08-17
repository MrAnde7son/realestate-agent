'use client'
import React, { useState, useEffect } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { fmtCurrency, fmtNumber } from '@/lib/utils'
import { calculateAllScenarios, calculateLTV, calculateAffordability, type MortgageInput, type MortgageCalculation } from '@/lib/mortgage'

export default function BOIMortgageCalculatorPage() {
  const [input, setInput] = useState<MortgageInput>({
    loanAmount: 2800000,
    loanTermYears: 25,
    propertyValue: 3500000
  })
  
  const [monthlyIncome, setMonthlyIncome] = useState<number>(35000)
  const [calculations, setCalculations] = useState<MortgageCalculation[]>([])
  const [boiRate, setBOIRate] = useState<number>(4.75)
  const [lastUpdated, setLastUpdated] = useState<string>('')

  useEffect(() => {
    // Fetch current BOI rate on component mount
    fetchBOIRate()
  }, [])

  const fetchBOIRate = async () => {
    try {
      const response = await fetch('/api/boi-rate')
      const data = await response.json()
      if (data.success) {
        setBOIRate(data.data.baseRate)
        setLastUpdated(data.data.lastUpdated)
      }
    } catch (error) {
      console.error('Error fetching BOI rate:', error)
    }
  }

  const calculateMortgage = () => {
    const results = calculateAllScenarios(input)
    setCalculations(results)
  }

  const ltv = calculateLTV(input.loanAmount, input.propertyValue)

  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader heading="מחשבון משכנתא - בנק ישראל" text="חישוב ריבית בהתבסס על נתוני בנק ישראל בזמן אמת" />
        
        {/* Bank of Israel Rate Display */}
        <Card className="mb-6">
          <CardContent className="flex items-center justify-between p-4">
            <div>
              <div className="text-sm text-muted-foreground">ריבית בנק ישראל נוכחית</div>
              <div className="text-2xl font-bold">{boiRate}%</div>
            </div>
            <div className="text-left">
              <Badge variant="outline">עדכון אחרון: {new Date(lastUpdated).toLocaleDateString('he-IL')}</Badge>
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
                  onChange={(e) => setInput({...input, propertyValue: parseInt(e.target.value) || 0})}
                  placeholder="3,500,000" 
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">סכום הלוואה</label>
                <Input 
                  type="number" 
                  value={input.loanAmount}
                  onChange={(e) => setInput({...input, loanAmount: parseInt(e.target.value) || 0})}
                  placeholder="2,800,000" 
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">תקופת הלוואה (שנים)</label>
                <Input 
                  type="number" 
                  value={input.loanTermYears}
                  onChange={(e) => setInput({...input, loanTermYears: parseInt(e.target.value) || 0})}
                  placeholder="25" 
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">הכנסה חודשית נטו</label>
                <Input 
                  type="number" 
                  value={monthlyIncome}
                  onChange={(e) => setMonthlyIncome(parseInt(e.target.value) || 0)}
                  placeholder="35,000" 
                />
              </div>
              
              {/* LTV Display */}
              <div className="p-3 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">יחס המימון (LTV)</div>
                <div className="text-lg font-semibold">{ltv.toFixed(1)}%</div>
                <Badge variant={ltv <= 75 ? 'good' : ltv <= 85 ? 'warn' : 'bad'}>
                  {ltv <= 75 ? 'יחס טוב' : ltv <= 85 ? 'יחס בינוני' : 'יחס גבוה'}
                </Badge>
              </div>
              
              <Button 
                className="w-full" 
                onClick={calculateMortgage}
                disabled={!input.loanAmount || !input.propertyValue || !input.loanTermYears}
              >
                חשב 3 תרחישי משכנתא
              </Button>
            </CardContent>
          </Card>

          {/* Results */}
          <div className="space-y-4">
            {calculations.length > 0 && (
              <>
                <h3 className="text-lg font-semibold">תרחישי ריבית (מבוסס על בנק ישראל {boiRate}%)</h3>
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
                          <Badge variant={index === 0 ? 'default' : index === 1 ? 'secondary' : 'outline'}>
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
                            <Badge variant={affordability.isAffordable ? 'good' : 'bad'}>
                              {affordability.isAffordable ? 'בר השגה' : 'מעבר ליכולת'}
                            </Badge>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
                
                {/* Summary Comparison */}
                {calculations.length > 1 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>השוואה בין התרחישים</CardTitle>
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
              </>
            )}
          </div>
        </div>

        {/* BOI Information */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>אודות ריבית בנק ישראל</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h3 className="font-medium mb-2">📈 השפעת ריבית בנק ישראל</h3>
                <p className="text-sm text-muted-foreground">
                  ריבית בנק ישראל מהווה בסיס לחישוב ריביות המשכנתא בכל הבנקים. שינוי של 0.25% יכול להשפיע על מאות שקלים בתשלום החודשי.
                </p>
              </div>
              <div>
                <h3 className="font-medium mb-2">🏦 מרווחי הבנקים</h3>
                <p className="text-sm text-muted-foreground">
                  כל בנק מוסיף מרווח לריבית הבסיסית. המרווח משתנה בהתאם לפרופיל הלקוח, סוג המשכנתא ותנאי השוק.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </DashboardShell>
    </DashboardLayout>
  )
}
