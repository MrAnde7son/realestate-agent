import { GET } from './route'
import { describe, it, expect, vi } from 'vitest'

describe('market-activity analytics API', () => {
  it('returns data from backend', async () => {
    const sample = { rows: [{ area: 'Tel Aviv', count: 3 }] }
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(sample)
    })
    vi.stubGlobal('fetch', fetchMock as any)
    const res = await GET()
    const data = await res.json()
    expect(fetchMock).toHaveBeenCalled()
    expect(data.rows[0].area).toBe('Tel Aviv')
  })
})
