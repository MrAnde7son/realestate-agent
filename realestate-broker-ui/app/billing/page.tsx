'use client'

import React, { useState, useEffect } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/button'
import { ContactSupportDialog, ConsultationDialog } from '@/components/support/dialogs'
import { Badge } from '@/components/ui/Badge'
import { Check, Star, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'
import PlanInfo from '@/components/PlanInfo'
import { useAuth } from '@/lib/auth-context'
import { authAPI, PlanInfo as PlanInfoType } from '@/lib/auth'

const plans = [
  {
    name: "חבילה חינמית",
    description: "למשתמשים מתחילים",
    price: "0 ₪",
    priceDescription: "לחודש",
    features: [
      "נכס אחד במעקב",
      "התראות בסיסיות",
      "מחשבון משכנתא בסיסי",
      "דוחות בסיסיים",
      "תמיכה בדוא״ל, וואטסאפ"
    ],
    limitations: [
      "ללא ניתוח מתקדם",
      "ללא ייצוא נתונים",
      "ללא תמיכה טלפונית"
    ],
    popular: false,
    icon: Star
  },
  {
    name: "חבילה בסיסית",
    description: "למשתמשים מתקדמים",
    price: "149 ₪",
    priceDescription: "לחודש",
    features: [
      "עד 10 נכסים במעקב",
      "התראות מתקדמות",
      "מחשבון משכנתא מתקדם",
      "דוחות מפורטים",
      "ייצוא נתונים ל-Excel",
      "ניתוח שוק בסיסי"
    ],
    limitations: [
      "ללא ניתוח AI מתקדם",
      "ללא אינטגרציה עם מערכות חיצוניות"
    ],
    popular: true,
    icon: Zap
  },
  {
    name: "חבילה מקצועית",
    description: "למשתמשים מקצועיים",
    price: "299 ₪",
    priceDescription: "לחודש",
    features: [
      "נכסים במעקב ללא הגבלה",
      "התראות מותאמות אישית",
      "מחשבון משכנתא מתקדם",
      "דוחות מותאמים אישית",
      "ייצוא נתונים לכל הפורמטים",
      "ניתוח שוק מתקדם",
      "ניתוח AI מתקדם",
      "אינטגרציה עם מערכות חיצוניות",
      "API גישה",
      "ניהול משתמשים והרשאות"
    ],
    limitations: [],
    popular: false,
    icon: Zap
  }
]

export default function BillingPage() {
  const { isAuthenticated } = useAuth()
  const [currentPlan, setCurrentPlan] = useState<PlanInfoType | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (isAuthenticated) {
      loadCurrentPlan()
    } else {
      setLoading(false)
    }
  }, [isAuthenticated])

  const loadCurrentPlan = async () => {
    try {
      const planInfo = await authAPI.getPlanInfo()
      setCurrentPlan(planInfo)
    } catch (error) {
      console.error('Error loading current plan:', error)
    } finally {
      setLoading(false)
    }
  }

  const getPlanButtonText = (planName: string) => {
    if (!currentPlan) return "התחל עכשיו"
    
    const planMap: Record<string, string> = {
      "חבילה חינמית": "free",
      "חבילה בסיסית": "basic", 
      "חבילה מקצועית": "pro"
    }
    
    const planKey = planMap[planName]
    if (planKey === currentPlan.plan_name) {
      return "החבילה הנוכחית"
    }
    
    return "בחר חבילה"
  }

  const getPlanButtonVariant = (planName: string) => {
    if (!currentPlan) return "outline" as const
    
    const planMap: Record<string, string> = {
      "חבילה חינמית": "free",
      "חבילה בסיסית": "basic",
      "חבילה מקצועית": "pro"
    }
    
    const planKey = planMap[planName]
    if (planKey === currentPlan.plan_name) {
      return "secondary" as const
    }
    
    return planName === "חבילה בסיסית" ? "default" as const : "outline" as const
  }

  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader 
          heading="חבילות ותשלומים" 
          text="בחר את החבילה המתאימה לצרכים שלך" 
        />
        
        {/* Current Plan Information */}
        {isAuthenticated && (
          <div className="mb-8">
            <PlanInfo />
          </div>
        )}
        
        <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {plans.map((plan) => {
            const Icon = plan.icon
            return (
              <Card 
                key={plan.name} 
                className={cn(
                  "relative",
                  plan.popular && "border-primary shadow-lg"
                )}
              >
                {plan.popular && (
                  <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-primary text-primary-foreground">
                    הכי פופולרי
                  </Badge>
                )}
                
                <CardHeader className="text-center">
                  <div className="flex justify-center mb-4">
                    <Icon className="h-8 w-8 text-primary" />
                  </div>
                  <CardTitle className="text-2xl">{plan.name}</CardTitle>
                  <CardDescription>{plan.description}</CardDescription>
                  <div className="mt-4">
                    <span className="text-4xl font-bold">{plan.price}</span>
                    <span className="text-muted-foreground">/{plan.priceDescription}</span>
                  </div>
                </CardHeader>
                
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <h4 className="font-medium">כלול בחבילה:</h4>
                    <ul className="space-y-2">
                      {plan.features.map((feature) => (
                        <li key={feature} className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-green-500" />
                          <span className="text-sm">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  {plan.limitations.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="font-medium text-muted-foreground">לא כלול:</h4>
                      <ul className="space-y-2">
                        {plan.limitations.map((limitation) => (
                          <li key={limitation} className="flex items-center gap-2">
                            <span className="h-4 w-4 text-muted-foreground">×</span>
                            <span className="text-sm text-muted-foreground">{limitation}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
                
                <CardFooter>
                  <Button 
                    className="w-full" 
                    variant={getPlanButtonVariant(plan.name)}
                    size="lg"
                    disabled={loading}
                  >
                    {getPlanButtonText(plan.name)}
                  </Button>
                </CardFooter>
              </Card>
            )
          })}
        </div>

        {/* Additional Information */}
        <div className="mt-12 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>שאלות נפוצות</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-medium mb-2">האם אני יכול לשנות חבילה?</h4>
                <p className="text-sm text-muted-foreground">
                  כן, אתה יכול לשדרג או לשנמך חבילה בכל עת. השינויים יחולו בתחילת החודש הבא.
                </p>
              </div>
              <div>
                <h4 className="font-medium mb-2">האם יש תקופת ניסיון?</h4>
                <p className="text-sm text-muted-foreground">
                  כן, כל החבילות כוללות תקופת ניסיון של 14 יום ללא התחייבות.
                </p>
              </div>
              <div>
                <h4 className="font-medium mb-2">האם התשלום חוזר?</h4>
                <p className="text-sm text-muted-foreground">
                  כן, התשלום מתחדש אוטומטית כל חודש. אתה יכול לבטל בכל עת.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>צריכים עזרה?</CardTitle>
              <CardDescription>
                צוות התמיכה שלנו כאן לעזור לך לבחור את החבילה המתאימה
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                <ContactSupportDialog>
                  <Button variant="outline">
                    צור קשר עם התמיכה
                  </Button>
                </ContactSupportDialog>
                <ConsultationDialog>
                  <Button variant="outline">
                    הזמן שיחת ייעוץ
                  </Button>
                </ConsultationDialog>
              </div>
            </CardContent>
          </Card>
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}
