'use client'

import { useEffect } from 'react'
import { useAnalytics } from '@/hooks/useAnalytics'

export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  const { trackPageView } = useAnalytics()

  useEffect(() => {
    // Track initial page view
    trackPageView({
      page_path: window.location.pathname,
      page_title: document.title,
      load_time: performance.now(),
      meta: {
        user_agent: navigator.userAgent,
        referrer: document.referrer,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight,
        },
      },
    })
  }, [trackPageView])

  return <>{children}</>
}
