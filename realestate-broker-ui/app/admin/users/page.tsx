import { redirect } from "next/navigation";
import AdminUsersClient from "./AdminUsersClient";
import DashboardLayout from "@/components/layout/dashboard-layout";
import { DashboardShell, DashboardHeader } from "@/components/layout/dashboard-shell";

// Force dynamic rendering since we use cookies()
export const dynamic = 'force-dynamic';

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

export default async function AdminUsersPage() {
  const me = await getMe();
  if (!me?.authenticated || me.role !== "admin") {
    redirect("/");
  }
  
  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader
          heading="ניהול משתמשים"
          text="ניהול משתמשי המערכת, הרשאות ותפקידים"
        />
        <AdminUsersClient />
      </DashboardShell>
    </DashboardLayout>
  );
}
