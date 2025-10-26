import { describe, it, expect } from 'vitest'
import { normalizeFromBackend } from '@/lib/normalizers/asset'

describe('normalizeFromBackend commercial flag', () => {
  it('preserves boolean commercial flag', () => {
    const normalized = normalizeFromBackend({ id: 1, isCommercial: true })
    expect(normalized.isCommercial).toBe(true)
  })

  it('infers commercial flag from listing type', () => {
    const normalized = normalizeFromBackend({ id: 2, listingType: 'commercial' })
    expect(normalized.isCommercial).toBe(true)
  })
})
