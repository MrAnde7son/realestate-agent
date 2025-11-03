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
import { BarChart3, MapPin, TrendingUp, Building } from 'lucide-react'
import Link from 'next/link'

interface DashboardChartsProps {
  marketData: any[]
  topAreas: any[]
  propertyTypes: any[]
  isAuthenticated: boolean
  onProtectedAction: (action: string) => void
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042"];

export default function DashboardCharts({
  marketData,
  topAreas,
  propertyTypes,
  isAuthenticated,
  onProtectedAction,
}: DashboardChartsProps) {
  return (
    <>
      {/* Charts Section */}
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        {/* Market Trends Chart */}
        <Card>
          <CardHeader>
            <CardTitle>מגמות שוק - מחירים ממוצעים</CardTitle>
            <CardDescription>
              {isAuthenticated 
                ? "מחירים ממוצעים מבוססים על נתוני מודעות למכירה"
                : "מגמות מחירים זמינות במערכת"
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {marketData && marketData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={marketData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip
                    formatter={(value: number) => [
                      fmtCurrency(value),
                      "מחיר ממוצע",
                    ]}
                    labelFormatter={(label) => `חודש: ${label}`}
                  />
                  <Area
                    type="monotone"
                    dataKey="avgPrice"
                    stroke="#8884d8"
                    fill="#8884d8"
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-[300px] text-center space-y-4">
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
                  <TrendingUp className="h-8 w-8 text-muted-foreground" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-medium text-foreground">
                    {isAuthenticated ? "אין נתוני שוק" : "נתוני שוק זמינים"}
                  </h3>
                  <p className="text-sm text-muted-foreground max-w-sm">
                    {isAuthenticated 
                      ? "עדיין אין נתוני שוק זמינים במערכת"
                      : "התחבר כדי לראות נתוני שוק מפורטים ומגמות מחירים"
                    }
                  </p>
                </div>
                {!isAuthenticated && (
                  <Button onClick={() => onProtectedAction("שוק")} className="mt-4">
                    <TrendingUp className="h-4 w-4 me-2" />
                    התחבר לצפייה בנתונים
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Property Types Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>התפלגות סוגי נכסים</CardTitle>
            <CardDescription>
              {isAuthenticated 
                ? "חלוקה לפי סוגי נכסים במאגר"
                : "חלוקה לפי סוגי נכסים זמינים"
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {propertyTypes && propertyTypes.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={propertyTypes}
                    cx="50%"
                    cy="50%"
                    nameKey="type"
                    labelLine={false}
                    label={({ type, percentage }) => `${type} ${percentage}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {propertyTypes.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-[300px] text-center space-y-4">
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
                  <Building className="h-8 w-8 text-muted-foreground" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-medium text-foreground">אין נתוני נכסים</h3>
                  <p className="text-sm text-muted-foreground max-w-sm">
                    עדיין לא נוספו נכסים למאגר. התחל להוסיף נכסים כדי לראות את התפלגות סוגי הנכסים
                  </p>
                </div>
                <Button asChild className="mt-4">
                  <Link href="/assets">
                    <Building className="h-4 w-4 me-2" />
                    הוסף נכס ראשון
                  </Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

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

