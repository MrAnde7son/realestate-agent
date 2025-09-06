// @vitest-environment jsdom
import React from 'react'
import { render } from '@testing-library/react'
import '@testing-library/jest-dom'
import { describe, it, expect, vi } from 'vitest'
import AssetsTable from './AssetsTable'

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() })
}))

vi.mock('next/link', () => ({
  default: ({ children, ...props }: any) => <a {...props}>{children}</a>
}))

describe('AssetsTable', () => {
  it('renders placeholders for missing optional fields', () => {
    const { container } = render(<AssetsTable data={[{ id: 1, address: 'Empty' } as any]} />)
    expect(container.textContent).not.toContain('undefined')
    expect(container.textContent).not.toContain('NaN')
    expect(container.textContent).toContain('—')
  })
})
