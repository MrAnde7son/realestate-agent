"use client";

import React from 'react';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { chartPalette as C } from "@/lib/chart-palette";
import { TrendingUp, TrendingDown, AlertTriangle, Activity, Loader2 } from "lucide-react";

interface Props {
  daily: any[];
  topFailures: any[];
}

export default function AnalyticsClient({ daily, topFailures }: Props) {
  const [rechartsModule, setRechartsModule] = React.useState<typeof import('recharts') | null>(null);
  const [chartsError, setChartsError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;

    import('recharts')
      .then(module => {
        if (cancelled) {
          return;
        }
        setRechartsModule(module);
      })
      .catch(error => {
        console.error('Failed to load Recharts library', error);
        if (!cancelled) {
          setChartsError('שגיאה בטעינת תרשימי האנליטיקה');
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const ReResponsiveContainer = rechartsModule?.ResponsiveContainer;
  const ReLineChart = rechartsModule?.LineChart;
  const ReLine = rechartsModule?.Line;
  const ReXAxis = rechartsModule?.XAxis;
  const ReYAxis = rechartsModule?.YAxis;
  const ReTooltip = rechartsModule?.Tooltip;
  const ReLegend = rechartsModule?.Legend;
  const ReCartesianGrid = rechartsModule?.CartesianGrid;
  const ReAreaChart = rechartsModule?.AreaChart;
  const ReArea = rechartsModule?.Area;
  const chartsReady = Boolean(rechartsModule);

  const renderChartLoadingState = (message: string) => (
    <div className="flex h-full flex-col items-center justify-center text-center space-y-3">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );

  const renderChartErrorState = (message: string) => (
    <div className="flex h-full flex-col items-center justify-center text-center space-y-3">
      <AlertTriangle className="h-6 w-6 text-destructive" />
      <p className="text-sm text-destructive">{message}</p>
    </div>
  );

  const getChartStatus = (message: string) => (
    chartsError ? renderChartErrorState(chartsError) : renderChartLoadingState(message)
  );

  if (!daily || !Array.isArray(daily)) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <Activity className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">אין נתוני אנליטיקה זמינים</p>
        </CardContent>
      </Card>
    );
  }

  if (!topFailures || !Array.isArray(topFailures)) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <AlertTriangle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">אין נתוני שגיאות זמינים</p>
        </CardContent>
      </Card>
    );
  }

  // Calculate summary statistics
  const totalUsers = daily.reduce((sum, day) => sum + (day.users || 0), 0);
  const totalAssets = daily.reduce((sum, day) => sum + (day.assets || 0), 0);
  const totalReports = daily.reduce((sum, day) => sum + (day.reports || 0), 0);
  const totalAlerts = daily.reduce((sum, day) => sum + (day.alerts || 0), 0);
  const totalErrors = daily.reduce((sum, day) => sum + (day.errors || 0), 0);
  
  // New engagement metrics
  const totalPageViews = daily.reduce((sum, day) => sum + (day.page_views || 0), 0);
  const totalUniqueVisitors = daily.reduce((sum, day) => sum + (day.unique_visitors || 0), 0);
  const avgSessionDuration = daily.reduce((sum, day) => sum + (day.session_duration_avg || 0), 0) / daily.length;
  const avgBounceRate = daily.reduce((sum, day) => sum + (day.bounce_rate || 0), 0) / daily.length;
  
  // Feature usage metrics
  const totalSearches = daily.reduce((sum, day) => sum + (day.searches_performed || 0), 0);
  const totalMarketingMessages = daily.reduce((sum, day) => sum + (day.marketing_messages_created || 0), 0);
  const totalFilters = daily.reduce((sum, day) => sum + (day.filters_applied || 0), 0);
  const totalExports = daily.reduce((sum, day) => sum + (day.exports_downloaded || 0), 0);
  
  // Performance metrics
  const avgPageLoadTime = daily.reduce((sum, day) => sum + (day.avg_page_load_time || 0), 0) / daily.length;
  const avgApiResponseTime = daily.reduce((sum, day) => sum + (day.api_response_time_avg || 0), 0) / daily.length;
  const avgErrorRate = daily.reduce((sum, day) => sum + (day.error_rate || 0), 0) / daily.length;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">משתמשים</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalUsers.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">משתמשים שנרשמו</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">נכסים</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalAssets.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">נכסים שנוספו</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">דוחות</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalReports.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">דוחות שנוצרו</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">התראות</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-500">{totalAlerts.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">התראות שנוצרו</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">שגיאות</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{totalErrors.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">שגיאות במערכת</p>
          </CardContent>
        </Card>
      </div>

      {/* Engagement Metrics */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">צפיות בדפים</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalPageViews.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">סה&quot;כ צפיות בדפים</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">מבקרים ייחודיים</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalUniqueVisitors.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">משתמשים ייחודיים</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">זמן ממוצע בפגישה</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Math.round(avgSessionDuration / 60)} דקות</div>
            <p className="text-xs text-muted-foreground">זמן ממוצע בפגישה</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">שיעור נטישה</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgBounceRate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">שיעור נטישה ממוצע</p>
          </CardContent>
        </Card>
      </div>

      {/* Feature Usage Metrics */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">חיפושים</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalSearches.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">חיפושים שבוצעו</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">הודעות שיווק</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalMarketingMessages.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">הודעות שיווק שנוצרו</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">סינונים</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalFilters.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">סינונים שהוחלו</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ייצוא</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalExports.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">קבצים שיוצאו</p>
          </CardContent>
        </Card>
      </div>

      {/* Performance Metrics */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">זמן טעינת דף</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgPageLoadTime.toFixed(2)}s</div>
            <p className="text-xs text-muted-foreground">זמן טעינה ממוצע</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">זמן תגובת API</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgApiResponseTime.toFixed(2)}s</div>
            <p className="text-xs text-muted-foreground">זמן תגובה ממוצע</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">שיעור שגיאות</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{avgErrorRate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">שיעור שגיאות ממוצע</p>
          </CardContent>
        </Card>
      </div>

      {/* Activity Chart */}
      <Card>
        <CardHeader>
          <CardTitle>פעילות יומית</CardTitle>
          <CardDescription>נתונים על פעילות המערכת לאורך זמן</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] w-full">
            {chartsReady &&
            ReResponsiveContainer &&
            ReLineChart &&
            ReLine &&
            ReXAxis &&
            ReYAxis &&
            ReTooltip &&
            ReLegend &&
            ReCartesianGrid ? (
              <ReResponsiveContainer width="100%" height="100%">
                <ReLineChart data={daily}>
                  <ReCartesianGrid strokeDasharray="3 3" stroke={C.grid} />
                  <ReXAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => new Date(value).toLocaleDateString('he-IL', { month: 'short', day: 'numeric' })}
                  />
                  <ReYAxis tick={{ fontSize: 12 }} />
                  <ReTooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '6px'
                    }}
                    labelFormatter={(value) => new Date(value).toLocaleDateString('he-IL')}
                  />
                  <ReLegend />
                  <ReLine
                    type="monotone"
                    dataKey="users"
                    stroke={C.series1}
                    strokeWidth={2}
                    name="משתמשים"
                  />
                  <ReLine
                    type="monotone"
                    dataKey="assets"
                    stroke={C.series2}
                    strokeWidth={2}
                    name="נכסים"
                  />
                  <ReLine
                    type="monotone"
                    dataKey="reports"
                    stroke={C.series3}
                    strokeWidth={2}
                    name="דוחות"
                  />
                  <ReLine
                    type="monotone"
                    dataKey="alerts"
                    stroke={C.series4}
                    strokeWidth={2}
                    name="התראות"
                  />
                  <ReLine
                    type="monotone"
                    dataKey="page_views"
                    stroke="#8884d8"
                    strokeWidth={2}
                    name="צפיות בדפים"
                  />
                  <ReLine
                    type="monotone"
                    dataKey="searches_performed"
                    stroke="#82ca9d"
                    strokeWidth={2}
                    name="חיפושים"
                  />
                </ReLineChart>
              </ReResponsiveContainer>
            ) : (
              getChartStatus('טוען תרשים פעילות יומית...')
            )}
          </div>
        </CardContent>
      </Card>

      {/* Error Trends Chart */}
      <Card>
        <CardHeader>
          <CardTitle>מגמות שגיאות</CardTitle>
          <CardDescription>ניתוח שגיאות במערכת לאורך זמן</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] w-full">
            {chartsReady &&
            ReResponsiveContainer &&
            ReAreaChart &&
            ReArea &&
            ReXAxis &&
            ReYAxis &&
            ReTooltip &&
            ReCartesianGrid ? (
              <ReResponsiveContainer width="100%" height="100%">
                <ReAreaChart data={daily}>
                  <defs>
                    <linearGradient id="colorErrors" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--destructive))" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="hsl(var(--destructive))" stopOpacity={0.1} />
                    </linearGradient>
                  </defs>
                  <ReCartesianGrid strokeDasharray="3 3" stroke={C.grid} />
                  <ReXAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => new Date(value).toLocaleDateString('he-IL', { month: 'short', day: 'numeric' })}
                  />
                  <ReYAxis tick={{ fontSize: 12 }} />
                  <ReTooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '6px'
                    }}
                    labelFormatter={(value) => new Date(value).toLocaleDateString('he-IL')}
                  />
                  <ReArea
                    type="monotone"
                    dataKey="errors"
                    stroke="hsl(var(--destructive))"
                    fillOpacity={1}
                    fill="url(#colorErrors)"
                    name="שגיאות"
                  />
                </ReAreaChart>
              </ReResponsiveContainer>
            ) : (
              getChartStatus('טוען תרשים מגמות שגיאות...')
            )}
          </div>
        </CardContent>
      </Card>

      {/* Top Failures Table */}
      <Card>
        <CardHeader>
          <CardTitle>שגיאות נפוצות</CardTitle>
          <CardDescription>רשימת השגיאות הנפוצות ביותר במערכת</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>מקור</TableHead>
                <TableHead>קוד שגיאה</TableHead>
                <TableHead>כמות</TableHead>
                <TableHead>סטטוס</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {topFailures.map((row: any, idx: number) => (
                <TableRow key={idx}>
                  <TableCell className="font-medium">{row.source}</TableCell>
                  <TableCell>
                    <code className="text-xs bg-muted px-2 py-1 rounded">
                      {row.error_code}
                    </code>
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary">
                      {row.count}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge 
                      variant={row.count > 5 ? "destructive" : row.count > 2 ? "default" : "secondary"}
                    >
                      {row.count > 5 ? "גבוה" : row.count > 2 ? "בינוני" : "נמוך"}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
