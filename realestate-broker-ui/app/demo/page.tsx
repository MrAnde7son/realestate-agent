"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/lib/auth-context"
import { authAPI } from "@/lib/auth"

export default function DemoPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const router = useRouter()
  const { refreshUser } = useAuth()

  const startDemo = async () => {
    try {
      setLoading(true)
      setError("")
      const res = await fetch("/api/demo/start", { method: "POST" })
      if (!res.ok) throw new Error("שגיאה בהתחלת הדמו")
      const data = await res.json()
      authAPI.setTokens(data.access_token, data.refresh_token)
      await refreshUser()
      router.push("/assets")
    } catch (err: any) {
      setError(err.message || "שגיאה בהתחלת הדמו")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[100dvh] flex flex-col items-center justify-center p-4 text-center">
      <h1 className="text-2xl font-bold mb-4">התנסות בדמו</h1>
      <p className="text-muted-foreground mb-6">אין צורך בהרשמה</p>
      {error && <p className="text-destructive mb-4">{error}</p>}
      <Button onClick={startDemo} disabled={loading}>
        {loading ? "מתחיל..." : "התחל דמו"}
      </Button>
    </div>
  )
}
