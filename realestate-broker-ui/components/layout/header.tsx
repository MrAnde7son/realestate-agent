'use client'

import * as React from "react"
import { Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from "@/components/ui/sheet"
import { ThemeToggle } from "@/components/ui/theme-toggle"
import Logo from "@/components/Logo"
import { baseNavigation } from "./app-sidebar"
import { GlobalSearch } from "./global-search"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { User, Users, CreditCard, Settings, LogOut, LineChart, LogIn } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
import { useAuth } from "@/lib/auth-context"
import { getRouteMatchState, usePersistentPathname } from "@/lib/navigation-state"
import { Badge } from "@/components/ui/Badge"

interface HeaderProps {
  onToggleSidebar?: () => void
}

// Mobile navigation items
const baseMobileNavigation = baseNavigation.map((item) => ({ ...item }))
const additionalMobileNavigation = [
  { name: "פרופיל", href: "/profile", icon: User },
  // { name: "חבילות ותשלומים", href: "/billing", icon: CreditCard },
  { name: "הגדרות", href: "/settings", icon: Settings },
]
const mobileNavigation = [...baseMobileNavigation, ...additionalMobileNavigation]

export default function Header({ onToggleSidebar }: HeaderProps) {
  const activePath = usePersistentPathname()
  const [mobileSidebarOpen, setMobileSidebarOpen] = React.useState(false)
  const [mounted, setMounted] = React.useState(false)
  const { user, logout, isAuthenticated, isLoading } = useAuth()
  const canAccessCrm = ['broker', 'appraiser', 'admin'].includes(user?.role || '')
  const canAccessAlertsAndReports = ['broker', 'admin'].includes(user?.role || '')
  const filteredMobileNavigation = mobileNavigation
    .filter((item) => item.href !== '/crm' || canAccessCrm)
    .filter((item) => {
      if (item.href === '/alerts' || item.href === '/reports') {
        return canAccessAlertsAndReports
      }
      return true
    })
  
  // Add admin navigation items for mobile
  if (user?.role === 'admin') {
    filteredMobileNavigation.push(
      { name: "מעקב", href: "/admin/analytics", icon: LineChart },
      { name: "משתמשים", href: "/admin/users", icon: Users }
    )
  }

  // Close mobile sidebar when pathname changes
  React.useEffect(() => {
    setMobileSidebarOpen(false)
  }, [activePath])

  // Prevent hydration mismatch
  React.useEffect(() => {
    setMounted(true)
  }, [])

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  const getUserDisplayName = () => {
    if (!mounted) return 'משתמש'
    if (user?.first_name && user?.last_name) {
      return `${user.first_name} ${user.last_name}`
    }
    return user?.username || user?.email || 'משתמש'
  }

  const getUserInitials = () => {
    if (!mounted) return 'מ'
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`
    }
    if (user?.username) {
      return user.username.substring(0, 2).toUpperCase()
    }
    if (user?.email) {
      return user.email.substring(0, 2).toUpperCase()
    }
    return 'משתמש'
  }

  return (
    <header className="fixed top-0 inset-x-0 z-50 flex h-16 items-center justify-between bg-background px-4 sm:px-6 shadow-md">
      {/* Right side - Menu button, logo and company name (RTL layout) */}
      <div className="flex items-center gap-2 sm:gap-3 md:gap-4">
        {/* Mobile hamburger menu */}
        <Sheet open={mobileSidebarOpen} onOpenChange={setMobileSidebarOpen}>
          <SheetTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="lg:hidden h-10 w-10 p-0"
              onClick={() => setMobileSidebarOpen(true)}
              aria-label="פתח תפריט ניווט"
            >
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent
            side="right"
            className="w-[min(320px,calc(100vw-1.5rem))] sm:w-96 p-0"
          >
            {/* Accessibility titles - hidden visually but available to screen readers */}
            <SheetTitle className="sr-only">תפריט ניווט</SheetTitle>
            <SheetDescription className="sr-only">תפריט ניווט ראשי לאפליקציה</SheetDescription>
            
            <div className="flex h-full flex-col">
              {/* Mobile Header */}
              <div className="flex h-16 items-center justify-between px-6">
                <div className="flex items-center gap-3">
                  <Logo variant="symbol" size={28} color="var(--brand-teal)" />
                  <span className="text-lg font-bold">נדל״נר</span>
                </div>
              </div>

              {/* Navigation */}
              <div className="flex-1 overflow-y-auto p-4 mobile-sidebar-nav">

                <nav className="space-y-2">
                  {filteredMobileNavigation.map((item) => {
                    const matchState = getRouteMatchState(item.href, activePath)
                    const isSelf = matchState === 'self'
                    const isDescendant = matchState === 'descendant'
                    const Icon = item.icon

                    return (
                      <Link
                        key={item.name}
                        href={item.href}
                        className={cn(
                          "group relative flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-colors mobile-nav-item",
                          "min-h-[44px]", // Ensure 44px touch target
                          isSelf || isDescendant
                            ? "bg-[var(--brand-teal)]/8 text-[var(--brand-teal)]"
                            : "text-muted-foreground hover:text-[var(--brand-teal)] hover:bg-[var(--brand-teal)]/8",
                          isSelf
                            ? "font-semibold"
                            : isDescendant
                            ? "font-medium text-[var(--brand-teal)]/80"
                            : undefined
                        )}
                        onClick={() => setMobileSidebarOpen(false)}
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
                        <Icon className="h-5 w-5 flex-shrink-0" />
                        <span className="truncate">{item.name}</span>
                      </Link>
                    )
                  })}
                </nav>

                <Separator className="my-6" />

                {/* User Info */}
                {!isLoading && isAuthenticated && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 rounded-lg bg-muted p-3">
                      <Avatar className="h-10 w-10 flex-shrink-0">
                        <AvatarFallback>{getUserInitials()}</AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">{getUserDisplayName()}</div>
                        <div className="text-xs text-muted-foreground truncate">{user?.email || 'demo@example.com'}</div>
                        {user?.company && (
                          <div className="text-xs text-muted-foreground truncate">{user.company}</div>
                        )}
                      </div>
                    </div>
                    
                    <Button 
                      variant="outline" 
                      className="w-full justify-start gap-2 min-h-[44px]"
                      onClick={handleLogout}
                    >
                      <LogOut className="h-4 w-4 flex-shrink-0" />
                      <span>התנתק</span>
                    </Button>
                  </div>
                )}
                {!isLoading && !isAuthenticated && (
                  <div className="px-2">
                    <Button 
                      asChild 
                      variant="default" 
                      className="w-full min-h-[44px] bg-[var(--brand-teal)] text-white hover:bg-[var(--brand-teal)]/90 shadow-sm"
                    >
                      <Link href="/auth" className="flex items-center justify-center gap-2 w-full">
                        <LogIn className="h-4 w-4" />
                        <span className="w-full text-center">התחבר</span>
                      </Link>
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </SheetContent>
        </Sheet>

        {/* Desktop hamburger menu for sidebar toggle */}
        <Button
          variant="ghost"
          size="sm"
          className="hidden md:flex h-10 w-10 p-0"
          onClick={onToggleSidebar}
          aria-label="הצג/הסתר תפריט צדדי"
        >
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle sidebar</span>
        </Button>

        <div className="flex items-center gap-2 sm:gap-3">
          <Link
            href="/assets"
            aria-label="עמוד הנכסים"
            className="flex items-center gap-2 min-h-[44px]"
          >
            <div className="sm:hidden">
              <Logo variant="symbol" size={24} color="var(--brand-teal)" />
            </div>
            <div className="hidden sm:block">
              <Logo variant="symbol" size={28} color="var(--brand-teal)" />
            </div>
            <span className="text-sm font-semibold text-foreground whitespace-nowrap sm:text-base md:text-lg">
              נדל״נר
            </span>
          </Link>
          <Badge variant="info" size="sm" className="rounded-md font-semibold text-[13px] leading-none">
            בהרצה
          </Badge>
        </div>
      </div>

      {/* Left side - Global search and theme toggle (enforced LTR for alignment) */}
      <div id="search" className="flex items-center gap-2 sm:gap-3 md:gap-4" dir="ltr">
        <div className="hidden sm:block">
          <GlobalSearch />
        </div>
        <ThemeToggle />
      </div>
    </header>
  )
}
