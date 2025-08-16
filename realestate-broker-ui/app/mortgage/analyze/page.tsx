'use client'
import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import DashboardLayout from '@/components/layout/dashboard-layout'

export default function MortgageAnalyzePage() {
  const [price, setPrice] = useState(5200000)
  const [down, setDown] = useState(1560000)
  const [rate, setRate] = useState(4.3)
  const [years, setYears] = useState(25)
  
  const loanAmount = price - down
  const monthlyRate = rate / 100 / 12
  const monthsTotal = years * 12
  const monthlyPayment = (loanAmount * monthlyRate * Math.pow(1 + monthlyRate, monthsTotal)) / (Math.pow(1 + monthlyRate, monthsTotal) - 1)
  const totalInterest = (monthlyPayment * monthsTotal) - loanAmount
  const totalPayment = loanAmount + totalInterest

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">אנליזת משכנתא</h1>
          <p className="text-muted-foreground">חישוב תרחישי מימון מתקדמים</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Input Form */}
          <Card>
            <CardHeader>
              <CardTitle>פרמטרי המשכנתא</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">מחיר הנכס (₪)</label>
                <Input 
                  type="number" 
                  value={price}
                  onChange={(e) => setPrice(Number(e.target.value))}
                  placeholder="5,200,000"
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">הון עצמי (₪)</label>
                <Input 
                  type="number" 
                  value={down}
                  onChange={(e) => setDown(Number(e.target.value))}
                  placeholder="1,560,000"
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">ריבית שנתיה (%)</label>
                <Input 
                  type="number" 
                  step="0.1"
                  value={rate}
                  onChange={(e) => setRate(Number(e.target.value))}
                  placeholder="4.3"
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">תקופת הלוואה (שנים)</label>
                <Input 
                  type="number" 
                  value={years}
                  onChange={(e) => setYears(Number(e.target.value))}
                  placeholder="25"
                />
              </div>
              
              <Button className="w-full">חשב מחדש</Button>
            </CardContent>
          </Card>

          {/* Results */}
          <Card>
            <CardHeader>
              <CardTitle>תוצאות החישוב</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 rounded-lg bg-muted">
                  <div className="text-sm text-muted-foreground">סכום הלוואה</div>
                  <div className="text-xl font-bold">₪{loanAmount.toLocaleString()}</div>
                </div>
                
                <div className="text-center p-4 rounded-lg bg-muted">
                  <div className="text-sm text-muted-foreground">% מימון</div>
                  <div className="text-xl font-bold">{((loanAmount / price) * 100).toFixed(1)}%</div>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm">החזר חודשי:</span>
                  <Badge variant="default" className="text-lg px-3 py-1">
                    ₪{monthlyPayment.toLocaleString('he-IL', { maximumFractionDigits: 0 })}
                  </Badge>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm">סה״כ ריבית:</span>
                  <span className="font-medium">₪{totalInterest.toLocaleString('he-IL', { maximumFractionDigits: 0 })}</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm">סה״כ החזר:</span>
                  <span className="font-medium">₪{totalPayment.toLocaleString('he-IL', { maximumFractionDigits: 0 })}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Scenarios */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>השוואת תרחישים</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { name: 'ריבית נמוכה', rate: 3.8, bgColor: 'bg-green-50 dark:bg-green-950' },
                  { name: 'ריבית נוכחית', rate: 4.3, bgColor: 'bg-blue-50 dark:bg-blue-950' },
                  { name: 'ריבית גבוהה', rate: 5.0, bgColor: 'bg-red-50 dark:bg-red-950' }
                ].map((scenario) => {
                  const scenarioMonthlyRate = scenario.rate / 100 / 12
                  const scenarioPayment = (loanAmount * scenarioMonthlyRate * Math.pow(1 + scenarioMonthlyRate, monthsTotal)) / (Math.pow(1 + scenarioMonthlyRate, monthsTotal) - 1)
                  
                  return (
                    <div key={scenario.name} className={`p-4 rounded-lg ${scenario.bgColor}`}>
                      <h3 className="font-medium text-center">{scenario.name}</h3>
                      <div className="text-center text-sm text-muted-foreground">{scenario.rate}% שנתיה</div>
                      <div className="text-center text-xl font-bold mt-2">
                        ₪{scenarioPayment.toLocaleString('he-IL', { maximumFractionDigits: 0 })}
                      </div>
                      <div className="text-center text-sm">לחודש</div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Info */}
        <Card>
          <CardHeader>
            <CardTitle>טיפים לחישוב משכנתא</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h3 className="font-medium mb-2">💡 הון עצמי מומלץ</h3>
                <p className="text-sm text-muted-foreground">
                  מומלץ להכין הון עצמי של לפחות 30% ממחיר הנכס כדי לקבל תנאי מימון טובים יותר
                </p>
              </div>
              <div>
                <h3 className="font-medium mb-2">📊 יחס הכנסה להחזר</h3>
                <p className="text-sm text-muted-foreground">
                  ודאו שההחזר החודשי לא עולה על 40% מההכנסה הנטו המשפחתית
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}