import { POST } from './route'
import { listings } from '@/lib/data'
import { describe, it, expect } from 'vitest'

describe('listings API', () => {
  it('adds a new listing', async () => {
    const initial = listings.length
    const req = new Request('http://localhost/api/listings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ address: 'New St 5', price: 500000 }),
    })
    const res = await POST(req)
    const data = await res.json()
    expect(res.status).toBe(201)
    expect(data.listing.address).toBe('New St 5')
    expect(listings.length).toBe(initial + 1)
    listings.pop()
  })
})
