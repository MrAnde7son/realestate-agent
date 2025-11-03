import { describe, expect, it } from 'vitest'

import {
  computeHeaderPricePerSqmValue,
  computeHeaderPriceValue,
  resolveContributorDisplayName,
  calculatePotentialScore,
  calculateEnvironmentScore,
} from '@/app/assets/[id]/AssetDetailPageClient'

describe('resolveContributorDisplayName', () => {
  it('returns trimmed name when provided', () => {
    expect(
      resolveContributorDisplayName({ name: '  יעל כהן  ', email: 'yael@example.com' })
    ).toBe('יעל כהן')
  })

  it('falls back to email when name is empty', () => {
    expect(
      resolveContributorDisplayName({ name: '  ', email: 'agent@example.com' })
    ).toBe('agent@example.com')
  })

  it('returns null when neither name nor email are available', () => {
    expect(resolveContributorDisplayName({})).toBeNull()
  })
})

describe('computeHeaderPriceValue', () => {
  it('prefers the asset price when available', () => {
    expect(computeHeaderPriceValue({ price: '2,500,000 ₪' })).toBe(2_500_000)
  })

  it('falls back to rent price when sale price is missing', () => {
    expect(computeHeaderPriceValue({ rentPrice: '7,500' })).toBe(7_500)
  })

  it('uses the provided fallback when asset fields are empty', () => {
    expect(computeHeaderPriceValue({}, 3_100_000)).toBe(3_100_000)
  })
})

describe('computeHeaderPricePerSqmValue', () => {
  it('returns direct price per sqm when available', () => {
    expect(computeHeaderPricePerSqmValue({ pricePerSqm: '15,750' }, null, null)).toBe(15_750)
  })

  it('computes price per sqm from listing size when needed', () => {
    expect(
      computeHeaderPricePerSqmValue({}, 2_000_000, 100)
    ).toBe(20_000)
  })

  it('falls back to asset area when listing size is missing', () => {
    expect(
      computeHeaderPricePerSqmValue({ area: 120 }, 2_400_000, null)
    ).toBe(20_000)
  })
})

describe('calculatePotentialScore', () => {
  it('returns investment potential score when available', () => {
    expect(calculatePotentialScore({ investmentPotentialScore: 120 }, 80)).toBe(100)
  })

  it('combines available signals when direct score is missing', () => {
    const asset = {
      rightsUsagePct: 40,
      area: 100,
      tama38KeyArea: true,
      tama38KeyAreasCount: 2,
    }
    expect(calculatePotentialScore(asset, 30)).toBe(52)
  })

  it('returns null when no relevant data is present', () => {
    expect(calculatePotentialScore({}, null)).toBeNull()
  })
})

describe('calculateEnvironmentScore', () => {
  it('prefers explicit environment score when provided', () => {
    expect(calculateEnvironmentScore({ environmentScore: 105 })).toBe(100)
  })

  it('aggregates contextual signals into a score', () => {
    const asset = {
      noiseLevel: 2,
      schoolsCount: 3,
      greenAmenitiesCount: 4,
      publicParkingLotsCount: 1,
    }
    expect(calculateEnvironmentScore(asset)).toBe(58)
  })

  it('returns null when there are no environmental indicators', () => {
    expect(calculateEnvironmentScore(null)).toBeNull()
    expect(calculateEnvironmentScore({})).toBeNull()
  })
})
