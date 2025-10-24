// @vitest-environment jsdom
import React from 'react'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
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

  it('shows a table body loading skeleton while keeping headers visible', async () => {
    render(
      <AssetsTable
        data={[{ id: 1, address: 'Asset 1', city: 'City' } as any]}
        loading
      />
    )

    await waitFor(() => {
      expect(screen.getByRole('columnheader', { name: 'נכס' })).toBeInTheDocument()
    })

    const loadingBody = await screen.findByTestId('assets-table-loading-body')
    expect(loadingBody).toHaveAttribute('aria-busy', 'true')

    const loadingRows = within(loadingBody).getAllByRole('row')
    expect(loadingRows.length).toBeGreaterThan(0)
  })

  it('renders listing metadata columns when provided', async () => {
    render(
      <AssetsTable
        data={[
          {
            id: 1,
            address: 'Asset 1',
            listingType: 'rent',
            contactName: 'Dana',
            contactPhone: '050-1234567',
            recentDeal: true,
            videoUrl: 'http://example.com/video.mp4',
          } as any,
        ]}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('השכרה')).toBeInTheDocument()
    })
    expect(screen.getByText('Dana')).toBeInTheDocument()
    expect(screen.getByText('050-1234567')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'פתח וידאו' })).toBeInTheDocument()
    expect(screen.getAllByText('כן')[0]).toBeInTheDocument()
  })
})
