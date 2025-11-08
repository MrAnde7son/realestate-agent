"use client"

import Link from "next/link"
import { cn } from "@/lib/utils"
import { isNavigationPathActive, useMobileNavigation } from "./use-mobile-navigation"

export function MobileBottomNav() {
  const { quickAccessItems, pathname } = useMobileNavigation()

  if (quickAccessItems.length === 0) {
    return null
  }

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-50 border-t border-border bg-background/95 shadow-[0_-4px_12px_rgba(15,23,42,0.08)] backdrop-blur supports-[backdrop-filter]:bg-background/70 md:hidden"
      aria-label="תפריט ניווט תחתון"
    >
      <ul className="mx-auto flex max-w-xl items-stretch justify-between px-2 py-2">
        {quickAccessItems.map((item) => {
          const Icon = item.icon
          const isActive = isNavigationPathActive(item.href, pathname)

          return (
            <li key={item.href} className="flex-1">
              <Link
                href={item.href}
                className={cn(
                  "flex flex-col items-center justify-center gap-1 rounded-xl px-2 py-1 text-xs font-medium transition-colors",
                  isActive
                    ? "text-[var(--brand-teal)]"
                    : "text-muted-foreground hover:text-foreground"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon className={cn("h-5 w-5", isActive ? "text-[var(--brand-teal)]" : "text-foreground/80")}
                />
                <span className="truncate">{item.name}</span>
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
