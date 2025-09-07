import { describe, it, expect, vi, beforeEach } from 'vitest'
import { GET } from './route'
import { NextRequest } from 'next/server'

process.env.BACKEND_URL = 'http://127.0.0.1:8000'

// No local data mock needed

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
    it('returns 404 when asset not found', async () => {
      const request = new NextRequest('http://127.0.0.1:3000/api/assets/999')
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
        json: async () => mockBackendAsset
      })

      const request = new NextRequest('http://127.0.0.1:3000/api/assets/101')
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
        'http://127.0.0.1:8000/api/assets/101'
      )
    })

    it('returns 404 when backend fails', async () => {
      ;(global.fetch as any).mockRejectedValue(new Error('Backend unavailable'))

      const request = new NextRequest('http://127.0.0.1:3000/api/assets/1')
      const params = { id: '1' }

      const response = await GET(request, { params })
      expect(response.status).toBe(404)
    })

    it('handles backend timeout gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      ;(global.fetch as any).mockImplementation(() =>
        new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 100))
      )

      const request = new NextRequest('http://127.0.0.1:3000/api/assets/1')
      const params = { id: '1' }

      try {
        const response = await GET(request, { params })
        expect(response.status).toBe(404)
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
        area: 75,
        rooms: 2.5,
        bathrooms: 1,
        property_type: 'דירה',
        pricePerSqm: Math.round(2500000 / 75)
      }

      ;(global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockBackendAsset
      })

      const request = new NextRequest('http://127.0.0.1:3000/api/assets/102')
      const params = { id: '102' }
      
      const response = await GET(request, { params })
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.asset).toBeDefined()
      
      const asset = data.asset
      expect(asset.id).toBe(102)
      expect(asset.address).toBe('Transform Street 999')
      expect(asset.price).toBe(2500000)
      expect(asset.rooms).toBe(2.5)
      expect(asset.bathrooms).toBe(1)
      expect(asset.area).toBe(75)
      expect(asset.type).toBe('דירה')
      expect(asset.pricePerSqm).toBe(Math.round(2500000 / 75))
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
        json: async () => mockBackendAsset
      })

      const request = new NextRequest('http://127.0.0.1:3000/api/assets/103')
      const params = { id: '103' }
      
      const response = await GET(request, { params })
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.asset.id).toBe(103)
    })
  })
})
