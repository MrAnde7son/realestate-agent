'use client'

import React from 'react'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/button'
import { fmtCurrency, fmtNumber } from '@/lib/utils'
import { BarChart3, MapPin } from 'lucide-react'
import Link from 'next/link'

interface DashboardChartsProps {
  marketData: any[]
  topAreas: any[]
  isAuthenticated: boolean
  onProtectedAction: (action: string) => void
}

export default function DashboardCharts({
  marketData,
  topAreas,
  isAuthenticated,
  onProtectedAction,
}: DashboardChartsProps) {
  return (
    <>
      {/* Market Volume and Transactions */}
      <Card>
        <CardHeader>
          <CardTitle>נפח עסקאות ושוק</CardTitle>
          <CardDescription>
            {isAuthenticated 
              ? "עסקאות נדלן - נפח שוק חודשי"
              : "נתוני עסקאות ושוק זמינים"
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          {marketData && marketData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={marketData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    name === "transactions" ? value : fmtCurrency(value),
                    name === "transactions" ? "עסקאות + רשימות" : "נפח שוק",
                  ]}
                />
                <Bar
                  yAxisId="left"
                  dataKey="transactions"
                  fill="#8884d8"
                  name="transactions"
                />
                <Bar
                  yAxisId="right"
                  dataKey="volume"
                  fill="#82ca9d"
                  name="volume"
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex flex-col items-center justify-center h-[300px] text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
                <BarChart3 className="h-8 w-8 text-muted-foreground" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-medium text-foreground">
                  {isAuthenticated ? "אין נתוני עסקאות" : "נתוני עסקאות זמינים"}
                </h3>
                <p className="text-sm text-muted-foreground max-w-sm">
                  {isAuthenticated 
                    ? "עדיין אין נתוני עסקאות זמינים במערכת"
                    : "התחבר כדי לראות נתוני עסקאות ונפח שוק מפורטים"
                  }
                </p>
              </div>
              {!isAuthenticated && (
                <Button onClick={() => onProtectedAction("עסקאות")} className="mt-4">
                  <BarChart3 className="h-4 w-4 me-2" />
                  התחבר לצפייה בנתונים
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Top Areas Performance */}
      <Card>
        <CardHeader>
          <CardTitle>ביצועי האזורים המובילים</CardTitle>
          <CardDescription>
            {isAuthenticated 
              ? "האזורים עם הפעילות הגבוהה ביותר"
              : "האזורים עם הפעילות הגבוהה ביותר"
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          {topAreas && topAreas.length > 0 ? (
            <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
              {topAreas.map((area, index) => (
                <Link
                  key={index}
                  href={`/assets?city=${encodeURIComponent(area.area)}`}
                  className="p-4 border rounded-lg hover:shadow-md transition-shadow block"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">{area.area}</h4>
                    <Badge
                      variant={
                        area.trend > 5
                          ? 'default'
                          : area.trend > 3
                          ? 'accent'
                          : 'neutral'
                      }
                    >
                      {area.trend > 0 ? "+" : ""}
                      {area.trend}%
                    </Badge>
                  </div>
                  <div className="text-2xl font-bold">
                    {fmtNumber(area.assets)}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {fmtCurrency(area.avgPrice)} ממוצע
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-[200px] text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
                <BarChart3 className="h-8 w-8 text-muted-foreground" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-medium text-foreground">
                  {isAuthenticated ? "אין נתוני אזורים" : "נתוני אזורים זמינים"}
                </h3>
                <p className="text-sm text-muted-foreground max-w-sm">
                  {isAuthenticated 
                    ? "עדיין אין נתוני אזורים זמינים במערכת"
                    : "התחבר כדי לראות ביצועי אזורים ונתוני פעילות מפורטים"
                  }
                </p>
              </div>
              {!isAuthenticated && (
                <Button onClick={() => onProtectedAction("אזורים")} className="mt-4">
                  <MapPin className="h-4 w-4 me-2" />
                  התחבר לצפייה בנתונים
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </>
  )
}

