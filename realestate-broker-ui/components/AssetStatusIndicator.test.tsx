import React from 'react'
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import AssetStatusIndicator from './AssetStatusIndicator'

describe('AssetStatusIndicator', () => {
  it('renders loader state for pending assets', () => {
    const { container } = render(<AssetStatusIndicator status="pending" />)

    expect(screen.getByText('מכין נתונים על הנכס')).toBeInTheDocument()
    expect(container.querySelector('svg.animate-spin')).toBeInTheDocument()
  })

  it('renders failure badge when enrichment fails', () => {
    const { container } = render(<AssetStatusIndicator status="failed" />)

    expect(screen.getByText('שגיאה באיסוף')).toBeInTheDocument()
    expect(container.querySelector('.bg-error')).not.toBeNull()
  })

  it('hides itself for done or unknown statuses', () => {
    const { container, rerender } = render(<AssetStatusIndicator status="done" />)

    expect(container).toBeEmptyDOMElement()

    rerender(<AssetStatusIndicator status={'active' as any} />)
    expect(container).toBeEmptyDOMElement()
  })
})
