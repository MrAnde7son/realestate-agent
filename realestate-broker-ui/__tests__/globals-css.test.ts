import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const globalsCssPath = path.join(__dirname, '..', 'app', 'globals.css')

const getOverflowXAutoBlock = (css: string) => {
  const match = css.match(/\.overflow-x-auto\s*{[^}]*}/s)
  return match?.[0] ?? ''
}

describe('global mobile touch handling', () => {
  const cssContents = readFileSync(globalsCssPath, 'utf8')

  it('allows pinch-zooming inside horizontal scroll areas', () => {
    const overflowBlock = getOverflowXAutoBlock(cssContents)
    expect(overflowBlock).toContain('touch-action: pan-x pinch-zoom;')
  })
})
