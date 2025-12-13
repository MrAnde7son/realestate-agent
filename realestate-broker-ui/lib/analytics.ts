
// Define the shape of your events for type safety
export type EventName =
  | 'register'
  | 'login'
  | 'view_asset_list'
  | 'view_asset_details'
  | 'create_asset'
  | 'start_deal'
  | 'calculate_deal_expense'
  | 'update_deal_status'
  | 'calculate_mortgage'

/**
 * Unified tracking utility that sends events to both Vercel Analytics and Google Analytics 4.
 * 
 * @param name - The event name (snake_case)
 * @param properties - Optional event properties to track
 * 
 * @example
 * ```ts
 * trackEvent('create_asset', {
 *   asset_type: 'apartment',
 *   city: 'Tel Aviv'
 * })
 * ```
 */
export const trackEvent = (name: EventName, properties?: Record<string, any>) => {
  // 1. Send to Vercel Analytics
  // va.track(name, properties)

  // 2. Send to Google Analytics 4 (assumes standard gtag implementation)
  if (typeof window !== 'undefined' && (window as any).gtag) {
    ;(window as any).gtag('event', name, properties)
  }

  // Console log for local debugging
  if (process.env.NODE_ENV === 'development') {
    console.log(`[Analytics] ${name}`, properties)
  }
}
