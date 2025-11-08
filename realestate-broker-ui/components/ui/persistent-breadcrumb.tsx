"use client"

import * as React from "react"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Button } from "@/components/ui/button"
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
  return (
    <div className={cn("flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-4 mb-4", className)}>
      <Breadcrumb className="flex-1 min-w-0">
        <BreadcrumbList className="flex-wrap">
          {items.map((item, index) => {
            const isLast = index === items.length - 1
            const Icon = item.icon
            const shouldHideOnMobile = items.length > 3 && index > 0 && index < items.length - 2
            const showEllipsisBefore = items.length > 3 && index === items.length - 2

            return (
              <React.Fragment key={index}>
                {index > 0 && <BreadcrumbSeparator className={cn(
                  shouldHideOnMobile && "hidden sm:block"
                )} />}
                {/* Show ellipsis on mobile before last 2 items */}
                {showEllipsisBefore && (
                  <>
                    <BreadcrumbSeparator className="sm:hidden" />
                    <BreadcrumbItem className="sm:hidden">
                      <span className="text-muted-foreground text-xs">...</span>
                    </BreadcrumbItem>
                  </>
                )}
                <BreadcrumbItem className={cn(
                  "max-w-[200px] sm:max-w-none",
                  shouldHideOnMobile && "hidden sm:inline-flex"
                )}>
                  {isLast ? (
                    <BreadcrumbPage className="flex items-center gap-1 truncate">
                      {Icon && <Icon className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" />}
                      <span className="truncate text-xs sm:text-sm">{item.label}</span>
                    </BreadcrumbPage>
                  ) : item.href ? (
                    <BreadcrumbLink href={item.href} className="flex items-center gap-1 truncate">
                      {Icon && <Icon className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" />}
                      <span className="truncate text-xs sm:text-sm">{item.label}</span>
                    </BreadcrumbLink>
                  ) : (
                    <span className="flex items-center gap-1 text-muted-foreground truncate">
                      {Icon && <Icon className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" />}
                      <span className="truncate text-xs sm:text-sm">{item.label}</span>
                    </span>
                  )}
                </BreadcrumbItem>
              </React.Fragment>
            )
          })}
        </BreadcrumbList>
      </Breadcrumb>

      {showBackToAssets && (
        <div className="flex items-center gap-2 flex-shrink-0">
          <Button variant="ghost" size="sm" asChild className="h-8 sm:h-9">
            <Link href="/assets" className="flex items-center gap-1">
              <ArrowLeft className="h-4 w-4 rtl:rotate-180" />
              <span className="hidden sm:inline">חזרה לנכסים</span>
            </Link>
          </Button>
        </div>
      )}
    </div>
  )
}

