import '@testing-library/jest-dom'
import { vi } from 'vitest'
import React from 'react'

// Mock ResizeObserver for chart components
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock Next.js hooks for testing
vi.mock('next/navigation', () => ({
  usePathname: () => '/',
  useRouter: () => ({
    push: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
}))

// Mock Next.js Link component
vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: any) => {
    // Return a proper anchor element with the correct role for accessibility testing
    return React.createElement('a', { href, ...props }, children)
  },
}))

// Mock fetch for analytics calls
global.fetch = vi.fn().mockImplementation((url, options) => {
  // Mock analytics API calls
  if (typeof url === 'string' && url.includes('/api/analytics/')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ success: true })
    })
  }
  // For other fetch calls, return a default response
  return Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({})
  })
})
