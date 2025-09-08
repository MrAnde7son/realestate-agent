"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  AreaChart,
  Area,
  ResponsiveContainer,
} from "recharts";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { chartPalette as C } from "@/lib/chart-palette";
import { TrendingUp, TrendingDown, AlertTriangle, Activity } from "lucide-react";

interface Props {
  daily: any[];
  topFailures: any[];
}

export default function AnalyticsClient({ daily, topFailures }: Props) {
  // Add safety checks for data
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
  const totalErrors = daily.reduce((sum, day) => sum + (day.errors || 0), 0);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">משתמשים</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalUsers.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">סה&quot;כ משתמשים פעילים</p>
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
            <CardTitle className="text-sm font-medium">שגיאות</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{totalErrors.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">שגיאות במערכת</p>
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
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={daily}>
                <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => new Date(value).toLocaleDateString('he-IL', { month: 'short', day: 'numeric' })}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))', 
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px'
                  }}
                  labelFormatter={(value) => new Date(value).toLocaleDateString('he-IL')}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="users" 
                  stroke={C.series1} 
                  strokeWidth={2}
                  name="משתמשים"
                />
                <Line 
                  type="monotone" 
                  dataKey="assets" 
                  stroke={C.series2} 
                  strokeWidth={2}
                  name="נכסים"
                />
                <Line 
                  type="monotone" 
                  dataKey="reports" 
                  stroke={C.series3} 
                  strokeWidth={2}
                  name="דוחות"
                />
              </LineChart>
            </ResponsiveContainer>
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
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={daily}>
                <defs>
                  <linearGradient id="colorErrors" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--destructive))" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="hsl(var(--destructive))" stopOpacity={0.1} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => new Date(value).toLocaleDateString('he-IL', { month: 'short', day: 'numeric' })}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))', 
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px'
                  }}
                  labelFormatter={(value) => new Date(value).toLocaleDateString('he-IL')}
                />
                <Area 
                  type="monotone" 
                  dataKey="errors" 
                  stroke="hsl(var(--destructive))" 
                  fillOpacity={1} 
                  fill="url(#colorErrors)"
                  name="שגיאות"
                />
              </AreaChart>
            </ResponsiveContainer>
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
