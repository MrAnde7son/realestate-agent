'use client'

import * as React from "react"
import { Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { ThemeToggle } from "@/components/ui/theme-toggle"
import Logo from "@/components/Logo"
import AppSidebar from "./app-sidebar"
import { GlobalSearch } from "./global-search"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Home, Building, AlertCircle, Calculator, BarChart3, User, CreditCard, Settings, LogOut } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"

interface HeaderProps {
  onToggleSidebar?: () => void
}

// Mobile navigation items
const mobileNavigation = [
  { name: "בית", href: "/", icon: Home },
  { name: "נכסים", href: "/listings", icon: Building },
  { name: "התראות", href: "/alerts", icon: AlertCircle },
  { name: "מחשבון משכנתא", href: "/mortgage/analyze", icon: Calculator },
  { name: "דוחות", href: "/reports", icon: BarChart3 },
  { name: "פרופיל", href: "/profile", icon: User },
  { name: "חבילות ותשלומים", href: "/billing", icon: CreditCard },
  { name: "הגדרות", href: "/settings", icon: Settings },
]

export default function Header({ onToggleSidebar }: HeaderProps) {
  const pathname = usePathname()
  const [mobileSidebarOpen, setMobileSidebarOpen] = React.useState(false)

  // Close mobile sidebar when pathname changes
  React.useEffect(() => {
    setMobileSidebarOpen(false)
  }, [pathname])

  return (
    <header className="flex h-16 items-center justify-between border-b bg-background px-6">
      <div className="flex items-center space-x-4">
        {/* Mobile menu trigger */}
        <Sheet open={mobileSidebarOpen} onOpenChange={setMobileSidebarOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="md:hidden">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="p-0 w-80">
            {/* Mobile Sidebar Content */}
            <div className="flex h-full flex-col bg-card">
              {/* Logo */}
              <div className="flex h-16 items-center border-b px-6">
                <Link href="/" className="flex items-center gap-3" onClick={() => setMobileSidebarOpen(false)}>
                  <Logo variant="symbol" size={28} color="var(--brand-teal)" />
                  <span className="text-xl font-bold text-brand-slate">נדל״נר</span>
                </Link>
              </div>

              {/* Navigation */}
              <div className="flex-1 overflow-y-auto p-4 mobile-sidebar-nav">
                <nav className="space-y-2">
                  {mobileNavigation.map((item) => {
                    const isActive = pathname === item.href
                    const Icon = item.icon
                    
                    return (
                      <Link
                        key={item.name}
                        href={item.href}
                        className={cn(
                          "flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground mobile-nav-item",
                          isActive 
                            ? "bg-accent text-accent-foreground" 
                            : "text-muted-foreground"
                        )}
                        onClick={() => setMobileSidebarOpen(false)}
                      >
                        <Icon className="h-5 w-5" />
                        <span>{item.name}</span>
                      </Link>
                    )
                  })}
                </nav>

                <Separator className="my-6" />

                {/* User Info */}
                <div className="space-y-4">
                  <div className="flex items-center gap-3 rounded-lg bg-muted p-3">
                    <Avatar className="h-10 w-10">
                      <AvatarFallback>משתמש</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="text-sm font-medium">משתמש דמו</div>
                      <div className="text-xs text-muted-foreground">demo@example.com</div>
                    </div>
                  </div>
                  
                  <Button variant="outline" className="w-full justify-start gap-2">
                    <LogOut className="h-4 w-4" />
                    <span>התנתק</span>
                  </Button>
                </div>
              </div>
            </div>
          </SheetContent>
        </Sheet>

        {/* Desktop sidebar toggle */}
        <Button 
          variant="ghost" 
          size="icon" 
          className="hidden md:flex"
          onClick={onToggleSidebar}
        >
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle sidebar</span>
        </Button>

        {/* Global Search */}
        <GlobalSearch />
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <Logo variant="horizontal" size={32} color="var(--brand-teal)" />
          <div className="hidden xl:block text-sm text-muted-foreground">
            נדל״ן חכם לשמאים, מתווכים ומשקיעים
          </div>
        </div>
        <ThemeToggle />
      </div>
    </header>
  )
}
