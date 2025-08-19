import { GET } from './route'
import { describe, it, expect, vi } from 'vitest'

describe('property-types analytics API', () => {
  it('returns data from backend', async () => {
    const sample = { rows: [{ property_type: 'Apartment', count: 2 }] }
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(sample)
    })
    vi.stubGlobal('fetch', fetchMock as any)
    const res = await GET()
    const data = await res.json()
    expect(fetchMock).toHaveBeenCalled()
    expect(data.rows[0].property_type).toBe('Apartment')
  })
})
