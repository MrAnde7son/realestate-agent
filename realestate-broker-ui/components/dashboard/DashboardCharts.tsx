"use client";

import React from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/button";
import { fmtCurrency, fmtNumber } from "@/lib/utils";
import { TrendingUp, Building, BarChart3 } from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
  BarChart,
  Bar,
} from "recharts";

interface MarketDataPoint {
  month: string;
  avgPrice: number;
  transactions?: number;
  volume?: number;
}

interface PropertyTypeDatum {
  type: string;
  count: number;
  percentage?: number;
}

export interface DashboardChartsProps {
  marketData: MarketDataPoint[];
  propertyTypes: PropertyTypeDatum[];
  colors: string[];
  isAuthenticated: boolean;
  onRequireAuth: (feature: string) => void;
}

export default function DashboardCharts({
  marketData,
  propertyTypes,
  colors,
  isAuthenticated,
  onRequireAuth,
}: DashboardChartsProps) {
  const hasMarketData = Array.isArray(marketData) && marketData.length > 0;
  const hasPropertyTypes = Array.isArray(propertyTypes) && propertyTypes.length > 0;

  return (
    <>
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>מגמות שוק - מחירים ממוצעים</CardTitle>
            <CardDescription>
              {isAuthenticated
                ? "מחירים ממוצעים מבוססים על נתוני מודעות למכירה"
                : "מגמות מחירים זמינות במערכת"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {hasMarketData ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={marketData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip
                    formatter={(value: number) => [fmtCurrency(value), "מחיר ממוצע"]}
                    labelFormatter={(label) => `חודש: ${label}`}
                  />
                  <Area type="monotone" dataKey="avgPrice" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
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
                      : "התחבר כדי לראות נתוני שוק מפורטים ומגמות מחירים"}
                  </p>
                </div>
                {!isAuthenticated && (
                  <Button onClick={() => onRequireAuth("שוק")} className="mt-4">
                    <TrendingUp className="h-4 w-4 me-2" />
                    התחבר לצפייה בנתונים
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>התפלגות סוגי נכסים</CardTitle>
            <CardDescription>
              {isAuthenticated ? "חלוקה לפי סוגי נכסים במאגר" : "חלוקה לפי סוגי נכסים זמינים"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {hasPropertyTypes ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={propertyTypes}
                    cx="50%"
                    cy="50%"
                    nameKey="type"
                    labelLine={false}
                    label={({ type, percentage }) => `${type} ${percentage ?? 0}%`}
                    outerRadius={80}
                    dataKey="count"
                  >
                    {propertyTypes.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
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

      <Card>
        <CardHeader>
          <CardTitle>נפח עסקאות ושוק</CardTitle>
          <CardDescription>
            {isAuthenticated ? "עסקאות נדלן - נפח שוק חודשי" : "נתוני עסקאות ושוק זמינים"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {hasMarketData ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={marketData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    name === "transactions" ? fmtNumber(value) : fmtCurrency(value),
                    name === "transactions" ? "עסקאות + רשימות" : "נפח שוק",
                  ]}
                />
                <Bar yAxisId="left" dataKey="transactions" fill="#8884d8" name="transactions" />
                <Bar yAxisId="right" dataKey="volume" fill="#82ca9d" name="volume" />
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
                    : "התחבר כדי לראות נתוני עסקאות ונפח שוק מפורטים"}
                </p>
              </div>
              {!isAuthenticated && (
                <Button onClick={() => onRequireAuth("עסקאות")} className="mt-4">
                  <BarChart3 className="h-4 w-4 me-2" />
                  התחבר לצפייה בנתונים
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </>
  );
}
