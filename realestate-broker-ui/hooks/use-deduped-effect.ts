/* eslint-disable react-hooks/exhaustive-deps */
import * as React from 'react'

/**
 * A drop-in replacement for useEffect that skips duplicate executions caused by
 * React.StrictMode double-invocation in development. The effect still runs
 * whenever its dependency list changes, ensuring that we don't miss legitimate
 * updates while preventing redundant API calls.
 */
export function useDedupedEffect(
  effect: React.EffectCallback,
  deps: React.DependencyList
): void {
  const hasRunRef = React.useRef(false)
  const previousDepsRef = React.useRef<React.DependencyList | null>(null)

  React.useEffect(() => {
    const depsChanged =
      !depsAreEqual(previousDepsRef.current, deps)

    if (!depsChanged && hasRunRef.current) {
      return
    }

    previousDepsRef.current = deps
    hasRunRef.current = true

    return effect()
  }, deps)
}

function depsAreEqual(
  previousDeps: React.DependencyList | null,
  currentDeps: React.DependencyList
): boolean {
  if (!previousDeps || previousDeps.length !== currentDeps.length) {
    return false
  }

  for (let i = 0; i < currentDeps.length; i += 1) {
    if (!Object.is(previousDeps[i], currentDeps[i])) {
      return false
    }
  }

  return true
}
