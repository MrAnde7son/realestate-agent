'use client'

import * as React from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'

import { TabsList } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'

interface ScrollableTabsListProps extends React.ComponentProps<typeof TabsList> {
  scrollStep?: number
}

export function ScrollableTabsList({
  className,
  children,
  scrollStep = 240,
  ...props
}: ScrollableTabsListProps) {
  const listRef = React.useRef<HTMLDivElement>(null)
  const [canScrollBack, setCanScrollBack] = React.useState(false)
  const [canScrollForward, setCanScrollForward] = React.useState(false)

  const updateScrollState = React.useCallback(() => {
    const node = listRef.current
    if (!node) return

    const maxScrollLeft = node.scrollWidth - node.clientWidth
    setCanScrollBack(node.scrollLeft > 4)
    setCanScrollForward(node.scrollLeft < maxScrollLeft - 4)
  }, [])

  React.useEffect(() => {
    updateScrollState()
    const node = listRef.current
    if (!node) return

    const handleScroll = () => updateScrollState()
    node.addEventListener('scroll', handleScroll)
    window.addEventListener('resize', updateScrollState)
    return () => {
      node.removeEventListener('scroll', handleScroll)
      window.removeEventListener('resize', updateScrollState)
    }
  }, [updateScrollState])

  const scrollByAmount = React.useCallback(
    (direction: 'back' | 'forward') => {
      const node = listRef.current
      if (!node) return
      const amount = scrollStep || node.clientWidth * 0.7
      const delta = direction === 'back' ? -amount : amount
      node.scrollBy({ left: delta, behavior: 'smooth' })
    },
    [scrollStep]
  )

  return (
    <div className="relative">
      <TabsList
        ref={listRef}
        className={cn(
          'relative w-full overflow-x-auto whitespace-nowrap rounded-xl bg-white/90 p-2 pr-10 pl-10 shadow-md',
          'scroll-smooth',
          className
        )}
        {...props}
      >
        {children}
      </TabsList>

      <div
        aria-hidden
        className={cn(
          'pointer-events-none absolute inset-y-2 left-0 w-8 bg-gradient-to-r from-background to-transparent transition-opacity',
          canScrollBack ? 'opacity-100' : 'opacity-0'
        )}
      />
      <div
        aria-hidden
        className={cn(
          'pointer-events-none absolute inset-y-2 right-0 w-8 bg-gradient-to-l from-background to-transparent transition-opacity',
          canScrollForward ? 'opacity-100' : 'opacity-0'
        )}
      />

      <button
        type="button"
        onClick={() => scrollByAmount('back')}
        aria-label="גלול אחורה בין הטאבים"
        className={cn(
          'absolute left-1 top-1/2 -translate-y-1/2 rounded-full bg-white shadow-md ring-1 ring-muted-foreground/20 transition',
          'hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
          'disabled:pointer-events-none disabled:opacity-0'
        )}
        disabled={!canScrollBack}
      >
        <ChevronLeft className="h-4 w-4" />
      </button>

      <button
        type="button"
        onClick={() => scrollByAmount('forward')}
        aria-label="גלול קדימה בין הטאבים"
        className={cn(
          'absolute right-1 top-1/2 -translate-y-1/2 rounded-full bg-white shadow-md ring-1 ring-muted-foreground/20 transition',
          'hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
          'disabled:pointer-events-none disabled:opacity-0'
        )}
        disabled={!canScrollForward}
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  )
}

export default ScrollableTabsList
