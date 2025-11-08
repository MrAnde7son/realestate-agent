"use client"

import * as React from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ArrowLeft, ChevronDown, X } from "lucide-react"
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
  const router = useRouter()
  const containerRef = React.useRef<HTMLDivElement>(null)
  const [isCollapsed, setIsCollapsed] = React.useState(false)

  const showBreadcrumbs = React.useCallback(() => {
    setIsCollapsed(false)
    setTimeout(() => {
      containerRef.current?.focus()
    }, 0)
  }, [])

  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "b") {
        event.preventDefault()
        showBreadcrumbs()
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [showBreadcrumbs])

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

  const wrapperClasses = React.useMemo(
    () =>
      cn(
        "sticky top-0 z-40 mb-4",
        className
      ),
    [className]
  )

  const containerClasses =
    "flex items-center justify-between gap-4 rounded-md border bg-background/95 px-3 py-2 shadow-sm outline-none supports-[backdrop-filter]:bg-background/70 supports-[backdrop-filter]:backdrop-blur focus-visible:ring-2 focus-visible:ring-ring"

  if (isCollapsed) {
    return (
      <div className={wrapperClasses}>
        <Button
          variant="outline"
          size="sm"
          onClick={showBreadcrumbs}
          className="flex items-center gap-2"
          aria-label="הצג נתיב ניווט"
        >
          <ChevronDown className="h-4 w-4" />
          הצג נתיב ניווט
        </Button>
      </div>
    )
  }

  return (
    <div className={wrapperClasses}>
      <div
        ref={containerRef}
        tabIndex={-1}
        role="region"
        aria-label="נתיב ניווט"
        className={containerClasses}
      >
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

        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(true)}
          aria-label="הסתר נתיב ניווט"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  </div>
  )
}

