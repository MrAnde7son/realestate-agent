import { describe, expect, it } from 'vitest'

import { parseShareMessageResponse } from '@/app/assets/[id]/shareMessage'

describe('parseShareMessageResponse', () => {
  it('returns nulls when properties are missing', () => {
    const result = parseShareMessageResponse({})
    expect(result).toEqual({ text: null, shareUrl: null, isAIGenerated: false })
  })

  it('returns nulls when properties are blank strings', () => {
    const result = parseShareMessageResponse({ text: '   ', share_url: '' })
    expect(result).toEqual({ text: null, shareUrl: null, isAIGenerated: false })
  })

  it('extracts trimmed strings when present', () => {
    const result = parseShareMessageResponse({ text: ' message ', share_url: ' https://example.com ' })
    expect(result).toEqual({ text: 'message', shareUrl: 'https://example.com', isAIGenerated: false })
  })

  it('parses isAIGenerated correctly', () => {
    expect(parseShareMessageResponse({ is_ai_generated: true })).toEqual({ text: null, shareUrl: null, isAIGenerated: true })
    expect(parseShareMessageResponse({ is_ai_generated: false })).toEqual({ text: null, shareUrl: null, isAIGenerated: false })
    expect(parseShareMessageResponse({ is_ai_generated: 'true' })).toEqual({ text: null, shareUrl: null, isAIGenerated: false })
  })

  it('ignores non-string values', () => {
    const result = parseShareMessageResponse({ text: 123, share_url: false })
    expect(result).toEqual({ text: null, shareUrl: null, isAIGenerated: false })
  })

  it('guards against non-object inputs', () => {
    expect(parseShareMessageResponse(null)).toEqual({ text: null, shareUrl: null, isAIGenerated: false })
    expect(parseShareMessageResponse(undefined)).toEqual({ text: null, shareUrl: null, isAIGenerated: false })
    expect(parseShareMessageResponse('text')).toEqual({ text: null, shareUrl: null, isAIGenerated: false })
  })
})
