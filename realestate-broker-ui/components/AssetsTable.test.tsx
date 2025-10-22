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

  it('renders quick filter buttons and triggers callbacks', async () => {
    const onStatusChange = vi.fn()
    const onRiskChange = vi.fn()
    const onDocumentsChange = vi.fn()

    render(
      <AssetsTable
        data={[{ id: 1, address: 'Asset 1', city: 'City' } as any]}
        filters={{
          city: { value: 'all', onChange: vi.fn(), options: [] },
          type: { value: 'all', onChange: vi.fn(), options: [] },
          priceMin: { value: undefined, onChange: vi.fn() },
          priceMax: { value: undefined, onChange: vi.fn() },
          status: {
            value: 'all',
            onChange: onStatusChange,
            options: [{ value: 'done', label: 'מוכן', count: 2 }],
          },
          risk: {
            value: 'all',
            onChange: onRiskChange,
            options: [
              { value: 'flagged', label: 'עם דגלי סיכון' },
              { value: 'clean', label: 'ללא דגלי סיכון' },
            ],
          },
          documents: {
            value: 'all',
            onChange: onDocumentsChange,
            options: [
              { value: 'with', label: 'עם מסמכים' },
              { value: 'without', label: 'ללא מסמכים' },
            ],
          },
          rentalSale: {
            value: 'all',
            onChange: vi.fn(),
            options: [
              { value: 'rental', label: 'השכרה' },
              { value: 'sale', label: 'מכירה' },
            ],
          },
          userAssets: {
            value: 'all',
            onChange: vi.fn(),
            options: [
              { value: 'mine', label: 'נכסים שלי' },
              { value: 'others', label: 'נכסים של אחרים' },
            ],
          },
        }}
      />
    )

    const riskButton = await screen.findByRole('button', { name: 'עם דגלי סיכון' })
    expect(riskButton).toBeInTheDocument()

    fireEvent.click(riskButton)
    expect(onRiskChange).toHaveBeenCalledWith('flagged')

    expect(screen.getByRole('button', { name: /כל הסטטוסים/ })).toBeInTheDocument()

    const statusButton = screen.getByRole('button', { name: /מוכן/ })
    fireEvent.click(statusButton)
    expect(onStatusChange).toHaveBeenCalledWith('done')

    const documentsButton = screen.getByRole('button', { name: 'עם מסמכים' })
    fireEvent.click(documentsButton)
    expect(onDocumentsChange).toHaveBeenCalledWith('with')
  })
})
