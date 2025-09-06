import { describe, it, expect, vi } from 'vitest'
import { GET, POST, DELETE } from './route'
import { NextRequest } from 'next/server'
import { assets } from '@/lib/data'

const originalFetch = global.fetch

// Mock NextRequest
const createMockRequest = (body?: any) => {
  const request = new NextRequest('http://127.0.0.1:3000/api/assets', {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
    headers: {
      'Content-Type': 'application/json',
    },
  })
  return request
}

describe('/api/assets', () => {
  process.env.BACKEND_URL = 'http://127.0.0.1:8000'

  afterAll(() => {
    global.fetch = originalFetch
  })

  describe('GET', () => {
    it('fetches assets from backend', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          rows: [
            {
              id: 1,
              address: 'Backend Asset',
              price: 0,
              bedrooms: 0,
              bathrooms: 1,
              area: 0,
              type: 'דירה',
              status: 'active',
              images: [],
              description: '',
              features: [],
              contactInfo: { agent: '', phone: '', email: '' },
              city: 'תל אביב',
              assetId: 1,
              assetStatus: 'active'
            }
          ]
        })
      } as any)

      const response = await GET()
      const data = await response.json()

      expect(global.fetch).toHaveBeenCalledTimes(1)
      expect(response.status).toBe(200)
      expect(data.rows[0].address).toBe('Backend Asset')
    })

    it('falls back to mock assets on error', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('fail'))

      const response = await GET()
      const data = await response.json()

      expect(global.fetch).toHaveBeenCalledTimes(1)
      expect(Array.isArray(data.rows)).toBe(true)
      expect(data.rows.length).toBe(assets.length)
    })
  })

  describe('POST', () => {
    beforeEach(() => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 201,
        json: async () => ({ id: 999, status: 'pending', message: 'ok' })
      })
    })

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
      expect(data.asset.id).toBe(999)
      expect(data.asset.type).toBe('לא ידוע')
      
      // Ensure backend receives payload with scope information
      expect(global.fetch).toHaveBeenCalledTimes(1)
      const [, fetchOptions] = (global.fetch as any).mock.calls[0]
      const sentBody = JSON.parse(fetchOptions.body)
      expect(sentBody).toEqual({
        scope: mockAsset.scope,
        city: mockAsset.city,
        street: mockAsset.street,
        number: mockAsset.number,
        radius: 100
      })
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

    it('returns validation errors for invalid data', async () => {
      const invalidAsset = {
        scope: {
          type: 'invalid_type', // Invalid enum value
          value: 'Test',
          city: 'תל אביב'
        },
        address: 'Test Address',
        city: 'תל אביב'
      }
      const request = createMockRequest(invalidAsset)
      
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(400)
      expect(data.error).toBe('Validation failed')
      expect(data.details).toBeDefined()
    })

    it('handles different scope types', async () => {
      const scopeTypes = ['neighborhood', 'street', 'city', 'parcel']
      
      for (const type of scopeTypes) {
        const mockAsset = {
          scope: {
            type: type as any,
            value: 'Test Value',
            city: 'תל אביב'
          },
          address: 'Test Address',
          city: 'תל אביב'
        }
        const request = createMockRequest(mockAsset)
        
        const response = await POST(request)
        expect(response.status).toBe(201)
        
        const data = await response.json()
        expect(data.asset).toBeDefined()
        expect(data.asset.address).toBe('Test Address')
      }
    })

    it('handles server errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      // Create invalid request to trigger error
      const request = new NextRequest('http://127.0.0.1:3000/api/assets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: 'invalid json',
      })

      try {
        const response = await POST(request)
        const data = await response.json()

        expect(response.status).toBe(500)
        expect(data.error).toBe('Failed to create asset')
      } finally {
        consoleSpy.mockRestore()
      }
    })
  })

  describe('DELETE', () => {
    beforeEach(() => {
      global.fetch = vi.fn().mockRejectedValue(new Error('backend unavailable'))
    })

    it('deletes an asset', async () => {
      const newAsset = {
        id: 1234,
        address: 'Temp',
        price: 0,
        bedrooms: 0,
        bathrooms: 1,
        area: 0,
        type: 'דירה',
        status: 'active',
        images: [],
        description: '',
        features: [],
        contactInfo: { agent: '', phone: '', email: '' },
      }
      assets.push(newAsset as any)
      const req = new Request('http://localhost/api/assets', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assetId: newAsset.id }),
      })

      const res = await DELETE(req)
      const data = await res.json()

      expect(res.status).toBe(200)
      expect(data.message).toBeDefined()
      expect(assets.find(a => a.id === newAsset.id)).toBeUndefined()
    })
  })
})
