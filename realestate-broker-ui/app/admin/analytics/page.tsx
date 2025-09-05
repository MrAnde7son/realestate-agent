import { redirect } from "next/navigation";
import AnalyticsClient from "./AnalyticsClient";

async function getMe() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000"}/api/me`, {
    credentials: "include",
    cache: "no-store",
  });
  if (res.status === 401) return { authenticated: false };
  return res.json();
}

async function getAnalytics() {
  const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
  const [tsRes, topRes] = await Promise.all([
    fetch(`${base}/api/analytics/timeseries`, { credentials: "include", cache: "no-store" }),
    fetch(`${base}/api/analytics/top-failures`, { credentials: "include", cache: "no-store" }),
  ]);
  const series = tsRes.ok ? (await tsRes.json()).series : [];
  const top = topRes.ok ? (await topRes.json()).rows : [];
  return { series, top };
}

export default async function AdminAnalyticsPage() {
  const me = await getMe();
  if (!me?.authenticated || me.role !== "admin") {
    redirect("/");
  }
  const data = await getAnalytics();
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Analytics</h1>
      <AnalyticsClient daily={data.series} topFailures={data.top} />
    </div>
  );
}
