import { describe, it, expect, beforeEach } from 'vitest'
import { 
  assets, 
  alerts, 
  appraisalByAsset, 
  compsByAsset, 
  rightsByAsset,
  getActiveAlerts,
  getActiveAlertsCount,
  getActiveAssetsCount,
  addAsset,
  type Asset,
  type Alert
} from './data'

describe('Data Module', () => {
  describe('Static Data', () => {
    it('exports assets array with correct structure', () => {
      expect(Array.isArray(assets)).toBe(true)
      expect(assets.length).toBeGreaterThan(0)
      
      const firstAsset = assets[0]
      expect(firstAsset).toHaveProperty('id')
      expect(firstAsset).toHaveProperty('address')
      expect(firstAsset).toHaveProperty('price')
      expect(firstAsset).toHaveProperty('bedrooms')
      expect(firstAsset).toHaveProperty('bathrooms')
      expect(firstAsset).toHaveProperty('area')
      expect(firstAsset).toHaveProperty('type')
      expect(firstAsset).toHaveProperty('status')
      expect(firstAsset).toHaveProperty('contactInfo')
    })

    it('exports alerts array with correct structure', () => {
      expect(Array.isArray(alerts)).toBe(true)
      expect(alerts.length).toBeGreaterThan(0)
      
      const firstAlert = alerts[0]
      expect(firstAlert).toHaveProperty('id')
      expect(firstAlert).toHaveProperty('type')
      expect(firstAlert).toHaveProperty('title')
      expect(firstAlert).toHaveProperty('message')
      expect(firstAlert).toHaveProperty('priority')
      expect(firstAlert).toHaveProperty('isRead')
      expect(firstAlert).toHaveProperty('createdAt')
    })

    it('has assets with valid price values', () => {
      assets.forEach(asset => {
        expect(typeof asset.price).toBe('number')
        expect(asset.price).toBeGreaterThanOrEqual(0)
      })
    })

    it('has assets with valid contact info', () => {
      assets.forEach(asset => {
        expect(asset.contactInfo).toHaveProperty('agent')
        expect(asset.contactInfo).toHaveProperty('phone')
        expect(asset.contactInfo).toHaveProperty('email')
        expect(typeof asset.contactInfo.agent).toBe('string')
        expect(typeof asset.contactInfo.phone).toBe('string')
        expect(typeof asset.contactInfo.email).toBe('string')
      })
    })
  })

  describe('appraisalByAsset', () => {
    it('returns appraisal data for valid asset ID', () => {
      const result = appraisalByAsset('l1')
      
      expect(result).toHaveProperty('assetId', 'l1')
      expect(result).toHaveProperty('marketValue')
      expect(result).toHaveProperty('rentEstimate')
      expect(result).toHaveProperty('capRate')
      expect(result).toHaveProperty('roi')
      expect(result).toHaveProperty('pricePerSqm')
      expect(result).toHaveProperty('comparables')
      expect(Array.isArray(result.comparables)).toBe(true)
    })

    it('returns default data for unknown asset ID', () => {
      const result = appraisalByAsset('unknown')
      
      expect(result).toHaveProperty('assetId', 'unknown')
      expect(result).toHaveProperty('marketValue')
      expect(typeof result.marketValue).toBe('number')
    })

    it('has valid comparable properties', () => {
      const result = appraisalByAsset('l1')
      
      result.comparables.forEach(comp => {
        expect(comp).toHaveProperty('address')
        expect(comp).toHaveProperty('price')
        expect(comp).toHaveProperty('pricePerSqm')
        expect(comp).toHaveProperty('size')
        expect(comp).toHaveProperty('distance')
        expect(comp).toHaveProperty('similarity')
        expect(typeof comp.price).toBe('number')
        expect(typeof comp.pricePerSqm).toBe('number')
        expect(typeof comp.size).toBe('number')
        expect(typeof comp.distance).toBe('number')
        expect(typeof comp.similarity).toBe('number')
      })
    })
  })

  describe('compsByAsset', () => {
    it('returns comparison data for valid asset ID', () => {
      const result = compsByAsset('l1')
      
      expect(result).toHaveProperty('assetId', 'l1')
      expect(result).toHaveProperty('similarProperties')
      expect(Array.isArray(result.similarProperties)).toBe(true)
      expect(result.similarProperties.length).toBeGreaterThan(0)
    })

    it('returns default data for unknown asset ID', () => {
      const result = compsByAsset('unknown')
      
      expect(result).toHaveProperty('assetId', 'unknown')
      expect(result).toHaveProperty('similarProperties')
      expect(Array.isArray(result.similarProperties)).toBe(true)
    })

    it('has valid similar property structure', () => {
      const result = compsByAsset('l1')
      
      result.similarProperties.forEach(prop => {
        expect(prop).toHaveProperty('address')
        expect(prop).toHaveProperty('price')
        expect(prop).toHaveProperty('pricePerSqm')
        expect(prop).toHaveProperty('bedrooms')
        expect(prop).toHaveProperty('area')
        expect(prop).toHaveProperty('yearBuilt')
        expect(prop).toHaveProperty('condition')
        expect(prop).toHaveProperty('lastSold')
        expect(typeof prop.price).toBe('number')
        expect(typeof prop.pricePerSqm).toBe('number')
        expect(typeof prop.bedrooms).toBe('number')
        expect(typeof prop.area).toBe('number')
      })
    })
  })

  describe('rightsByAsset', () => {
    it('returns rights data for valid asset ID', () => {
      const result = rightsByAsset('l1')
      
      expect(result).toHaveProperty('assetId', 'l1')
      expect(result).toHaveProperty('currentRights')
      expect(result).toHaveProperty('usedRights')
      expect(result).toHaveProperty('remainingRights')
      expect(result).toHaveProperty('buildingCoverage')
      expect(result).toHaveProperty('maxHeight')
      expect(result).toHaveProperty('setbacks')
      expect(result).toHaveProperty('zoning')
    })

    it('returns default data for unknown asset ID', () => {
      const result = rightsByAsset('unknown')
      
      expect(result).toHaveProperty('assetId', 'unknown')
      expect(result).toHaveProperty('currentRights')
      expect(typeof result.currentRights).toBe('number')
    })

    it('has valid setbacks structure', () => {
      const result = rightsByAsset('l1')
      
      expect(result.setbacks).toHaveProperty('front')
      expect(result.setbacks).toHaveProperty('rear')
      expect(result.setbacks).toHaveProperty('side')
      expect(typeof result.setbacks.front).toBe('number')
      expect(typeof result.setbacks.rear).toBe('number')
      expect(typeof result.setbacks.side).toBe('number')
    })
  })

  describe('Alert Functions', () => {
    it('getActiveAlerts returns only unread alerts', () => {
      const activeAlerts = getActiveAlerts()
      
      expect(Array.isArray(activeAlerts)).toBe(true)
      activeAlerts.forEach(alert => {
        expect(alert.isRead).toBe(false)
      })
    })

    it('getActiveAlertsCount returns correct count', () => {
      const count = getActiveAlertsCount()
      const activeAlerts = getActiveAlerts()
      
      expect(count).toBe(activeAlerts.length)
      expect(typeof count).toBe('number')
      expect(count).toBeGreaterThanOrEqual(0)
    })

    it('getActiveAssetsCount returns correct count', () => {
      const count = getActiveAssetsCount()
      const activeAssets = assets.filter(asset => asset.status === 'active')
      
      expect(count).toBe(activeAssets.length)
      expect(typeof count).toBe('number')
      expect(count).toBeGreaterThanOrEqual(0)
    })
  })

  describe('addAsset', () => {
    let originalLength: number

    beforeEach(() => {
      originalLength = assets.length
    })

    it('adds a new asset to the assets array', () => {
      const newAsset: Asset = {
        id: 'test-asset',
        address: 'Test Street 123',
        price: 2000000,
        bedrooms: 3,
        bathrooms: 2,
        area: 90,
        type: 'דירה',
        status: 'pending',
        images: [],
        description: 'Test asset',
        features: [],
        contactInfo: {
          agent: 'Test Agent',
          phone: '050-1234567',
          email: 'test@example.com'
        }
      }

      addAsset(newAsset)
      
      expect(assets.length).toBe(originalLength + 1)
      expect(assets[assets.length - 1]).toEqual(newAsset)
    })

    it('maintains asset array structure after adding', () => {
      const newAsset: Asset = {
        id: 'test-asset-2',
        address: 'Another Test Street 456',
        price: 3500000,
        bedrooms: 4,
        bathrooms: 3,
        area: 120,
        type: 'בית',
        status: 'active',
        images: ['/test-image.jpg'],
        description: 'Another test asset',
        features: ['garden', 'garage'],
        contactInfo: {
          agent: 'Another Agent',
          phone: '052-7654321',
          email: 'another@example.com'
        },
        city: 'תל אביב',
        neighborhood: 'מרכז העיר'
      }

      addAsset(newAsset)
      
      const addedAsset = assets[assets.length - 1]
      expect(addedAsset).toHaveProperty('id', 'test-asset-2')
      expect(addedAsset).toHaveProperty('city', 'תל אביב')
      expect(addedAsset).toHaveProperty('neighborhood', 'מרכז העיר')
      expect(addedAsset.features).toEqual(['garden', 'garage'])
    })
  })

  describe('Data Integrity', () => {
    it('has unique asset IDs', () => {
      const ids = assets.map(asset => asset.id)
      const uniqueIds = new Set(ids)
      
      expect(uniqueIds.size).toBe(ids.length)
    })

    it('has unique alert IDs', () => {
      const ids = alerts.map(alert => alert.id)
      const uniqueIds = new Set(ids)
      
      expect(uniqueIds.size).toBe(ids.length)
    })

    it('has valid asset status values', () => {
      const validStatuses = ['active', 'pending', 'sold']
      
      assets.forEach(asset => {
        expect(validStatuses).toContain(asset.status)
      })
    })

    it('has valid alert types', () => {
      const validTypes = ['price_drop', 'new_asset', 'market_change', 'document_update', 'permit_status']
      
      alerts.forEach(alert => {
        expect(validTypes).toContain(alert.type)
      })
    })

    it('has valid alert priorities', () => {
      const validPriorities = ['high', 'medium', 'low']
      
      alerts.forEach(alert => {
        expect(validPriorities).toContain(alert.priority)
      })
    })
  })
})
