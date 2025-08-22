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
      const mockAsset = {
        scope: {
          type: 'address' as const,
          value: 'New St 5',
          city: 'תל אביב'
        },
        address: 'New St 5',
        city: 'תל אביב',
        street: 'New St',
        number: 5
      }
      const request = createMockRequest(mockAsset)
      
      const response = await POST(request)
      const data = await response.json()
      
      expect(data.asset).toBeDefined()
      expect(data.asset.address).toBe('New St 5')
      expect(data.asset.city).toBe('תל אביב')
      expect(data.asset.status).toBe('pending')
      expect(data.asset.type).toBe('דירה')
    })

    it('validates required fields', async () => {
      const invalidAsset = { 
        address: '', 
        city: '' 
      }
      const request = createMockRequest(invalidAsset)
      
      const response = await POST(request)
      expect(response.status).toBe(400)
    })

    it('validates scope object', async () => {
      const invalidAsset = {
        address: 'Valid Address',
        city: 'תל אביב'
        // Missing scope object
      }
      const request = createMockRequest(invalidAsset)
      
      const response = await POST(request)
      expect(response.status).toBe(400)
    })
  })
})
