import { describe, it, expect, vi, afterEach } from 'vitest'
import { toast } from './use-toast'

describe('use-toast timers', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('unrefs auto-dismiss timers when environment supports it', () => {
    const unref = vi.fn()
    const fakeTimer = { unref } as unknown as NodeJS.Timeout
    let scheduledCallback: (() => void) | undefined

    const setTimeoutSpy = vi
      .spyOn(global, 'setTimeout')
      .mockImplementation((handler: Parameters<typeof setTimeout>[0], timeout?: number, ...args: any[]) => {
        scheduledCallback = handler as () => void
        return fakeTimer as unknown as ReturnType<typeof setTimeout>
      })

    const { dismiss } = toast({ title: 'Test toast' })
    dismiss()

    expect(setTimeoutSpy).toHaveBeenCalled()
    expect(unref).toHaveBeenCalled()

    // Execute the scheduled callback to keep internal state clean for subsequent tests
    scheduledCallback?.()
  })
})
