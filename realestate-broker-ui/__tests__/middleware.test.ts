import { describe, it, expect } from 'vitest'
import { NextRequest } from 'next/server'

import { proxy } from '../proxy'

function createRequest(pathname: string) {
  return new NextRequest(`http://example.com${pathname}`)
}

describe('middleware route protection', () => {
  it('allows unauthenticated access to the mortgage analyzer', async () => {
    const response = await proxy(createRequest('/mortgage/analyze'))

    expect(response?.status).toBe(200)
    expect(response?.headers.get('location')).toBeNull()
  })

  it('continues to protect authenticated-only sections', async () => {
    const response = await proxy(createRequest('/alerts'))

    expect(response?.status).toBe(307)
    expect(response?.headers.get('location')).toBe('http://example.com/auth')
  })
})
