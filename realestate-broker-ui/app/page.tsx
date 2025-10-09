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
} from "@/components/ui/Card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/Badge";
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
  Receipt,
  Banknote,
  Heart,
  Share2,
  BarChart3,
} from "lucide-react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/protected-route";
import { useAuth } from "@/lib/auth-context";
import { fmtCurrency, fmtNumber } from "@/lib/utils";
import { useDashboardData } from "@/lib/dashboard";
import { useRouter } from "next/navigation";
import { useState, useEffect, useCallback } from "react";

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
  Legend,
} from "recharts";
import { chartPalette as C } from "@/lib/chart-palette";
import { KpiCard } from "@/components/KpiCard";
import { TrendingUp, FileText, Bell, Building2 } from "lucide-react";
import OnboardingProgress from "@/components/OnboardingProgress";
import OnboardingChecklist from "@/components/OnboardingChecklist";
import { selectOnboardingState, getCompletionPct, isOnboardingComplete } from "@/onboarding/selectors";
import { ALERT_TYPE_LABELS } from "@/lib/alert-constants";
import { api } from "@/lib/api-client";

export default function HomePage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const { data: dashboardData, loading, error } = useDashboardData();
  const router = useRouter();
  const onboardingState = React.useMemo(() => {
    return selectOnboardingState(user);
  }, [user]);
  const [mounted, setMounted] = useState(false);
  
  
  // Alert data state
  const [alertRules, setAlertRules] = useState<any[]>([]);
  const [alertEvents, setAlertEvents] = useState<any[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(false);

  // Fetch alerts data
  const fetchAlerts = useCallback(async () => {
    if (!isAuthenticated) return;
    
    try {
      setAlertsLoading(true);
      
      // Fetch alert rules
      const rulesResponse = await api.get('/api/alerts');
      if (rulesResponse.ok) {
        setAlertRules(rulesResponse.data?.rules || []);
      }
      
      // Fetch recent alert events
      const eventsResponse = await api.get('/api/alerts?since=2024-01-01');
      if (eventsResponse.ok) {
        setAlertEvents(eventsResponse.data?.events || []);
      }
    } catch (err) {
      console.error('Error fetching alerts:', err);
    } finally {
      setAlertsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      fetchAlerts();
    }
  }, [isAuthenticated, fetchAlerts]);

  const handleProtectedAction = (action: string) => {
    if (!isAuthenticated) {
      router.push("/auth?redirect=" + encodeURIComponent("/assets"));
    }
  };

  // Prevent hydration mismatch by not rendering auth-dependent content until mounted
  if (!mounted || authLoading) {
    return (
      <DashboardLayout>
        <DashboardShell>
          <DashboardHeader
            heading="ברוכים הבאים לנדל״נר"
            text="פלטפורמה חכמה מבוססת בינה מלאכותית לניהול נכסים עבור מתווכים, שמאים ומשקיעים"
          />
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          </div>
        </DashboardShell>
      </DashboardLayout>
    );
  }

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

  // Show loading state for authenticated users
  if (isAuthenticated && loading) {
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

  // Show error state for authenticated users
  if (isAuthenticated && error) {
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

  // Show no data state for authenticated users
  if (isAuthenticated && !dashboardData) {
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

  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042"];

  // Only show data if user is authenticated
  const displayData = dashboardData || {
    totalassets: 0,
    activeAlerts: 0,
    totalReports: 0,
    averageReturn: 0,
    marketTrend: 'stable' as const,
    recentActivity: [],
    marketData: [],
    propertyTypes: [],
    topAreas: []
  };

  // Helper function to get alert icon
  const getAlertIcon = (triggerType: string) => {
    switch (triggerType) {
      case 'PRICE_DROP':
        return <TrendingDown className="h-4 w-4 text-red-500" />
      case 'NEW_LISTING':
        return <Home className="h-4 w-4 text-blue-500" />
      case 'MARKET_TREND':
        return <Bell className="h-4 w-4 text-orange-500" />
      case 'DOCS_UPDATE':
        return <FileText className="h-4 w-4 text-purple-500" />
      case 'PERMIT_STATUS':
        return <Building className="h-4 w-4 text-green-500" />
      case 'NEW_GOV_TX':
        return <FileText className="h-4 w-4 text-green-500" />
      case 'LISTING_REMOVED':
        return <TrendingDown className="h-4 w-4 text-gray-500" />
      default:
        return <Bell className="h-4 w-4 text-gray-500" />
    }
  };

  // Helper function to format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) {
      return 'לפני פחות משעה';
    } else if (diffInHours < 24) {
      return `לפני ${diffInHours} שעות`;
    } else if (diffInHours < 48) {
      return 'אתמול';
    } else {
      return date.toLocaleDateString('he-IL');
    }
  };

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

        {isAuthenticated && user?.onboarding_flags && !isOnboardingComplete(onboardingState) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
            <OnboardingProgress state={onboardingState} />
            <OnboardingChecklist state={onboardingState} />
          </div>
        )}

        {/* Login Prompt for Guests */}
        {!isAuthenticated && (
          <div className="bg-blue-50 border border-blue-200 dark:bg-blue-950 dark:border-blue-800 rounded-lg p-4 mb-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="space-y-1">
                <h3 className="font-medium text-blue-900 dark:text-blue-100">
                  התחבר כדי לגשת לכל התכונות
                </h3>
                <p className="text-sm text-blue-700 dark:text-blue-200 mt-1">
                  צור חשבון או התחבר כדי ליצור דוחות, לנתח משכנתאות ולנהל התראות
                </p>
              </div>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-end sm:gap-3">
                <Button
                  onClick={() => router.push("/demo")}
                  variant="outline"
                  className="w-full sm:w-auto"
                >
                  נסה הדגמה
                </Button>
                <Button
                  onClick={() => router.push("/auth")}
                  className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
                >
                  התחבר עכשיו
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-4 items-stretch">
          <KpiCard
            title="סה״כ נכסים"
            value={fmtNumber(displayData.totalassets)}
            icon={<Building2 className="h-5 w-5" />}
            tone="teal"
            href="/assets"
          >
            {isAuthenticated ? "נכסים במערכת" : "נכסים זמינים במערכת"}
          </KpiCard>

          <KpiCard
            title="כללי התראות"
            value={isAuthenticated ? fmtNumber(alertRules.length) : "0"}
            icon={<Bell className="h-5 w-5" />}
            tone="red"
            href={isAuthenticated ? "/alerts" : undefined}
            onClick={!isAuthenticated ? () => handleProtectedAction("התראות") : undefined}
          >
            {isAuthenticated ? (
              alertRules.length > 0 ? (
                <>
                  {alertRules.filter(rule => rule.active).length} פעילים מתוך {alertRules.length} כללי התראות
                  <div className="text-xs text-muted-foreground mt-1">
                    לחץ לניהול התראות
                  </div>
                </>
              ) : (
                <>
                  אין כללי התראות מוגדרים
                  <div className="text-xs text-muted-foreground mt-1">
                    לחץ להגדרת התראות ראשונות
                  </div>
                </>
              )
            ) : (
              <>
                התראות פעילות במערכת
                <div className="text-blue-600 dark:text-blue-400 mt-1">
                  התחבר לניהול התראות
                </div>
              </>
            )}
          </KpiCard>

          <KpiCard
            title="דוחות"
            value={isAuthenticated ? fmtNumber(displayData.totalReports) : "0"}
            icon={<FileText className="h-5 w-5" />}
            tone="blue"
            href={isAuthenticated ? "/reports" : undefined}
            onClick={!isAuthenticated ? () => handleProtectedAction("דוחות") : undefined}
          >
            {isAuthenticated ? "סה״כ דוחות במערכת" : "התחבר לצפייה בדוחות"}
          </KpiCard>

          <KpiCard
            title="ממוצע תשואה"
            value={isAuthenticated ? `${displayData.averageReturn}%` : "0%"}
            icon={<TrendingUp className="h-5 w-5" />}
            tone="green"
            showHoverEffect={false}
          >
            {isAuthenticated ? "ממוצע תשואות נכסים" : "התחבר לצפייה בתשואות"}
          </KpiCard>
        </div>

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
              {displayData.marketData && displayData.marketData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={displayData.marketData}>
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
                    <Button onClick={() => handleProtectedAction("שוק")} className="mt-4">
                      <TrendingUp className="h-4 w-4 mr-2" />
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
              {displayData.propertyTypes && displayData.propertyTypes.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={displayData.propertyTypes}
                      cx="50%"
                      cy="50%"
                      nameKey="type"
                      labelLine={false}
                      label={({ type, percentage }) => `${type} ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {displayData.propertyTypes.map((entry, index) => (
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
                      <Building className="h-4 w-4 mr-2" />
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
            {displayData.marketData && displayData.marketData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={displayData.marketData}>
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
                  <Button onClick={() => handleProtectedAction("עסקאות")} className="mt-4">
                    <BarChart3 className="h-4 w-4 mr-2" />
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
            {displayData.topAreas && displayData.topAreas.length > 0 ? (
              <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
                {displayData.topAreas.map((area, index) => (
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
                  <MapPin className="h-8 w-8 text-muted-foreground" />
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
                  <Button onClick={() => handleProtectedAction("אזורים")} className="mt-4">
                    <MapPin className="h-4 w-4 mr-2" />
                    התחבר לצפייה בנתונים
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Alerts Feed */}
        <Card>
          <CardHeader>
            <CardTitle>התראות אחרונות</CardTitle>
            <CardDescription>
              ההתראות האחרונות שהתקבלו במערכת
            </CardDescription>
          </CardHeader>
          <CardContent>
            {alertsLoading ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 border rounded-lg">
                    <Skeleton className="h-8 w-8 rounded-full" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  </div>
                ))}
              </div>
            ) : alertEvents.length > 0 ? (
              <div className="space-y-4">
                {alertEvents.slice(0, 5).map((alert) => (
                  <div
                    key={alert.id}
                    className={`flex items-center gap-3 p-3 border rounded-lg transition-colors ${
                      alert.delivered_at ? 'bg-muted/50' : 'bg-card hover:bg-muted/50'
                    }`}
                  >
                    <div className="flex-shrink-0">
                      {getAlertIcon(alert.alert_rule.trigger_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className={`font-medium text-sm ${!alert.delivered_at ? 'text-primary' : 'text-muted-foreground'}`}>
                          {ALERT_TYPE_LABELS[alert.alert_rule.trigger_type as keyof typeof ALERT_TYPE_LABELS] || alert.alert_rule.trigger_type_display}
                        </p>
                        {!alert.delivered_at && (
                          <div className="w-2 h-2 bg-blue-500 rounded-full" />
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mb-1">
                        {alert.payload?.message || 'התראה חדשה'}
                      </p>
                      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between sm:gap-2 sm:min-w-0">
                        <p className="text-xs text-muted-foreground order-2 sm:order-1">
                          {formatDate(alert.occurred_at)}
                        </p>
                        {alert.asset_address && (
                          <p className="text-xs text-muted-foreground order-1 sm:order-2 truncate sm:max-w-[60%]" title={alert.asset_address}>
                            📍 {alert.asset_address}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {alertEvents.length > 5 && (
                  <div className="text-center pt-2">
                    <Button variant="outline" size="sm" asChild>
                      <Link href="/alerts">
                        צפה בכל ההתראות
                      </Link>
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                  <Bell className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-medium text-foreground mb-2">אין התראות</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  עדיין לא התקבלו התראות במערכת
                </p>
                <Button asChild>
                  <Link href="/alerts">
                    <Bell className="h-4 w-4 mr-2" />
                    הגדר התראות ראשונות
                  </Link>
                </Button>
              </div>
            )}
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
                  <Banknote className="h-5 w-5 text-green-600" />
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
                    <Banknote className="h-4 w-4 ml-2" />
                    חשב משכנתא
                  </Link>
                </Button>
              ) : (
                <Button
                  onClick={() => handleProtectedAction("mortgage-calculator")}
                  variant="outline"
                  className="w-full mt-4"
                >
                  <Banknote className="h-4 w-4 ml-2" />
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
