import { renderHook, act, waitFor } from "@testing-library/react"
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { useMediaQuery } from "./use-media-query"

describe("useMediaQuery", () => {
  let listeners: Array<(event: MediaQueryListEvent) => void>
  let currentMatch = false
  const originalMatchMedia = window.matchMedia ?? null

  const createMatchMedia = () => {
    const addEventListener = vi.fn<(key: string, cb: (event: MediaQueryListEvent) => void) => void>((_, cb) => {
      listeners.push(cb)
    })

    return {
      matches: currentMatch,
      media: "",
      onchange: null,
      addEventListener,
      removeEventListener: vi.fn(),
      addListener: vi.fn((cb: (event: MediaQueryListEvent) => void) => listeners.push(cb)),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(() => true),
    } as unknown as MediaQueryList
  }

  beforeEach(() => {
    listeners = []
    currentMatch = false
    ;(window as any).matchMedia = vi.fn(() => createMatchMedia())
  })

  afterEach(() => {
    vi.restoreAllMocks()
    if (originalMatchMedia) {
      window.matchMedia = originalMatchMedia
    } else {
      delete (window as any).matchMedia
    }
  })

  it("returns updated matches once the query resolves", async () => {
    currentMatch = true

    const { result } = renderHook(() => useMediaQuery("(min-width: 1024px)"))

    await waitFor(() => expect(result.current.matches).toBe(true))
  })

  it("responds to media query change events", async () => {
    currentMatch = false

    const { result } = renderHook(() => useMediaQuery("(min-width: 1024px)"))

    await waitFor(() => expect(result.current.isReady).toBe(true))
    expect(result.current.matches).toBe(false)

    act(() => {
      currentMatch = true
      listeners.forEach((listener) => listener({ matches: true } as MediaQueryListEvent))
    })

    expect(result.current.matches).toBe(true)
  })

  it("falls back to the provided default when matchMedia is unavailable", async () => {
    delete (window as any).matchMedia

    const { result } = renderHook(() => useMediaQuery("(min-width: 1024px)", { defaultValue: true }))

    await waitFor(() => expect(result.current.isReady).toBe(true))
    expect(result.current.matches).toBe(true)
  })
})
