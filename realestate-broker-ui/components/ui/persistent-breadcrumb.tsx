"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { ArrowLeft, Home, Building, ChevronDown } from "lucide-react"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

export interface PersistentBreadcrumbItemType {
  label: string
  href?: string
  icon?: React.ComponentType<{ className?: string }>
}

export interface TabContextItem {
  value: string
  label: string
  href?: string
}

interface PersistentBreadcrumbProps {
  items: PersistentBreadcrumbItemType[]
  showBackToAssets?: boolean
  tabContext?: {
    currentTab?: string
    tabs: TabContextItem[]
    onTabChange?: (value: string) => void
  }
  className?: string
}

export function PersistentBreadcrumb({
  items,
  showBackToAssets = false,
  tabContext,
  className,
}: PersistentBreadcrumbProps) {
  const pathname = usePathname()
  const router = useRouter()

  const handleTabChange = (value: string) => {
    if (tabContext?.onTabChange) {
      tabContext.onTabChange(value)
    } else if (tabContext) {
      const tab = tabContext.tabs.find((t) => t.value === value)
      if (tab?.href) {
        router.push(tab.href)
      } else {
        // Update URL with tab parameter
        const url = new URL(window.location.href)
        url.searchParams.set("tab", value)
        router.push(`${url.pathname}${url.search}`)
      }
    }
  }

  const currentTab = tabContext?.tabs.find((t) => t.value === tabContext.currentTab)

  return (
    <div className={cn("flex items-center justify-between gap-4 mb-4", className)}>
      <Breadcrumb>
        <BreadcrumbList>
          {items.map((item, index) => {
            const isLast = index === items.length - 1
            const Icon = item.icon

            return (
              <React.Fragment key={index}>
                {index > 0 && <BreadcrumbSeparator />}
                <BreadcrumbItem>
                  {isLast ? (
                    <BreadcrumbPage className="flex items-center gap-1">
                      {Icon && <Icon className="h-4 w-4" />}
                      {item.label}
                    </BreadcrumbPage>
                  ) : item.href ? (
                    <BreadcrumbLink href={item.href} className="flex items-center gap-1">
                      {Icon && <Icon className="h-4 w-4" />}
                      {item.label}
                    </BreadcrumbLink>
                  ) : (
                    <span className="flex items-center gap-1 text-muted-foreground">
                      {Icon && <Icon className="h-4 w-4" />}
                      {item.label}
                    </span>
                  )}
                </BreadcrumbItem>
              </React.Fragment>
            )
          })}
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex items-center gap-2 flex-shrink-0">
        {tabContext && tabContext.tabs.length > 1 && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2">
                {currentTab?.label || "בחר קטגוריה"}
                <ChevronDown className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {tabContext.tabs.map((tab) => (
                <DropdownMenuItem
                  key={tab.value}
                  onClick={() => handleTabChange(tab.value)}
                  className={cn(
                    tab.value === tabContext.currentTab && "bg-accent"
                  )}
                >
                  {tab.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {showBackToAssets && (
          <Button variant="ghost" size="sm" asChild>
            <Link href="/assets" className="flex items-center gap-1">
              <ArrowLeft className="h-4 w-4 rtl:rotate-180" />
              חזרה לנכסים
            </Link>
          </Button>
        )}
      </div>
    </div>
  )
}

