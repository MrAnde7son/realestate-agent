import { describe, it, expect, vi } from 'vitest'
import { GET, POST } from './route'
import { NextRequest } from 'next/server'

// Mock NextRequest
const createMockRequest = (body?: any) => {
  const request = new NextRequest('http://localhost:3000/api/assets', {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
    headers: {
      'Content-Type': 'application/json',
    },
  })
  return request
}

describe('/api/assets', () => {
  describe('GET', () => {
    it('returns assets list', async () => {
      const response = await GET()
      const data = await response.json()
      
      expect(data.rows).toBeDefined()
      expect(Array.isArray(data.rows)).toBe(true)
      expect(data.rows.length).toBeGreaterThan(0)
    })
  })

  describe('POST', () => {
    it('adds a new asset', async () => {
      const mockAsset = { address: 'New St 5', price: 500000, bedrooms: 3, bathrooms: 2, area: 80 }
      const request = createMockRequest(mockAsset)
      
      const response = await POST(request)
      const data = await response.json()
      
      expect(data.asset).toBeDefined()
      expect(data.asset.address).toBe('New St 5')
      expect(data.asset.price).toBe(500000)
      expect(data.asset.bedrooms).toBe(3)
      expect(data.asset.bathrooms).toBe(2)
      expect(data.asset.area).toBe(80)
    })

    it('validates required fields', async () => {
      const invalidAsset = { address: '', price: -100 }
      const request = createMockRequest(invalidAsset)
      
      const response = await POST(request)
      expect(response.status).toBe(400)
    })
  })
})
