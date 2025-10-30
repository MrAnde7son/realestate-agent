import * as React from "react"

interface UseMediaQueryOptions {
  /** Value to return during SSR before the media query is evaluated on the client. */
  defaultValue?: boolean
  /**
   * When true the hook evaluates the media query synchronously during the initial render.
   * This is helpful for client-only components but should be avoided for SSR to prevent
   * hydration mismatches.
   */
  initializeWithValue?: boolean
}

interface UseMediaQueryResult {
  matches: boolean
  isReady: boolean
}

/**
 * Client-side utility that exposes the `matches` state of a CSS media query.
 * It is resilient to SSR environments by falling back to a configurable default
 * until the component mounts in the browser.
 */
export function useMediaQuery(
  query: string,
  { defaultValue = false, initializeWithValue = false }: UseMediaQueryOptions = {}
): UseMediaQueryResult {
  const getMatch = React.useCallback(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return defaultValue
    }

    try {
      return window.matchMedia(query).matches
    } catch (error) {
      console.warn("useMediaQuery: matchMedia evaluation failed", error)
      return defaultValue
    }
  }, [defaultValue, query])

  const [matches, setMatches] = React.useState<boolean>(() =>
    initializeWithValue ? getMatch() : defaultValue
  )
  const [isReady, setIsReady] = React.useState<boolean>(() =>
    typeof window === "undefined" ? false : initializeWithValue
  )

  React.useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      setMatches(defaultValue)
      setIsReady(true)
      return
    }

    const mediaQueryList = window.matchMedia(query)
    const listener = (event: MediaQueryListEvent | MediaQueryList) => {
      const nextValue = "matches" in event ? event.matches : mediaQueryList.matches
      setMatches(nextValue)
    }

    setMatches(mediaQueryList.matches)
    setIsReady(true)

    if (typeof mediaQueryList.addEventListener === "function") {
      mediaQueryList.addEventListener("change", listener)
    } else if (typeof mediaQueryList.addListener === "function") {
      mediaQueryList.addListener(listener)
    }

    return () => {
      if (typeof mediaQueryList.removeEventListener === "function") {
        mediaQueryList.removeEventListener("change", listener)
      } else if (typeof mediaQueryList.removeListener === "function") {
        mediaQueryList.removeListener(listener)
      }
    }
  }, [defaultValue, getMatch, query])

  return { matches, isReady }
}

export default useMediaQuery
