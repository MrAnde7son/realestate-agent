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

describe('normalizeFromBackend timestamps', () => {
  it('normalizes enrichment, update, and creation timestamps', () => {
    const updatedEpochSeconds = Math.floor(Date.UTC(2024, 0, 5, 12, 0, 0) / 1000)
    const normalized = normalizeFromBackend({
      id: 3,
      last_enriched_at: '2024-01-02T03:04:05Z',
      updated_at: updatedEpochSeconds,
      created_at: '2023-12-31T21:00:00Z',
    })

    expect(normalized.last_enriched_at).toBe('2024-01-02T03:04:05Z')
    expect(normalized.lastEnrichedAt).toBe('2024-01-02T03:04:05Z')

    const expectedUpdatedIso = new Date(updatedEpochSeconds * 1000).toISOString()
    expect(normalized.updated_at).toBe(expectedUpdatedIso)
    expect(normalized.updatedAt).toBe(expectedUpdatedIso)

    expect(normalized.created_at).toBe('2023-12-31T21:00:00Z')
    expect(normalized.createdAt).toBe('2023-12-31T21:00:00Z')
  })
})
