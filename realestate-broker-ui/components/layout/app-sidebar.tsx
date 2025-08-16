'use client'

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { ChevronDown, Home, Building, AlertCircle, Calculator, FileText, BarChart3 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import * as Collapsible from "@radix-ui/react-collapsible"

const navigation = [
  {
    name: "דשבורד",
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
    name: "משכנתא",
    href: "/mortgage/analyze",
    icon: Calculator,
  },
  {
    name: "דוחות",
    href: "/reports",
    icon: BarChart3,
    badge: "בקרוב"
  }
]

interface AppSidebarProps {
  className?: string
}

export default function AppSidebar({ className }: AppSidebarProps) {
  const pathname = usePathname()

  return (
    <div className={cn("flex h-full w-64 flex-col bg-card border-r", className)}>
      {/* Logo */}
      <div className="flex h-16 items-center border-b px-6">
        <Link href="/" className="flex items-center space-x-2">
          <Building className="h-6 w-6 text-primary" />
          <span className="text-xl font-bold">Real Estate Pro</span>
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
              >
                <div className="flex items-center space-x-3">
                  <Icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span className="rounded-full bg-primary px-2 py-0.5 text-xs text-primary-foreground">
                    {item.badge}
                  </span>
                )}
              </Link>
            )
          })}
        </nav>

        <Separator className="my-6" />

        {/* Stats Section */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-muted-foreground">סטטיסטיקות</h3>
          <div className="space-y-3">
            <div className="rounded-lg bg-muted p-3">
              <div className="text-sm font-medium">נכסים פעילים</div>
              <div className="text-2xl font-bold text-primary">5</div>
            </div>
            <div className="rounded-lg bg-muted p-3">
              <div className="text-sm font-medium">התראות פעילות</div>
              <div className="text-2xl font-bold text-orange-500">3</div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t p-4">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-full bg-primary" />
          <div className="flex-1">
            <div className="text-sm font-medium">משתמש דמו</div>
            <div className="text-xs text-muted-foreground">demo@example.com</div>
          </div>
        </div>
      </div>
    </div>
  )
}
