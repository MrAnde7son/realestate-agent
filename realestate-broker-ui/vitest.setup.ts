import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Declare the global type to avoid TypeScript errors
declare global {
  var __vite_ssr_exportName__: any
}

// Mock Next.js specific globals
globalThis.__vite_ssr_exportName__ = undefined

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
