'use client'

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { ChevronDown, Home, Building, AlertCircle, Calculator, FileText, BarChart3, User, CreditCard, Settings, LogOut } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import Logo from "@/components/Logo"
import * as Collapsible from "@radix-ui/react-collapsible"

const navigation = [
  {
    name: "בית",
    href: "/",
    icon: Home,
  },
  {
    name: "נכסים",
    href: "/listings",
    icon: Building,
  },
  {
    name: "התראות",
    href: "/alerts", 
    icon: AlertCircle,
  },
  {
    name: "מחשבון משכנתא",
    href: "/mortgage/analyze",
    icon: Calculator,
  },
  {
    name: "דוחות",
    href: "/reports",
    icon: BarChart3
  }
]



interface AppSidebarProps {
  className?: string
  isCollapsed?: boolean
}

export default function AppSidebar({ className, isCollapsed = false }: AppSidebarProps) {
  const pathname = usePathname()

  return (
    <div className={cn(
      "flex h-full flex-col bg-card border-l transition-all duration-300",
      isCollapsed ? "w-16" : "w-64",
      className
    )}>
      {/* Logo */}
      <div className="flex h-16 items-center border-b px-6">
        <Link href="/" className="flex items-center gap-3">
          <Logo variant="symbol" size={28} color="var(--brand-teal)" />
          {!isCollapsed && (
            <span className="text-xl font-bold text-logo-title">נדל״נר</span>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto p-4">
        <nav className="space-y-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            const Icon = item.icon
            
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center justify-between rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground",
                  isActive 
                    ? "bg-accent text-accent-foreground" 
                    : "text-muted-foreground"
                )}
                title={isCollapsed ? item.name : undefined}
              >
                <div className="flex items-center gap-3">
                  <Icon className="h-4 w-4" />
                  {!isCollapsed && <span>{item.name}</span>}
                </div>
              </Link>
            )
          })}
        </nav>

                      <Separator className="my-6" />

              {/* Stats Section */}
              {!isCollapsed && (
                <div className="space-y-4">
                  <h3 className="text-sm font-medium text-muted-foreground">סטטיסטיקות</h3>
                  <div className="space-y-3">
                    <div className="rounded-lg bg-muted p-3">
                      <div className="text-sm font-medium">נכסים פעילים</div>
                      <div className="text-2xl font-bold text-primary">1</div>
                    </div>
                    <div className="rounded-lg bg-muted p-3">
                      <div className="text-sm font-medium">התראות פעילות</div>
                      <div className="text-2xl font-bold text-orange-500">3</div>
                    </div>
                  </div>
                </div>
              )}
      </div>

                  {/* Footer with User Menu */}
            <div className="border-t p-4">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className={cn(
                      "w-full justify-start gap-3 px-2 py-2 h-auto",
                      isCollapsed ? "px-2" : "px-3"
                    )}
                  >
                    <Avatar className="h-8 w-8">
                      <AvatarFallback>משתמש</AvatarFallback>
                    </Avatar>
                    {!isCollapsed && (
                      <div className="flex-1 text-right">
                        <div className="text-sm font-medium">משתמש דמו</div>
                        <div className="text-xs text-muted-foreground">demo@example.com</div>
                      </div>
                    )}
                    {!isCollapsed && <ChevronDown className="h-4 w-4" />}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent 
                  className="w-56" 
                  align={isCollapsed ? "center" : "end"} 
                  side={isCollapsed ? "right" : "top"}
                  forceMount
                >
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">משתמש דמו</p>
                      <p className="text-xs leading-none text-muted-foreground">
                        demo@example.com
                      </p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuGroup>
                    <DropdownMenuItem asChild>
                      <Link href="/profile" className="flex items-center">
                        <User className="ml-2 h-4 w-4" />
                        <span>פרופיל</span>
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link href="/billing" className="flex items-center">
                        <CreditCard className="ml-2 h-4 w-4" />
                        <span>חבילות ותשלומים</span>
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link href="/settings" className="flex items-center">
                        <Settings className="ml-2 h-4 w-4" />
                        <span>הגדרות</span>
                      </Link>
                    </DropdownMenuItem>
                  </DropdownMenuGroup>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem className="text-red-600 focus:text-red-600">
                    <LogOut className="ml-2 h-4 w-4" />
                    <span>התנתק</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
    </div>
  )
}
