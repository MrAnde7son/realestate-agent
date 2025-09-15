import { describe, it, expect } from 'vitest'
import { calculatePurchaseTax } from './purchase-tax'

describe('calculatePurchaseTax', () => {
  it('calculates tax for first home buyer', () => {
    const tax = calculatePurchaseTax(2000000, [{ share: 100, firstApartment: true }])
    expect(tax).toBeCloseTo(744, 0)
  })

  it('calculates tax for additional home', () => {
    const tax = calculatePurchaseTax(2000000, [{ share: 100, firstApartment: false }])
    expect(tax).toBeCloseTo(160000, 0)
  })

  it('handles multiple buyers with different shares', () => {
    const tax = calculatePurchaseTax(1000000, [
      { share: 50, firstApartment: true },
      { share: 50, firstApartment: false }
    ])
    expect(tax).toBeCloseTo(40000, 0)
  })
})
