import { describe, expect, it, beforeEach } from 'vitest'
import {
  buildCssVariableDeclaration,
  buildResolvedCssVariableDeclaration,
  chartColorPalette,
  colorVar,
  hslColorVar,
  hslColorVarWithAlpha,
  resolveColorValue,
} from '@/lib/design-tokens'

describe('design tokens', () => {
  beforeEach(() => {
    document.documentElement.style.cssText = ''
  })

  it('exposes CSS variable fallbacks for brand colors', () => {
    expect(colorVar('brandBlue')).toBe('var(--brand-blue, #2563eb)')
    expect(hslColorVar('chart1')).toBe('hsl(var(--chart-1, 12 76% 61%))')
  })

  it('supports alpha adjustments for HSL tokens', () => {
    expect(hslColorVarWithAlpha('chart1', 0.25)).toBe('hsl(var(--chart-1, 12 76% 61%) / 0.25)')
    expect(hslColorVarWithAlpha('chart1', 2)).toBe('hsl(var(--chart-1, 12 76% 61%) / 1)')
    expect(hslColorVarWithAlpha('chart1', -1)).toBe('hsl(var(--chart-1, 12 76% 61%) / 0)')
  })

  it('provides a consistent chart palette', () => {
    expect(chartColorPalette()).toEqual([
      'hsl(var(--chart-1, 12 76% 61%))',
      'hsl(var(--chart-2, 173 58% 39%))',
      'hsl(var(--chart-3, 197 37% 24%))',
      'hsl(var(--chart-4, 43 74% 66%))',
      'hsl(var(--chart-5, 27 87% 67%))',
    ])
  })

  it('builds CSS variable declarations with fallbacks', () => {
    const css = buildCssVariableDeclaration()
    expect(css.startsWith(':root {')).toBe(true)
    expect(css).toContain('--brand-blue: #2563eb;')
    expect(css).toContain('--chart-1: 12 76% 61%;')
  })

  it('resolves runtime variable declarations using computed styles', () => {
    document.documentElement.style.setProperty('--brand-blue', '#123456')
    document.documentElement.style.setProperty('--chart-1', '200 50% 40%')

    expect(resolveColorValue('brandBlue')).toBe('#123456')
    expect(resolveColorValue('chart1')).toBe('hsl(200 50% 40%)')

    const resolvedCss = buildResolvedCssVariableDeclaration()
    expect(resolvedCss).toContain('--brand-blue: #123456;')
    expect(resolvedCss).toContain('--chart-1: 200 50% 40%;')
  })
})
