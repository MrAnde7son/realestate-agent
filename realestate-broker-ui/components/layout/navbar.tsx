"use client"

import Link from "next/link"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from "@/components/ui/sheet"
import { Menu, X } from "lucide-react"
import { useState } from "react"
import { getRouteMatchState, usePersistentPathname } from "@/lib/navigation-state"

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const activePath = usePersistentPathname()

  const navigationItems = [
    { href: "/assets", label: "נכסים" },
    { href: "/alerts", label: "התראות" },
    { href: "/mortgage/analyze", label: "משכנתא" },
    { href: "/deal-expenses", label: "הוצאות" },
  ]

  return (
    <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <nav className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        {/* Logo - Left side */}
        <div className="flex items-center">
          <Link href="/assets" className="flex items-center space-x-2 rtl:space-x-reverse">
            <span className="text-lg sm:text-xl font-bold">🏠 Real Estate Pro</span>
          </Link>
        </div>

        {/* Desktop Navigation - Hidden on mobile and large screens */}
        <div className="hidden md:flex lg:hidden items-center space-x-4 rtl:space-x-reverse">
          {navigationItems.map((item) => {
            const matchState = getRouteMatchState(item.href, activePath)
            const isSelf = matchState === "self"
            const isDescendant = matchState === "descendant"

            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isSelf ? "page" : isDescendant ? "true" : undefined}
                data-active-state={matchState}
                className={cn(
                  "group relative text-sm font-medium transition-colors px-3 py-2 rounded-md",
                  isSelf || isDescendant
                    ? "bg-[var(--brand-teal)]/8 text-[var(--brand-teal)]"
                    : "text-muted-foreground hover:text-[var(--brand-teal)] hover:bg-[var(--brand-teal)]/8",
                  isSelf
                    ? "font-semibold"
                    : isDescendant
                    ? "font-medium text-[var(--brand-teal)]/80"
                    : undefined
                )}
              >
                <span
                  aria-hidden="true"
                  data-active-indicator
                  className={cn(
                    "absolute inset-y-1 rounded-full bg-[var(--brand-teal)] transition-opacity duration-200",
                    "ltr:right-1 rtl:left-1",
                    "w-1",
                    isSelf
                      ? "opacity-100"
                      : isDescendant
                      ? "opacity-60"
                      : "opacity-0"
                  )}
                />
                {item.label}
              </Link>
            )
          })}
        </div>

        {/* Mobile Menu Button */}
        <div className="lg:hidden">
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-10 w-10 p-0"
                aria-label="פתח תפריט ניווט"
              >
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-80 p-0">
              <SheetTitle className="sr-only">תפריט ניווט</SheetTitle>
              <SheetDescription className="sr-only">תפריט ניווט ראשי לאפליקציה</SheetDescription>

              <div className="flex h-full flex-col">
                {/* Mobile Header */}
                <div className="flex h-16 items-center justify-between border-b px-6">
                  <span className="text-lg font-bold">Real Estate Pro</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setMobileMenuOpen(false)}
                    className="h-8 w-8 p-0"
                    aria-label="סגור תפריט"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* Mobile Navigation */}
                <div className="flex-1 overflow-y-auto p-4">
                  <nav className="space-y-2">
                    {navigationItems.map((item) => {
                      const matchState = getRouteMatchState(item.href, activePath)
                      const isSelf = matchState === "self"
                      const isDescendant = matchState === "descendant"

                      return (
                        <Link
                          key={item.href}
                          href={item.href}
                          className={cn(
                            "group relative flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-colors",
                            "min-h-[44px]",
                            isSelf || isDescendant
                              ? "bg-[var(--brand-teal)]/8 text-[var(--brand-teal)]"
                              : "text-muted-foreground hover:text-[var(--brand-teal)] hover:bg-[var(--brand-teal)]/8",
                            isSelf
                              ? "font-semibold"
                              : isDescendant
                              ? "font-medium text-[var(--brand-teal)]/80"
                              : undefined
                          )}
                          onClick={() => setMobileMenuOpen(false)}
                          aria-current={
                            isSelf ? "page" : isDescendant ? "true" : undefined
                          }
                          data-active-state={matchState}
                        >
                          <span
                            aria-hidden="true"
                            data-active-indicator
                            className={cn(
                              "absolute inset-y-1 rounded-full bg-[var(--brand-teal)] transition-opacity duration-200",
                              "ltr:right-1 rtl:left-1",
                              "w-1",
                              isSelf
                                ? "opacity-100"
                                : isDescendant
                                ? "opacity-60"
                                : "opacity-0"
                            )}
                          />
                          {item.label}
                        </Link>
                      )
                    })}
                  </nav>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </nav>
    </div>
  )
}

