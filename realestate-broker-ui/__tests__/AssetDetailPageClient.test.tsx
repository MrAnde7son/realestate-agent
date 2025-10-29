import { describe, it, expect, vi, beforeEach } from 'vitest'
import { syncTabWithUrl } from '@/app/assets/[id]/AssetDetailPageClient'

describe('syncTabWithUrl', () => {
  let setActiveTab: ReturnType<typeof vi.fn>
  let replace: ReturnType<typeof vi.fn>

  beforeEach(() => {
    setActiveTab = vi.fn()
    replace = vi.fn()
    window.history.replaceState(null, '', '/assets/123?foo=bar')
  })

  it('does nothing when the selected tab matches the active tab', () => {
    const changed = syncTabWithUrl('analysis', 'analysis', setActiveTab, { replace } as any)

    expect(changed).toBe(false)
    expect(setActiveTab).not.toHaveBeenCalled()
    expect(replace).not.toHaveBeenCalled()
  })

  it('updates the state and URL when switching tabs', () => {
    const changed = syncTabWithUrl('listings', 'analysis', setActiveTab, { replace } as any)

    expect(changed).toBe(true)
    expect(setActiveTab).toHaveBeenCalledWith('listings')
    expect(replace).toHaveBeenCalledWith('/assets/123?foo=bar&tab=listings', { scroll: false })
  })

  it('replaces existing tab parameter when switching tabs', () => {
    window.history.replaceState(null, '', '/assets/123?tab=analysis&foo=bar')

    syncTabWithUrl('listings', 'analysis', setActiveTab, { replace } as any)

    expect(replace).toHaveBeenCalledWith('/assets/123?tab=listings&foo=bar', { scroll: false })
  })
})
