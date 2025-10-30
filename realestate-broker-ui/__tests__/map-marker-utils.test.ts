import { describe, expect, it } from 'vitest'
import {
  buildMarkerDisplayData,
  formatAreaLabel,
  formatPriceLabel,
  formatPricePerSqmLabel,
  formatRoomsLabel,
  shouldDisplayMarkerLabel,
  truncateMiddle,
  type Asset,
} from '@/components/map-marker-utils'

describe('map marker display helpers', () => {
  it('formats price with compact notation for millions', () => {
    const label = formatPriceLabel(1_250_000)
    expect(label).toBeTruthy()
    expect(label).toContain('₪')
    expect(label).toMatch(/M/)
  })

  it('formats area and rooms labels correctly', () => {
    expect(formatAreaLabel(119.6)).toBe('120 מ״ר')
    expect(formatRoomsLabel(3.5)).toBe('3.5 חדרים')
  })

  it('falls back to computed price per sqm when explicit value missing', () => {
    const computed = formatPricePerSqmLabel(2_400_000, 120)
    expect(computed).toBe('20,000 ₪ למ״ר')

    const explicit = formatPricePerSqmLabel(2_400_000, 120, 18_750)
    expect(explicit).toBe('18,750 ₪ למ״ר')
  })

  it('builds marker data with sensible fallbacks', () => {
    const asset = {
      id: 42,
      street: 'דיזנגוף',
      number: 12,
      city: 'תל אביב',
      price: 2_450_000,
      area: 97,
      rooms: 3.5,
      type: 'דירה',
      photos: ['https://example.com/photo.jpg'],
      features: ['מעלית', 'חניה'],
    } as Asset

    const display = buildMarkerDisplayData(asset)

    expect(display.shortAddress).toContain('דיזנגוף')
    expect(display.fullAddress).toContain('תל אביב')
    expect(display.priceLabel).toContain('₪')
    expect(display.areaLabel).toBe('97 מ״ר')
    expect(display.roomsLabel).toBe('3.5 חדרים')
    expect(display.propertyType).toBe('דירה')
    expect(display.pricePerSqmLabel).toBe('25,258 ₪ למ״ר')
    expect(display.photoUrl).toBe('https://example.com/photo.jpg')
    expect(display.features).toEqual(['מעלית', 'חניה'])
    expect(display.cityLine).toBe('תל אביב')
  })

  it('uses listing level data when asset level info missing', () => {
    const asset = {
      id: 7,
      primaryListing: {
        address: 'Herzl 10, Tel Aviv',
        price: 1_650_000,
        size: 82,
        rooms: 4,
        propertyType: 'Garden Apartment',
        photos: ['https://example.com/listing.jpg'],
        features: ['מחסן', 'גן'],
        source: 'Yad2',
      },
    } as Asset

    const display = buildMarkerDisplayData(asset)

    expect(display.shortAddress).toContain('Herzl 10')
    expect(display.fullAddress).toContain('Tel Aviv')
    expect(display.priceLabel).toContain('₪')
    expect(display.areaLabel).toBe('82 מ״ר')
    expect(display.roomsLabel).toBe('4 חדרים')
    expect(display.propertyType).toBe('Garden Apartment')
    expect(display.features).toEqual(['מחסן', 'גן'])
    expect(display.sourceLabel).toBe('Yad2')
  })

  it('truncates long addresses for compact marker labels', () => {
    const long = '123 Example Street Very Long Address Text Here'
    const truncated = truncateMiddle(long, 20)
    expect(truncated.length).toBeLessThanOrEqual(20)
    expect(truncated).toContain('…')
  })

  it('determines label visibility based on density and zoom', () => {
    expect(shouldDisplayMarkerLabel({ totalAssets: 4 })).toBe(true)
    expect(shouldDisplayMarkerLabel({ totalAssets: 30, zoom: 12 })).toBe(false)
    expect(shouldDisplayMarkerLabel({ totalAssets: 30, zoom: 14 })).toBe(true)
    expect(shouldDisplayMarkerLabel({ totalAssets: 0, zoom: 18 })).toBe(false)
    expect(shouldDisplayMarkerLabel({ totalAssets: 30, zoom: 10, preferTouchDevice: true })).toBe(false)
  })
})
