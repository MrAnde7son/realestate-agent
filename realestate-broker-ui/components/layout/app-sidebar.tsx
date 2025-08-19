'use client'

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { ChevronDown, Home, Building, AlertCircle, Calculator, FileText, BarChart3, CreditCard } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import Logo from "@/components/Logo"
import { useSession } from "next-auth/react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

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
  },
  {
    name: "חיוב",
    href: "/billing",
    icon: CreditCard
  }
]

interface AppSidebarProps {
  className?: string
}

export default function AppSidebar({ className }: AppSidebarProps) {
  const pathname = usePathname()
  const { data: session } = useSession()

  return (
    <div className={cn("flex h-full w-64 flex-col bg-card border-l", className)}>
      {/* Logo */}
      <div className="flex h-16 items-center border-b px-6">
        <Link href="/" className="flex items-center gap-3">
          <Logo variant="symbol" size={28} color="var(--brand-teal)" />
          <span className="text-xl font-bold text-brand-slate">נדל״נר</span>
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
                <div className="flex items-center gap-3">
                  <Icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </div>
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
              <div className="text-2xl font-bold text-primary">1</div>
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
        {session?.user ? (
          <div className="flex items-center gap-3">
            <Avatar className="h-8 w-8">
              <AvatarImage src={session.user.image ?? ''} alt={session.user.name ?? ''} />
              <AvatarFallback>{session.user.name?.[0] ?? 'U'}</AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <div className="text-sm font-medium">{session.user.name}</div>
              <div className="text-xs text-muted-foreground">{session.user.email}</div>
            </div>
          </div>
        ) : (
          <Button asChild variant="outline" className="w-full">
            <Link href="/login">התחבר</Link>
          </Button>
        )}
      </div>
    </div>
  )
}
