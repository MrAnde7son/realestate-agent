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
  deleteAsset,
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
      const result = appraisalByAsset(1)

      expect(result).toHaveProperty('assetId', 1)
      expect(result).toHaveProperty('marketValue')
      expect(result).toHaveProperty('appraisedValue')
      expect(result).toHaveProperty('date')
      expect(result).toHaveProperty('appraiser')
      expect(result).toHaveProperty('notes')
      expect(typeof result.marketValue).toBe('number')
      expect(typeof result.appraisedValue).toBe('number')
    })

    it('returns default data for unknown asset ID', () => {
      const result = appraisalByAsset(999)

      expect(result).toHaveProperty('assetId', 999)
      expect(result).toHaveProperty('marketValue')
      expect(typeof result.marketValue).toBe('number')
    })

    it('has valid structure with expected fields', () => {
      const result = appraisalByAsset(1)

      expect(result.assetId).toBe(1)
      expect(result.marketValue).toBe(2850000)
      expect(result.appraisedValue).toBe(2800000)
      expect(typeof result.date).toBe('string')
      expect(typeof result.appraiser).toBe('string')
      expect(typeof result.notes).toBe('string')
    })
  })

  describe('compsByAsset', () => {
    it('returns comparison data for valid asset ID', () => {
      const result = compsByAsset(1)
      
      expect(Array.isArray(result)).toBe(true)
      expect(result.length).toBeGreaterThan(0)
    })

    it('returns default data for unknown asset ID', () => {
      const result = compsByAsset(999)
      
      expect(Array.isArray(result)).toBe(true)
      expect(result.length).toBeGreaterThan(0)
    })

    it('has valid comparable property structure', () => {
      const result = compsByAsset(1)
      
      result.forEach(prop => {
        expect(prop).toHaveProperty('address')
        expect(prop).toHaveProperty('price')
        expect(prop).toHaveProperty('area')
        expect(prop).toHaveProperty('pricePerSqm')
        expect(prop).toHaveProperty('date')
        expect(typeof prop.price).toBe('number')
        expect(typeof prop.area).toBe('number')
        expect(typeof prop.pricePerSqm).toBe('number')
        expect(typeof prop.address).toBe('string')
        expect(typeof prop.date).toBe('string')
      })
    })
  })

  describe('rightsByAsset', () => {
    it('returns rights data for valid asset ID', () => {
      const result = rightsByAsset(1)

      expect(result).toHaveProperty('assetId', 1)
      expect(result).toHaveProperty('buildingRights')
      expect(result).toHaveProperty('landUse')
      expect(result).toHaveProperty('restrictions')
      expect(result).toHaveProperty('permits')
      expect(result).toHaveProperty('lastUpdate')
      expect(Array.isArray(result.restrictions)).toBe(true)
      expect(Array.isArray(result.permits)).toBe(true)
    })

    it('returns default data for unknown asset ID', () => {
      const result = rightsByAsset(999)

      expect(result).toHaveProperty('assetId', 999)
      expect(result).toHaveProperty('buildingRights')
      expect(typeof result.buildingRights).toBe('string')
    })

    it('has valid structure with expected fields', () => {
      const result = rightsByAsset(1)

      expect(result.assetId).toBe(1)
      expect(typeof result.buildingRights).toBe('string')
      expect(typeof result.landUse).toBe('string')
      expect(typeof result.lastUpdate).toBe('string')
      expect(result.restrictions.length).toBeGreaterThan(0)
      expect(result.permits.length).toBeGreaterThan(0)
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

  describe('deleteAsset', () => {
    it('removes asset by id', () => {
      const newAsset: Asset = { id: 1010, address: 'Del St', price: 1, bedrooms: 1, bathrooms: 1, area: 1, type: 'דירה', status: 'active', images: [], description: '', features: [], contactInfo: { agent: '', phone: '', email: '' } }
      assets.push(newAsset)
      const removed = deleteAsset(1010)
      expect(removed?.id).toBe(1010)
      expect(assets.find(a => a.id === 1010)).toBeUndefined()
    })

    it('returns null for unknown id', () => {
      const result = deleteAsset(99999)
      expect(result).toBeNull()
    })
  })
})
