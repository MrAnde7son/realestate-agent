import { describe, it, expect, vi, beforeEach } from 'vitest'
import { GET } from './route'
import { NextRequest } from 'next/server'

process.env.BACKEND_URL = 'http://localhost:8000'

// Mock the data import
vi.mock('@/lib/data', () => ({
  assets: [
    {
      id: 1,
      address: 'Test Street 123',
      price: 3000000,
      bedrooms: 3,
      bathrooms: 2,
      area: 85,
      type: 'דירה',
      status: 'active',
      city: 'תל אביב',
      neighborhood: 'מרכז העיר',
    },
    {
      id: 2,
      address: 'Another Street 456',
      price: 4200000,
      bedrooms: 4,
      bathrooms: 3,
      area: 120,
      type: 'דירה',
      status: 'pending',
      city: 'תל אביב',
      neighborhood: 'רוטשילד',
    }
  ]
}))

// Mock fetch for backend calls
global.fetch = vi.fn()

describe('/api/assets/[id]', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default mock for failed backend calls
    ;(global.fetch as any).mockResolvedValue({
      ok: false,
      status: 404
    })
  })

  describe('GET', () => {
    it('returns asset when found in mock data', async () => {
      const request = new NextRequest('http://localhost:3000/api/assets/1')
      const params = { id: '1' }
      
      const response = await GET(request, { params })
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.asset).toBeDefined()
      expect(data.asset.id).toBe(1)
      expect(data.asset.address).toBe('Test Street 123')
      expect(data.asset.price).toBe(3000000)
      expect(data.asset.city).toBe('תל אביב')
    })

    it('returns 404 when asset not found', async () => {
      const request = new NextRequest('http://localhost:3000/api/assets/999')
      const params = { id: '999' }
      
      const response = await GET(request, { params })
      
      expect(response.status).toBe(404)
      expect(response.statusText).toBe('Not Found')
    })

    it('prefers backend data when available', async () => {
      const mockBackendAsset = {
        id: 101,
        address: 'Backend Street 789',
        price: 5000000,
        size: 100,
        property_type: 'פנטהאוס'
      }

      // Mock successful backend response
      ;(global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          rows: [mockBackendAsset]
        })
      })

      const request = new NextRequest('http://localhost:3000/api/assets/101')
      const params = { id: '101' }
      
      const response = await GET(request, { params })
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.asset).toBeDefined()
      expect(data.asset.id).toBe(101)
      expect(data.asset.address).toBe('Backend Street 789')
      expect(data.asset.price).toBe(5000000)
      expect(data.asset.type).toBe('פנטהאוס')
      
      // Verify backend was called
      expect(global.fetch).toHaveBeenCalledWith(
        `${process.env.BACKEND_URL || 'http://localhost:8000'}/api/assets/101`
      )
    })

    it('falls back to mock data when backend fails', async () => {
      // Mock backend failure
      ;(global.fetch as any).mockRejectedValue(new Error('Backend unavailable'))

      const request = new NextRequest('http://localhost:3000/api/assets/1')
      const params = { id: '1' }
      
      const response = await GET(request, { params })
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.asset).toBeDefined()
      expect(data.asset.id).toBe(1)
      expect(data.asset.address).toBe('Test Street 123')
    })

    it('handles backend timeout gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      // Mock backend timeout
      ;(global.fetch as any).mockImplementation(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Timeout')), 100)
        )
      )

      const request = new NextRequest('http://localhost:3000/api/assets/1')
      const params = { id: '1' }
      
      try {
        const response = await GET(request, { params })
        const data = await response.json()
        
        expect(response.status).toBe(200)
        expect(data.asset).toBeDefined()
        expect(data.asset.id).toBe(1)
      } finally {
        consoleSpy.mockRestore()
      }
    })

    it('transforms backend data correctly', async () => {
      const mockBackendAsset = {
        id: 102,
        external_id: 202,
        address: 'Transform Street 999',
        price: 2500000,
        size: 75,
        rooms: 2.5,
        bathrooms: 1,
        property_type: 'דירה',
        images: ['/image1.jpg', '/image2.jpg'],
        description: 'Nice apartment',
        features: ['balcony', 'parking'],
        contact_info: {
          name: 'Agent Name',
          phone: '050-1234567',
          email: 'agent@example.com'
        }
      }

      ;(global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          rows: [mockBackendAsset]
        })
      })

      const request = new NextRequest('http://localhost:3000/api/assets/102')
      const params = { id: '102' }
      
      const response = await GET(request, { params })
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.asset).toBeDefined()
      
      const asset = data.asset
      expect(asset.id).toBe(102)
      expect(asset.address).toBe('Transform Street 999')
      expect(asset.price).toBe(2500000)
      expect(asset.bedrooms).toBe(2.5)
      expect(asset.bathrooms).toBe(1)
      expect(asset.area).toBe(75)
      expect(asset.type).toBe('דירה')
      expect(asset.images).toEqual(['/image1.jpg', '/image2.jpg'])
      expect(asset.description).toBe('Nice apartment')
      expect(asset.features).toEqual(['balcony', 'parking'])
      expect(asset.contactInfo).toEqual({
        name: 'Agent Name',
        phone: '050-1234567',
        email: 'agent@example.com'
      })
      
      // Check calculated fields
      expect(asset.pricePerSqm).toBe(Math.round(2500000 / 75))
      expect(asset.city).toBe('תל אביב') // Default fallback
      expect(asset.neighborhood).toBe('מרכז העיר') // Default fallback
      expect(asset.netSqm).toBe(75)
    })

    it('uses external_id when id is not available in backend data', async () => {
      const mockBackendAsset = {
        external_id: 103,
        address: 'External ID Street',
        price: 3500000,
        size: 90,
        property_type: 'בית'
      }

      ;(global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          rows: [mockBackendAsset]
        })
      })

      const request = new NextRequest('http://localhost:3000/api/assets/103')
      const params = { id: '103' }
      
      const response = await GET(request, { params })
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.asset.id).toBe(103)
    })
  })
})
