"use client";

import React from "react";
import DashboardLayout from "@/components/layout/dashboard-layout";
import {
  DashboardShell,
  DashboardHeader,
} from "@/components/layout/dashboard-shell";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Calculator,
  Building,
  AlertCircle,
  Users,
  MapPin,
  Clock,
  DollarSign,
  Home,
  Car,
  TrendingDown,
  Eye,
  Heart,
  Share2,
} from "lucide-react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/protected-route";
import { useAuth } from "@/lib/auth-context";
import { fmtCurrency, fmtNumber } from "@/lib/utils";
import { useDashboardData } from "@/lib/dashboard";
import { useRouter } from "next/navigation";

import {
  LineChart,
  Line,
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
} from "recharts";
import { chartPalette as C } from "@/lib/chart-palette";
import { KpiCard } from "@/components/KpiCard";
import { TrendingUp, FileText, Bell, Building2 } from "lucide-react";

export default function HomePage() {
  const { user, isAuthenticated } = useAuth();
  const { data: dashboardData, loading, error } = useDashboardData();
  const router = useRouter();

  const handleProtectedAction = (action: string) => {
    if (!isAuthenticated) {
      router.push(
        "/auth?redirect=" + encodeURIComponent(window.location.pathname)
      );
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <DashboardShell>
          <DashboardHeader
            heading="ברוכים הבאים לנדל״נר"
            text="פלטפורמה חכמה מבוססת בינה מלאכותית לניהול נכסים עבור מתווכים, שמאים ומשקיעים"
          />
          <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Card key={i}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-4" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-16 mb-2" />
                  <Skeleton className="h-4 w-24" />
                </CardContent>
              </Card>
            ))}
          </div>
        </DashboardShell>
      </DashboardLayout>
    );
  }

  if (!dashboardData) {
    return (
      <DashboardLayout>
        <DashboardShell>
          <DashboardHeader
            heading="ברוכים הבאים לנדל״נר"
            text="פלטפורמה חכמה מבוססת בינה מלאכותית לניהול נכסים עבור מתווכים, שמאים ומשקיעים"
          />
          <div className="text-center py-12">
            <p className="text-muted-foreground">
              לא ניתן לטעון נתוני לוח הבקרה
            </p>
          </div>
        </DashboardShell>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <DashboardShell>
          <DashboardHeader
            heading="ברוכים הבאים לנדל״נר"
            text="פלטפורמה חכמה מבוססת בינה מלאכותית לניהול נכסים עבור מתווכים, שמאים ומשקיעים"
          />
          <div className="text-center py-12">
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg max-w-md mx-auto">
              <p className="font-medium mb-2">שגיאה בטעינת נתונים</p>
              <p className="text-sm">{error}</p>
              <Button
                onClick={() => window.location.reload()}
                variant="outline"
                className="mt-4"
              >
                נסה שוב
              </Button>
            </div>
          </div>
        </DashboardShell>
      </DashboardLayout>
    );
  }

  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042"];

  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader
          heading={
            isAuthenticated
              ? `ברוכים הבאים, ${user?.first_name || "משתמש"}!`
              : "ברוכים הבאים לנדל״נר"
          }
          text="פלטפורמה חכמה מבוססת בינה מלאכותית לניהול נכסים עבור מתווכים, שמאים ומשקיעים"
        />

        {/* Login Prompt for Guests */}
        {!isAuthenticated && (
          <div className="bg-blue-50 border border-blue-200 dark:bg-blue-950 dark:border-blue-800 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium text-blue-900 dark:text-blue-100">
                  התחבר כדי לגשת לכל התכונות
                </h3>
                <p className="text-sm text-blue-700 dark:text-blue-200 mt-1">
                  צור חשבון או התחבר כדי ליצור דוחות, לנתח משכנתאות ולנהל התראות
                </p>
              </div>
              <Button
                onClick={() => router.push("/auth")}
                className="bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
              >
                התחבר עכשיו
              </Button>
            </div>
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
          <KpiCard
            title="סה״כ נכסים"
            value={fmtNumber(dashboardData.totalassets)}
            icon={<Building2 className="h-5 w-5" />}
            tone="teal"
            href="/assets"
          >
            נכסים במערכת
          </KpiCard>

          <KpiCard
            title="התראות פעילות"
            value={fmtNumber(dashboardData.activeAlerts)}
            icon={<Bell className="h-5 w-5" />}
            tone="red"
            href="/alerts"
          >
            התראות פעילות במערכת
            {!isAuthenticated && (
              <div className="text-blue-600 dark:text-blue-400 mt-1">
                התחבר לניהול התראות
              </div>
            )}
          </KpiCard>

          <KpiCard
            title="דוחות"
            value={fmtNumber(dashboardData.totalReports)}
            icon={<FileText className="h-5 w-5" />}
            tone="blue"
            href="/reports"
          >
            סה״כ דוחות במערכת
            {!isAuthenticated && (
              <div className="text-blue-600 dark:text-blue-400 mt-1">
                התחבר לצפייה בדוחות
              </div>
            )}
          </KpiCard>

          <KpiCard
            title="ממוצע תשואה"
            value={`${dashboardData.averageReturn}%`}
            icon={<TrendingUp className="h-5 w-5" />}
            tone="green"
            showHoverEffect={false}
          >
            ממוצע תשואות נכסים
          </KpiCard>
        </div>

        {/* Charts Section */}
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
          {/* Market Trends Chart */}
          <Card>
            <CardHeader>
              <CardTitle>מגמות שוק - מחירים ממוצעים</CardTitle>
              <CardDescription>
                שינויי מחירים לאורך 6 החודשים האחרונים
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={dashboardData.marketData}>
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
            </CardContent>
          </Card>

          {/* Property Types Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>התפלגות סוגי נכסים</CardTitle>
              <CardDescription>חלוקה לפי סוגי נכסים במאגר</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={dashboardData.propertyTypes}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ type, percentage }) => `${type} ${percentage}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {dashboardData.propertyTypes.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => [value, "כמות"]} />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Market Volume and Transactions */}
        <Card>
          <CardHeader>
            <CardTitle>נפח עסקאות ושוק</CardTitle>
            <CardDescription>סך העסקאות ונפח השוק החודשי</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={dashboardData.marketData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    name === "transactions" ? value : fmtCurrency(value),
                    name === "transactions" ? "עסקאות" : "נפח שוק",
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
          </CardContent>
        </Card>

        {/* Top Areas Performance */}
        <Card>
          <CardHeader>
            <CardTitle>ביצועי האזורים המובילים</CardTitle>
            <CardDescription>האזורים עם הפעילות הגבוהה ביותר</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
              {dashboardData.topAreas.map((area, index) => (
                <div
                  key={index}
                  className="p-4 border rounded-lg hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">{area.area}</h4>
                    <Badge
                      variant={
                        area.trend > 5
                          ? "default"
                          : area.trend > 3
                          ? "secondary"
                          : "outline"
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
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity Feed */}
        <Card>
          <CardHeader>
            <CardTitle>פעילות אחרונה</CardTitle>
            <CardDescription>
              הפעילויות והעדכונים האחרונים במערכת
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData.recentActivity.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-2 rounded-full ${
                        activity.type === "asset"
                          ? "bg-blue-100 text-blue-600"
                          : activity.type === "alert"
                          ? "bg-orange-100 text-orange-600"
                          : activity.type === "client"
                          ? "bg-green-100 text-green-600"
                          : "bg-purple-100 text-purple-600"
                      }`}
                    >
                      {activity.type === "asset" ? (
                        <Building className="h-4 w-4" />
                      ) : activity.type === "alert" ? (
                        <AlertCircle className="h-4 w-4" />
                      ) : activity.type === "client" ? (
                        <Users className="h-4 w-4" />
                      ) : (
                        <DollarSign className="h-4 w-4" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium">{activity.title}</p>
                      <p className="text-sm text-muted-foreground">
                        {new Date(activity.timestamp).toLocaleString("he-IL")}
                      </p>
                    </div>
                  </div>
                  {activity.value && (
                    <div className="text-right">
                      <div className="font-medium">
                        {fmtCurrency(activity.value)}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Building className="h-5 w-5 text-blue-600" />
                </div>
                <CardTitle className="text-lg">הוסף נכס חדש</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription>
                הוסף נכס חדש למאגר שלך עם כל הפרטים והתמונות
              </CardDescription>
              {isAuthenticated ? (
                <Button asChild className="w-full mt-4">
                  <Link href="/assets">
                    <Building className="h-4 w-4 ml-2" />
                    הוסף נכס
                  </Link>
                </Button>
              ) : (
                <Button
                  onClick={() => handleProtectedAction("assets")}
                  className="w-full mt-4"
                >
                  <Building className="h-4 w-4 ml-2" />
                  התחבר להוספת נכס
                </Button>
              )}
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <AlertCircle className="h-5 w-5 text-orange-600" />
                </div>
                <CardTitle className="text-lg">צור התראה חדשה</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription>
                הגדר התראה מותאמת אישית וקבל התראות על הזדמנויות בשוק
              </CardDescription>
              {isAuthenticated ? (
                <Button asChild variant="outline" className="w-full mt-4">
                  <Link href="/alerts">
                    <AlertCircle className="h-4 w-4 ml-2" />
                    צור התראה
                  </Link>
                </Button>
              ) : (
                <Button
                  onClick={() => handleProtectedAction("create-alert")}
                  variant="outline"
                  className="w-full mt-4"
                >
                  <AlertCircle className="h-4 w-4 ml-2" />
                  התחבר ליצירת התראה
                </Button>
              )}
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Calculator className="h-5 w-5 text-green-600" />
                </div>
                <CardTitle className="text-lg">מחשבון משכנתא</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription>
                חשב משכנתאות ובדוק זכאות עם נתוני בנק ישראל בזמן אמת
              </CardDescription>
              {isAuthenticated ? (
                <Button asChild variant="outline" className="w-full mt-4">
                  <Link href="/mortgage/analyze">
                    <Calculator className="h-4 w-4 ml-2" />
                    חשב משכנתא
                  </Link>
                </Button>
              ) : (
                <Button
                  onClick={() => handleProtectedAction("mortgage-calculator")}
                  variant="outline"
                  className="w-full mt-4"
                >
                  <Calculator className="h-4 w-4 ml-2" />
                  התחבר למחשבון
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      </DashboardShell>
    </DashboardLayout>
  );
}
