import { describe, it, expect } from 'vitest'
import {
  pricePortfolio,
  amortizeTranche,
  calcPrime,
  calculateLTV,
  calculateAffordability,
  type PortfolioInput,
  type TrancheInput
} from './mortgage'

describe('mortgage engine', () => {
  const baseEnv: Omit<PortfolioInput, 'tranches'> = {
    boiAnnual: 4.75,
    primeSpread: 1.5,
    boiShock: 0,
    bondShock: 0,
    cpiShock: 0,
    monthlyIncome: 65_000
  }

  const defaultTranches: TrancheInput[] = [
    {
      name: 'Prime P-0.9',
      amount: 450_000,
      termMonths: 360,
      track: 'PRIME',
      anchorAnnual: calcPrime(baseEnv.boiAnnual, baseEnv.primeSpread),
      marginAnnual: -0.9,
      indexation: 'NONE',
      repayment: 'ANNUITY'
    },
    {
      name: 'Fixed Unlinked 4.7%',
      amount: 540_000,
      termMonths: 300,
      track: 'FIXED_UNLINKED',
      anchorAnnual: 4.7,
      marginAnnual: 0,
      indexation: 'NONE',
      repayment: 'ANNUITY'
    },
    {
      name: 'Variable Bond +0.8% CPI',
      amount: 333_000,
      termMonths: 360,
      track: 'VARIABLE_BOND',
      anchorAnnual: 3.9,
      marginAnnual: 0.8,
      resetEveryMonths: 60,
      indexation: 'CPI',
      cpiAnnualAssumption: 2,
      repayment: 'ANNUITY'
    }
  ]

  it('computes blended payments and totals for multi-track portfolio', () => {
    const result = pricePortfolio({ ...baseEnv, tranches: defaultTranches })

    expect(result.tranches).toHaveLength(3)
    expect(result.blendedFirstPayment).toBeGreaterThan(7000)
    expect(result.blendedFirstPayment).toBeLessThan(7600)
    expect(result.blendedMaxPayment).toBeGreaterThanOrEqual(result.blendedFirstPayment)
    expect(result.totals.paid).toBeGreaterThan(0)
    expect(result.totals.indexation).toBeGreaterThan(100_000)
    expect(result.affordability?.ok).toBe(true)
  })

  it('tracks grace periods and interest-only handling', () => {
    const graceTranche: TrancheInput = {
      name: 'Interest only year 1',
      amount: 300_000,
      termMonths: 240,
      track: 'FIXED_UNLINKED',
      anchorAnnual: 4.2,
      marginAnnual: 0,
      indexation: 'NONE',
      repayment: 'ANNUITY',
      graceType: 'INTEREST_ONLY',
      graceMonths: 12
    }

    const schedule = amortizeTranche(graceTranche, { ...baseEnv, tranches: [graceTranche] }).schedule
    expect(schedule[0].principalPortion).toBeCloseTo(0, 6)
    expect(schedule[0].payment).toBeCloseTo(schedule[0].interestPortion, 6)
    expect(schedule[12].principalPortion).toBeGreaterThan(0)
  })

  it('includes fees in APR calculation', () => {
    const trancheWithFees: TrancheInput = {
      name: 'Fixed with fees',
      amount: 200_000,
      termMonths: 120,
      track: 'FIXED_UNLINKED',
      anchorAnnual: 4,
      marginAnnual: 0,
      repayment: 'ANNUITY',
      indexation: 'NONE',
      feesUpfront: 5_000
    }

    const result = amortizeTranche(trancheWithFees, { ...baseEnv, tranches: [trancheWithFees] })
    expect(result.aprApprox).toBeGreaterThan(trancheWithFees.anchorAnnual)
  })

  it('calculates LTV and affordability helpers', () => {
    expect(calculateLTV(1_000_000, 2_000_000)).toBeCloseTo(50)
    const affordability = calculateAffordability(40_000, 10_000)
    expect(affordability.ratio).toBeCloseTo(25)
    expect(affordability.isAffordable).toBe(true)
  })
})
