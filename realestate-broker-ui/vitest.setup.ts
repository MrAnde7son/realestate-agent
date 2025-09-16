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

// Make URL constructor available globally for tests
global.URL = URL

// Mock URL.createObjectURL for MapLibre GL
const originalCreateObjectURL = URL.createObjectURL
const originalRevokeObjectURL = URL.revokeObjectURL

URL.createObjectURL = vi.fn(() => 'mock-blob-url')
URL.revokeObjectURL = vi.fn()

// Also add to window for MapLibre GL
Object.defineProperty(window, 'URL', {
  value: URL,
  writable: true,
})

// Mock WebGL context for MapLibre GL
const mockWebGLContext = {
  getParameter: vi.fn(),
  createShader: vi.fn(),
  createProgram: vi.fn(),
  createBuffer: vi.fn(),
  createTexture: vi.fn(),
  createFramebuffer: vi.fn(),
  createRenderbuffer: vi.fn(),
  shaderSource: vi.fn(),
  compileShader: vi.fn(),
  attachShader: vi.fn(),
  linkProgram: vi.fn(),
  useProgram: vi.fn(),
  enable: vi.fn(),
  disable: vi.fn(),
  clear: vi.fn(),
  clearColor: vi.fn(),
  viewport: vi.fn(),
  drawArrays: vi.fn(),
  drawElements: vi.fn(),
  bindBuffer: vi.fn(),
  bindTexture: vi.fn(),
  bindFramebuffer: vi.fn(),
  bindRenderbuffer: vi.fn(),
  bufferData: vi.fn(),
  texImage2D: vi.fn(),
  texParameteri: vi.fn(),
  framebufferTexture2D: vi.fn(),
  renderbufferStorage: vi.fn(),
  framebufferRenderbuffer: vi.fn(),
  getAttribLocation: vi.fn(),
  getUniformLocation: vi.fn(),
  uniform1f: vi.fn(),
  uniform2f: vi.fn(),
  uniform3f: vi.fn(),
  uniform4f: vi.fn(),
  uniform1i: vi.fn(),
  uniformMatrix4fv: vi.fn(),
  vertexAttribPointer: vi.fn(),
  enableVertexAttribArray: vi.fn(),
  disableVertexAttribArray: vi.fn(),
  activeTexture: vi.fn(),
  generateMipmap: vi.fn(),
  deleteShader: vi.fn(),
  deleteProgram: vi.fn(),
  deleteBuffer: vi.fn(),
  deleteTexture: vi.fn(),
  deleteFramebuffer: vi.fn(),
  deleteRenderbuffer: vi.fn(),
  checkFramebufferStatus: vi.fn(() => 36053), // FRAMEBUFFER_COMPLETE
  getShaderParameter: vi.fn(() => true),
  getProgramParameter: vi.fn(() => true),
  getShaderInfoLog: vi.fn(() => ''),
  getProgramInfoLog: vi.fn(() => ''),
}

// Mock canvas for MapLibre GL
Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
  value: vi.fn(function(contextType) {
    if (contextType === 'webgl' || contextType === 'webgl2') {
      return mockWebGLContext
    }
    // For other context types, return a basic 2D context mock
    if (contextType === '2d') {
      return {
        fillRect: vi.fn(),
        clearRect: vi.fn(),
        getImageData: vi.fn(() => ({ data: new Array(4) })),
        putImageData: vi.fn(),
        createImageData: vi.fn(() => ({ data: new Array(4) })),
        setTransform: vi.fn(),
        drawImage: vi.fn(),
        save: vi.fn(),
        restore: vi.fn(),
        beginPath: vi.fn(),
        closePath: vi.fn(),
        moveTo: vi.fn(),
        lineTo: vi.fn(),
        arc: vi.fn(),
        fill: vi.fn(),
        stroke: vi.fn(),
        translate: vi.fn(),
        scale: vi.fn(),
        rotate: vi.fn(),
        rect: vi.fn(),
        clip: vi.fn(),
      }
    }
    return null
  }),
  writable: true,
  configurable: true,
})

// Mock canvas dimensions
Object.defineProperty(HTMLCanvasElement.prototype, 'clientWidth', {
  value: 800,
  writable: true,
})
Object.defineProperty(HTMLCanvasElement.prototype, 'clientHeight', {
  value: 600,
  writable: true,
})
