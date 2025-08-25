import '@testing-library/jest-dom'
import { vi } from 'vitest'
import React from 'react'

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
    // Return a simple div with the href as a data attribute for testing
    return React.createElement('div', { 'data-href': href, ...props }, children)
  },
}))
