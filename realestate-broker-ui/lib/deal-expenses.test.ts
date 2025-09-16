import { describe, it, expect } from 'vitest'

import { calculateServiceCosts } from './deal-expenses'

describe('calculateServiceCosts', () => {
  it('calculates percent-based services and adds VAT when needed', () => {
    const price = 2_000_000
    const vatRate = 0.18

    const { breakdown, total } = calculateServiceCosts(
      price,
      [
        {
          label: 'עמלת תיווך',
          percent: 2,
          includesVat: false
        }
      ],
      vatRate
    )

    const expectedCost = price * 0.02 * (1 + vatRate)

    expect(breakdown).toHaveLength(1)
    expect(breakdown[0]).toMatchObject({ label: 'עמלת תיווך' })
    expect(breakdown[0].cost).toBeCloseTo(expectedCost, 2)
    expect(total).toBeCloseTo(expectedCost, 2)
  })

  it('ignores services without cost and keeps values that already include VAT', () => {
    const { breakdown, total } = calculateServiceCosts(
      1_500_000,
      [
        { label: 'עמלת תיווך', percent: 0 },
        { label: 'יועץ משכנתא', amount: 0 },
        { label: 'בדק בית', amount: 4_200, includesVat: true }
      ],
      0.18
    )

    expect(breakdown).toHaveLength(1)
    expect(breakdown[0]).toMatchObject({ label: 'בדק בית', cost: 4_200 })
    expect(total).toBe(4_200)
  })
})
