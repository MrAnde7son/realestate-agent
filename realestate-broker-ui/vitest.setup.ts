import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Provide minimal polyfill for Vite's SSR export helper used by "use client" directives
;(globalThis as any).__vite_ssr_exportName__ = (name: string, getter: () => any) => {
  const exports = (globalThis as any).__vite_ssr_exports__ || {}
  Object.defineProperty(exports, name, { enumerable: true, configurable: true, get: getter })
  ;(globalThis as any).__vite_ssr_exports__ = exports
}

// Mock Next.js navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
}))

// Mock Next.js link - simplified to avoid JSX issues
vi.mock('next/link', () => ({
  default: vi.fn(),
}))
