"use client"

import { useMemo } from "react"
import { usePathname } from "next/navigation"
import { baseNavigation } from "./app-sidebar"
import { useAuth } from "@/lib/auth-context"
import { type LucideIcon, CreditCard, LineChart, Settings, User, Users } from "lucide-react"

export type MobileNavigationItem = {
  name: string
  href: string
  icon: LucideIcon
}

const ADDITIONAL_MOBILE_NAVIGATION: MobileNavigationItem[] = [
  { name: "פרופיל", href: "/profile", icon: User },
  { name: "חבילות ותשלומים", href: "/billing", icon: CreditCard },
  { name: "הגדרות", href: "/settings", icon: Settings },
]

const ADMIN_MOBILE_NAVIGATION: MobileNavigationItem[] = [
  { name: "מעקב", href: "/admin/analytics", icon: LineChart },
  { name: "משתמשים", href: "/admin/users", icon: Users },
]

const QUICK_ACCESS_PATHS = ["/assets", "/alerts", "/deals", "/profile", "/mortgage/analyze"] as const

export function isNavigationPathActive(href: string, pathname: string) {
  if (pathname === href) {
    return true
  }

  if (href === "/") {
    return pathname === href
  }

  return pathname.startsWith(`${href}/`)
}

export function useMobileNavigation() {
  const pathname = usePathname()
  const { user } = useAuth()

  const canAccessCrm = useMemo(
    () => ["broker", "appraiser", "admin"].includes(user?.role || ""),
    [user?.role]
  )

  const baseItems = useMemo(() => {
    return baseNavigation
      .filter((item) => item.href !== "/crm" || canAccessCrm)
      .map((item) => ({ ...item }))
  }, [canAccessCrm])

  const items = useMemo(() => {
    const list: MobileNavigationItem[] = [...baseItems, ...ADDITIONAL_MOBILE_NAVIGATION]

    if (user?.role === "admin") {
      list.push(...ADMIN_MOBILE_NAVIGATION)
    }

    const seen = new Set<string>()

    return list.filter((item) => {
      if (seen.has(item.href)) {
        return false
      }
      seen.add(item.href)
      return true
    })
  }, [baseItems, user?.role])

  const activeItem = useMemo(() => {
    const matching = items.filter((item) => isNavigationPathActive(item.href, pathname))
    if (matching.length === 0) {
      return null
    }

    return matching.sort((a, b) => b.href.length - a.href.length)[0]
  }, [items, pathname])

  const quickAccessItems = useMemo(() => {
    const preferred: MobileNavigationItem[] = []
    const seen = new Set<string>()

    for (const path of QUICK_ACCESS_PATHS) {
      const match = items.find((item) => item.href === path)
      if (match && !seen.has(match.href)) {
        preferred.push(match)
        seen.add(match.href)
      }
      if (preferred.length >= 4) {
        break
      }
    }

    if (preferred.length < Math.min(4, items.length)) {
      for (const item of items) {
        if (seen.has(item.href)) {
          continue
        }
        preferred.push(item)
        seen.add(item.href)
        if (preferred.length >= Math.min(4, items.length)) {
          break
        }
      }
    }

    return preferred
  }, [items])

  return {
    items,
    activeItem,
    quickAccessItems,
    pathname,
  }
}
