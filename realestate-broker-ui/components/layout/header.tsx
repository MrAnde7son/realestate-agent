'use client'

import * as React from "react"
import { Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from "@/components/ui/sheet"
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
import { useAuth } from "@/lib/auth-context"

interface HeaderProps {
  onToggleSidebar?: () => void
}

// Mobile navigation items
const mobileNavigation = [
  { name: "בית", href: "/", icon: Home },
  { name: "נכסים", href: "/assets", icon: Building },
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
  const { user, logout } = useAuth()

  // Close mobile sidebar when pathname changes
  React.useEffect(() => {
    setMobileSidebarOpen(false)
  }, [pathname])

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  const getUserDisplayName = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name} ${user.last_name}`
    }
    return user?.username || user?.email || 'משתמש'
  }

  const getUserInitials = () => {
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
    <header className="flex h-16 items-center justify-between border-b bg-background px-6">
      {/* Left side - Menu button and search */}
      <div className="flex items-center gap-4">
        <Sheet open={mobileSidebarOpen} onOpenChange={setMobileSidebarOpen}>
          <SheetTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="md:hidden"
              onClick={() => setMobileSidebarOpen(true)}
            >
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-80 p-0">
            {/* Accessibility titles - hidden visually but available to screen readers */}
            <SheetTitle className="sr-only">תפריט ניווט</SheetTitle>
            <SheetDescription className="sr-only">תפריט ניווט ראשי לאפליקציה</SheetDescription>
            
            <div className="flex h-full flex-col">
              {/* Mobile Header */}
              <div className="flex h-16 items-center border-b px-6">
                <Logo variant="symbol" size={28} color="var(--brand-teal)" />
                <span className="ml-3 text-xl font-bold">נדל״נר</span>
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
                      <AvatarFallback>{getUserInitials()}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="text-sm font-medium">{getUserDisplayName()}</div>
                      <div className="text-xs text-muted-foreground">{user?.email || 'demo@example.com'}</div>
                      {user?.company && (
                        <div className="text-xs text-muted-foreground">{user.company}</div>
                      )}
                    </div>
                  </div>
                  
                  <Button 
                    variant="outline" 
                    className="w-full justify-start gap-2"
                    onClick={handleLogout}
                  >
                    <LogOut className="h-4 w-4" />
                    <span>התנתק</span>
                  </Button>
                </div>
              </div>
            </div>
          </SheetContent>
        </Sheet>

        <Link href="/" className="md:hidden" aria-label="עמוד הבית">
          <Logo variant="symbol" size={28} color="var(--brand-teal)" />
        </Link>
        <GlobalSearch />
      </div>

      {/* Right side - Theme toggle and user menu */}
      <div className="flex items-center gap-4">
        <ThemeToggle />
      </div>
    </header>
  )
}
