import { redirect } from "next/navigation";
import dynamic from "next/dynamic";
import DashboardLayout from "@/components/layout/dashboard-layout";
import { DashboardShell, DashboardHeader } from "@/components/layout/dashboard-shell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Loader2 } from "lucide-react";

const AnalyticsClient = dynamic(() => import("./AnalyticsClient"), {
  ssr: false,
  loading: () => (
    <Card>
      <CardHeader>
        <CardTitle>טוען אנליטיקות...</CardTitle>
        <CardDescription>אנא המתן בזמן שאנחנו טוענים את נתוני המערכת</CardDescription>
      </CardHeader>
      <CardContent className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </CardContent>
    </Card>
  ),
});

export const dynamic = "force-dynamic";

async function getMe() {
  try {
    // Get the access token from cookies (similar to middleware)
    const { cookies } = await import('next/headers');
    const cookieStore = await cookies();
    const accessToken = cookieStore.get('access_token')?.value;
    
    if (!accessToken) {
      console.log("No access token found in cookies");
      return { authenticated: false };
    }
    
    const res = await fetch(`${process.env.BACKEND_URL || "http://127.0.0.1:8000"}/api/me`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      cache: "no-store",
    });
    
    if (res.status === 401) return { authenticated: false };
    return res.json();
  } catch (error) {
    console.error("Error fetching user data:", error);
    return { authenticated: false };
  }
}

async function getAnalytics() {
  const base = process.env.BACKEND_URL || "http://127.0.0.1:8000";
  try {
    // Get the access token from cookies
    const { cookies } = await import('next/headers');
    const cookieStore = await cookies();
    const accessToken = cookieStore.get('access_token')?.value;
    
    if (!accessToken) {
      console.log("No access token found for analytics");
      return { series: [], top: [] };
    }
    
    const headers = {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    };
    
    const [tsRes, topRes] = await Promise.all([
      fetch(`${base}/api/analytics/timeseries`, { headers, cache: "no-store" }),
      fetch(`${base}/api/analytics/top-failures`, { headers, cache: "no-store" }),
    ]);
    const series = tsRes.ok ? (await tsRes.json()).series : [];
    const top = topRes.ok ? (await topRes.json()).rows : [];
    return { series, top };
  } catch (error) {
    console.error("Error fetching analytics data:", error);
    return { series: [], top: [] };
  }
}

export default async function AdminAnalyticsPage() {
  const me = await getMe();
  if (!me?.authenticated || me.role !== "admin") {
    redirect("/");
  }
  const data = await getAnalytics();
  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader
          heading="מעקב ואנליטיקה"
          text="נתונים וסטטיסטיקות על פעילות המערכת"
        />
        <AnalyticsClient daily={data.series} topFailures={data.top} />
      </DashboardShell>
    </DashboardLayout>
  );
}
