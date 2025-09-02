import { describe, it, expect } from 'vitest'
import { cn, fmtCurrency, fmtNumber, fmtPct } from './utils'

describe('Utils', () => {
  describe('cn (className merger)', () => {
    it('merges class names correctly', () => {
      expect(cn('flex', 'items-center')).toBe('flex items-center')
    })

    it('handles conditional classes', () => {
      expect(cn('flex', true && 'items-center', false && 'hidden')).toBe('flex items-center')
    })

    it('resolves Tailwind conflicts', () => {
      expect(cn('px-2', 'px-4')).toBe('px-4')
      expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500')
    })

    it('handles undefined and null values', () => {
      expect(cn('flex', undefined, null, 'items-center')).toBe('flex items-center')
    })

    it('handles empty input', () => {
      expect(cn()).toBe('')
    })

    it('handles arrays of classes', () => {
      expect(cn(['flex', 'items-center'], 'justify-center')).toBe('flex items-center justify-center')
    })

    it('handles objects with boolean values', () => {
      expect(cn({
        'flex': true,
        'hidden': false,
        'items-center': true
      })).toBe('flex items-center')
    })
  })

  describe('fmtCurrency', () => {
    it('formats currency in Hebrew locale', () => {
      const result = fmtCurrency(3000000)
      expect(result).toContain('3,000,000')
      expect(result).toContain('₪')
    })

    it('handles zero correctly', () => {
      const result = fmtCurrency(0)
      expect(result).toContain('0')
      expect(result).toContain('₪')
    })

    it('handles negative numbers', () => {
      const result = fmtCurrency(-1500000)
      expect(result).toContain('-1,500,000')
      expect(result).toContain('₪')
    })

    it('handles large numbers', () => {
      const result = fmtCurrency(50000000)
      expect(result).toContain('50,000,000')
      expect(result).toContain('₪')
    })

    it('does not show decimal places', () => {
      const result = fmtCurrency(3000000.75)
      expect(result).not.toContain('.75')
      expect(result).toContain('3,000,001') // Should round
    })

    it('handles small decimals correctly', () => {
      const result = fmtCurrency(100.25)
      expect(result).toContain('100')
      expect(result).not.toContain('.25')
    })
  })

  describe('fmtNumber', () => {
    it('formats numbers with Hebrew locale separators', () => {
      expect(fmtNumber(1000)).toBe('1,000')
      expect(fmtNumber(1000000)).toBe('1,000,000')
    })

    it('handles zero correctly', () => {
      expect(fmtNumber(0)).toBe('0')
    })

    it('handles negative numbers', () => {
      const result = fmtNumber(-1500)
      expect(result).toContain('-1,500')
      // Hebrew locale may add direction marks
    })

    it('handles decimal numbers', () => {
      const result = fmtNumber(1234.56)
      expect(result).toContain('1,234.56')
    })

    it('handles very large numbers', () => {
      const result = fmtNumber(123456789)
      expect(result).toBe('123,456,789')
    })

    it('handles small numbers without separators', () => {
      expect(fmtNumber(123)).toBe('123')
      expect(fmtNumber(45)).toBe('45')
      expect(fmtNumber(7)).toBe('7')
    })
  })

  describe('fmtPct', () => {
    it('formats positive percentages with plus sign', () => {
      expect(fmtPct(5.2)).toBe('+5.2%')
      expect(fmtPct(10)).toBe('+10.0%')
      expect(fmtPct(0.5)).toBe('+0.5%')
    })

    it('formats negative percentages without extra sign', () => {
      expect(fmtPct(-3.7)).toBe('-3.7%')
      expect(fmtPct(-10)).toBe('-10.0%')
      expect(fmtPct(-0.1)).toBe('-0.1%')
    })

    it('formats zero correctly', () => {
      expect(fmtPct(0)).toBe('+0.0%')
    })

    it('formats to one decimal place', () => {
      expect(fmtPct(5.123)).toBe('+5.1%')
      expect(fmtPct(-2.987)).toBe('-3.0%')
      expect(fmtPct(10.95)).toBe('+10.9%') // Fixed: 10.95 rounds to 10.9, not 11.0
    })

    it('handles very small numbers', () => {
      expect(fmtPct(0.01)).toBe('+0.0%')
      expect(fmtPct(-0.01)).toBe('-0.0%')
    })

    it('handles large percentages', () => {
      expect(fmtPct(100)).toBe('+100.0%')
      expect(fmtPct(-50)).toBe('-50.0%')
      expect(fmtPct(250.75)).toBe('+250.8%')
    })

    it('handles undefined input', () => {
      // @ts-expect-error testing runtime behaviour with undefined
      expect(fmtPct(undefined)).toBe('—')
    })
  })

})
