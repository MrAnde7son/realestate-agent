import { describe, it, expect, vi } from 'vitest'
import { GET, POST, DELETE } from './route'
import { NextRequest } from 'next/server'

// Create a valid JWT token for testing (expires in 1 hour)
const createMockJWT = () => {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const payload = btoa(JSON.stringify({ 
    exp: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
    iat: Math.floor(Date.now() / 1000),
    sub: 'test-user'
  }))
  const signature = 'mock-signature'
  return `${header}.${payload}.${signature}`
}

// Mock cookies
vi.mock('next/headers', () => ({
  cookies: vi.fn(() => ({
    get: vi.fn((name: string) => {
      if (name === 'access_token') {
        return { value: createMockJWT() }
      }
      return undefined
    })
  }))
}))

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
              assetId: 1
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

    it('returns error when backend fetch fails', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('fail'))

      const response = await GET()
      const data = await response.json()

      expect(global.fetch).toHaveBeenCalledTimes(1)
      expect(response.status).toBe(500)
      expect(data.error).toBeDefined()
    })
  })

  describe('POST', () => {
    beforeEach(() => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 201,
        json: async () => ({ 
          id: 999, 
          status: 'pending', 
          message: 'ok',
          address: 'New St 5',
          city: 'תל אביב',
          street: 'New St',
          number: 5
        })
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
      expect(data.asset.assetStatus).toBe('pending')
      expect(data.asset.id).toBe(999)
      expect(data.asset.type).toBeNull()
      
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

    it('passes parcel information through DTO', async () => {
      const mockParcelAsset = {
        scope: {
          type: 'parcel' as const,
          value: '1/2'
        },
        block: '1',
        parcel: '2',
        subparcel: '3'
      }
      const request = createMockRequest(mockParcelAsset)

      const response = await POST(request)
      const data = await response.json()

      expect(response.status).toBe(201)
      expect(data.asset.block).toBe('1')
      expect(data.asset.parcel).toBe('2')
      expect(data.asset.subparcel).toBe('3')

      const [, fetchOptions] = (global.fetch as any).mock.calls[0]
      const sentBody = JSON.parse(fetchOptions.body)
      expect(sentBody.block).toBe('1')
      expect(sentBody.parcel).toBe('2')
      expect(sentBody.subparcel).toBe('3')
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
    it('deletes an asset', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ message: 'deleted' })
      })

      const req = new Request('http://localhost/api/assets', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assetId: 1234 }),
      })

      const res = await DELETE(req)
      const data = await res.json()

      expect(res.status).toBe(200)
      expect(data.message).toBeDefined()
      expect(global.fetch).toHaveBeenCalledTimes(1)
    })
  })
})
