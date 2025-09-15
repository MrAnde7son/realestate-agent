let cache: { rate: number; updatedAt: string } | null = null

export async function fetchVatRate(): Promise<{ rate: number; updatedAt: string }> {
  const now = Date.now()
  if (cache && now - new Date(cache.updatedAt).getTime() < 24 * 60 * 60 * 1000) {
    return cache
  }
  const fallback = { rate: 0.18, updatedAt: '2025-01-01' }
  try {
    const res = await fetch('https://www.gov.il/api/vat-rates')
    if (!res.ok) throw new Error('failed')
    const data = await res.json()
    const rate = typeof data?.rate === 'number' ? data.rate : typeof data?.currentRate === 'number' ? data.currentRate : fallback.rate
    const updatedAt = data?.updatedAt || new Date().toISOString()
    cache = { rate, updatedAt }
    return cache
  } catch (e) {
    cache = cache || fallback
    return cache
  }
}
