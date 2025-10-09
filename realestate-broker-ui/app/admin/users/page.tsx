import { redirect } from "next/navigation"
import DashboardLayout from "@/components/layout/dashboard-layout"
import { DashboardShell, DashboardHeader } from "@/components/layout/dashboard-shell"
import UsersClient from "./UsersClient"

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  "http://127.0.0.1:8000"

async function getMe() {
  try {
    const { cookies } = await import("next/headers")
    const cookieStore = cookies()
    const accessToken = cookieStore.get("access_token")?.value

    if (!accessToken) {
      return { authenticated: false }
    }

    const response = await fetch(`${API_BASE}/api/me`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      cache: "no-store",
    })

    if (!response.ok) {
      return { authenticated: false }
    }

    return response.json()
  } catch (error) {
    console.error("Failed to fetch current user", error)
    return { authenticated: false }
  }
}

export default async function AdminUsersPage() {
  const me = await getMe()

  if (!me?.authenticated || me.role !== "admin") {
    redirect("/")
  }

  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader
          heading="ניהול משתמשים"
          text="צפייה, יצירה וניהול של משתמשי המערכת"
        />
        <UsersClient />
      </DashboardShell>
    </DashboardLayout>
  )
}
