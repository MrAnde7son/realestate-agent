// @vitest-environment jsdom
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { describe, it, expect, vi } from 'vitest'
import AssetsTable from './AssetsTable'

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
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

  it('passes selected assets to bulk action handlers', async () => {
    const actionSpy = vi.fn()
    render(
      <AssetsTable
        data={[
          { id: 1, address: 'Asset 1', city: 'City' } as any,
          { id: 2, address: 'Asset 2', city: 'City' } as any,
        ]}
        bulkActions={[
          {
            label: 'Bulk Action',
            action: (selected, helpers) => actionSpy(selected, helpers),
          },
        ]}
      />
    )

    await waitFor(() => {
      expect(screen.getByRole('columnheader', { name: 'נכס' })).toBeInTheDocument()
    })

    const rowCheckboxes = screen.getAllByRole('checkbox', { name: /בחר נכס/ })
    fireEvent.click(rowCheckboxes[0])

    const bulkButton = await screen.findByRole('button', { name: /פעולות/ })
    fireEvent.pointerDown(bulkButton)
    fireEvent.keyDown(bulkButton, { key: 'Enter', code: 'Enter', charCode: 13 })

    const actionItem = await screen.findByRole('menuitemcheckbox', { name: 'Bulk Action' })
    fireEvent.click(actionItem)

    expect(actionSpy).toHaveBeenCalledTimes(1)
    const [selected, helpers] = actionSpy.mock.calls[0]
    expect(selected).toHaveLength(1)
    expect(selected[0].id).toBe(1)
    expect(typeof helpers.clearSelection).toBe('function')
  })
})
