'use client'

import * as React from 'react'
import Link from 'next/link'
import { cn } from '@/lib/utils'

export interface SkipLink {
  href: string
  label: string
}

export interface SkipLinksProps {
  links?: SkipLink[]
  className?: string
}

const DEFAULT_SKIP_LINKS: SkipLink[] = [
  { href: '#main-content', label: 'דלג לתוכן הראשי' },
  { href: '#navigation', label: 'דלג לניווט' },
  { href: '#search', label: 'דלג לחיפוש' },
]

/**
 * Skip links for keyboard navigation accessibility
 * Allows users to skip to main content areas
 */
export function SkipLinks({ links = DEFAULT_SKIP_LINKS, className }: SkipLinksProps) {
  return (
    <div className={cn('sr-only focus-within:not-sr-only', className)}>
      <nav aria-label="קישורי דילוג">
        <ul className="flex flex-col gap-2 p-4 bg-background border-b">
          {links.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                className="block px-4 py-2 text-sm font-medium text-foreground bg-primary text-primary-foreground rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
}

