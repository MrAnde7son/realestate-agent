'use client'

import * as React from 'react'
import Link from 'next/link'
import { ChevronLeft, Home } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface BreadcrumbItem {
  label: string
  href?: string
}

export interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  className?: string
  homeHref?: string
}

/**
 * Breadcrumb navigation component
 * Provides navigation context and improves accessibility
 */
export function Breadcrumbs({
  items,
  className,
  homeHref = '/assets',
}: BreadcrumbsProps) {
  if (items.length === 0) return null

  return (
    <nav
      aria-label="ניווט דרך"
      className={cn('flex items-center gap-2 text-sm', className)}
    >
      <ol className="flex items-center gap-2" itemScope itemType="https://schema.org/BreadcrumbList">
        {/* Home link */}
        <li itemProp="itemListElement" itemScope itemType="https://schema.org/ListItem">
          <Link
            href={homeHref}
            className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
            aria-label="דף הבית"
            itemProp="item"
          >
            <Home className="h-4 w-4" aria-hidden="true" />
            <span className="sr-only">דף הבית</span>
          </Link>
          <meta itemProp="position" content="1" />
        </li>

        {/* Breadcrumb items */}
        {items.map((item, index) => {
          const isLast = index === items.length - 1
          const position = index + 2

          return (
            <React.Fragment key={item.href || index}>
              <li
                className="flex items-center gap-2 text-muted-foreground"
                aria-hidden="true"
              >
                <ChevronLeft className="h-4 w-4" />
              </li>
              <li
                itemProp="itemListElement"
                itemScope
                itemType="https://schema.org/ListItem"
                aria-current={isLast ? 'page' : undefined}
              >
                {item.href && !isLast ? (
                  <Link
                    href={item.href}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                    itemProp="item"
                  >
                    <span itemProp="name">{item.label}</span>
                  </Link>
                ) : (
                  <span
                    className={cn(
                      'text-foreground',
                      isLast && 'font-medium'
                    )}
                    itemProp="name"
                  >
                    {item.label}
                  </span>
                )}
                <meta itemProp="position" content={position.toString()} />
              </li>
            </React.Fragment>
          )
        })}
      </ol>
    </nav>
  )
}

