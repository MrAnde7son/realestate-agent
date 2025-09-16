import { describe, it, expect } from 'vitest'
import { calculatePurchaseTax, type Buyer } from './purchase-tax'

describe('calculatePurchaseTax', () => {
  it('calculates tax for single buyer first home', () => {
    const buyers: Buyer[] = [{ name: 'A', sharePct: 100, isFirstHome: true }]
    const { totalTax } = calculatePurchaseTax(2_000_000, buyers)
    expect(Math.round(totalTax)).toBe(744)
  })

  it('calculates tax for additional home', () => {
    const buyers: Buyer[] = [{ name: 'A', sharePct: 100, isFirstHome: false }]
    const { totalTax } = calculatePurchaseTax(1_000_000, buyers)
    expect(totalTax).toBeCloseTo(80_000)
  })

  it('applies flat tax rate for land purchases', () => {
    const buyers: Buyer[] = [
      { name: 'A', sharePct: 60 },
      { name: 'B', sharePct: 40 }
    ]
    const { totalTax, breakdown } = calculatePurchaseTax(1_000_000, buyers, { propertyType: 'land' })
    expect(totalTax).toBeCloseTo(60_000)
    expect(breakdown[0].tax).toBeCloseTo(36_000)
    expect(breakdown[1].tax).toBeCloseTo(24_000)
    expect(breakdown.every(item => item.track === 'land')).toBe(true)
  })
})
