import { useEffect, useRef, useCallback } from 'react';
import { usePathname } from 'next/navigation';

interface AnalyticsEvent {
  event: string;
  user?: any;
  asset_id?: number;
  source?: string;
  error_code?: string;
  meta?: Record<string, any>;
}

interface PageViewData {
  session_id: string;
  page_path: string;
  user?: any;
  page_title?: string;
  load_time?: number;
  duration?: number;
  meta?: Record<string, any>;
}

class AnalyticsTracker {
  private sessionId: string;
  private pageStartTime: number;
  private currentPage: string | null = null;

  constructor() {
    this.sessionId = this.getOrCreateSessionId();
    this.pageStartTime = Date.now();
  }

  private getOrCreateSessionId(): string {
    if (typeof window === 'undefined') return '';
    
    let sessionId = sessionStorage.getItem('analytics_session_id');
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('analytics_session_id', sessionId);
    }
    return sessionId;
  }

  private async sendEvent(endpoint: string, data: any): Promise<void> {
    try {
      await fetch(`/api/analytics/${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
    } catch (error) {
      console.warn('Analytics tracking failed:', error);
    }
  }

  trackEvent(event: AnalyticsEvent): void {
    this.sendEvent('track', event);
  }

  trackPageView(data: Omit<PageViewData, 'session_id'>): void {
    const pageViewData: PageViewData = {
      session_id: this.sessionId,
      ...data,
    };
    this.sendEvent('page-view', pageViewData);
  }

  trackSearch(query: string, filters?: Record<string, any>, resultsCount?: number): void {
    this.trackEvent({
      event: 'search_performed',
      meta: {
        query,
        filters: filters || {},
        results_count: resultsCount || 0,
      },
    });
  }

  trackFeatureUsage(feature: string, assetId?: number, meta?: Record<string, any>): void {
    this.trackEvent({
      event: 'feature_usage',
      asset_id: assetId,
      meta: {
        feature,
        ...meta,
      },
    });
  }

  trackPerformance(metric: string, value: number, meta?: Record<string, any>): void {
    this.trackEvent({
      event: 'performance_metric',
      meta: {
        metric,
        value,
        ...meta,
      },
    });
  }

  trackCalculatorUsage(calculatorType: 'mortgage' | 'expense', action: string, meta?: Record<string, any>): void {
    this.trackEvent({
      event: 'calculator_usage',
      meta: {
        calculator_type: calculatorType,
        action,
        ...meta,
      },
    });
  }

  trackCalculatorCalculation(calculatorType: 'mortgage' | 'expense', inputData: Record<string, any>, resultData?: Record<string, any>): void {
    this.trackEvent({
      event: 'calculator_calculation',
      meta: {
        calculator_type: calculatorType,
        input_data: inputData,
        result_data: resultData,
      },
    });
  }

  trackCalculatorExport(calculatorType: 'mortgage' | 'expense', exportFormat: 'csv' | 'pdf' | 'excel', meta?: Record<string, any>): void {
    this.trackEvent({
      event: 'calculator_export',
      meta: {
        calculator_type: calculatorType,
        export_format: exportFormat,
        ...meta,
      },
    });
  }

  startPageTimer(pagePath: string): void {
    this.currentPage = pagePath;
    this.pageStartTime = Date.now();
  }

  endPageTimer(): number {
    if (!this.currentPage) return 0;
    
    const duration = (Date.now() - this.pageStartTime) / 1000;
    this.trackPageView({
      page_path: this.currentPage,
      page_title: document.title,
      duration,
      load_time: this.getPageLoadTime(),
      meta: {
        user_agent: navigator.userAgent,
        referrer: document.referrer,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight,
        },
      },
    });
    
    this.currentPage = null;
    return duration;
  }

  private getPageLoadTime(): number {
    if (typeof window === 'undefined' || !window.performance) return 0;
    
    const navigation = window.performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    return navigation ? navigation.loadEventEnd - navigation.loadEventStart : 0;
  }

  endSession(): void {
    const duration = (Date.now() - this.pageStartTime) / 1000;
    this.sendEvent('session-end', {
      session_id: this.sessionId,
      duration,
    });
  }
}

// Global analytics instance
const analytics = new AnalyticsTracker();

export function useAnalytics() {
  const pathname = usePathname();
  const pageTimerRef = useRef<NodeJS.Timeout>();

  // Track page views on route changes
  useEffect(() => {
    // End previous page timer
    analytics.endPageTimer();
    
    // Start new page timer for current path
    analytics.startPageTimer(pathname);
  }, [pathname]);

  // Track page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        analytics.endPageTimer();
      } else {
        analytics.startPageTimer(window.location.pathname);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // Track performance metrics
  useEffect(() => {
    const trackPerformanceMetrics = () => {
      if (typeof window !== 'undefined' && window.performance) {
        // Track page load time
        const navigation = window.performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        if (navigation) {
          analytics.trackPerformance('page_load_time', navigation.loadEventEnd - navigation.loadEventStart);
        }

        // Track First Contentful Paint
        const fcp = window.performance.getEntriesByName('first-contentful-paint')[0];
        if (fcp) {
          analytics.trackPerformance('first_contentful_paint', fcp.startTime);
        }

        // Track Largest Contentful Paint
        const lcp = window.performance.getEntriesByName('largest-contentful-paint')[0];
        if (lcp) {
          analytics.trackPerformance('largest_contentful_paint', lcp.startTime);
        }
      }
    };

    // Track performance after page load
    if (document.readyState === 'complete') {
      trackPerformanceMetrics();
    } else {
      window.addEventListener('load', trackPerformanceMetrics);
    }

    return () => {
      window.removeEventListener('load', trackPerformanceMetrics);
    };
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      analytics.endPageTimer();
      analytics.endSession();
    };
  }, []);

  return {
    trackEvent: useCallback(analytics.trackEvent.bind(analytics), []),
    trackPageView: useCallback(analytics.trackPageView.bind(analytics), []),
    trackSearch: useCallback(analytics.trackSearch.bind(analytics), []),
    trackFeatureUsage: useCallback(analytics.trackFeatureUsage.bind(analytics), []),
    trackPerformance: useCallback(analytics.trackPerformance.bind(analytics), []),
    trackCalculatorUsage: useCallback(analytics.trackCalculatorUsage.bind(analytics), []),
    trackCalculatorCalculation: useCallback(analytics.trackCalculatorCalculation.bind(analytics), []),
    trackCalculatorExport: useCallback(analytics.trackCalculatorExport.bind(analytics), []),
  };
}

export default analytics;
