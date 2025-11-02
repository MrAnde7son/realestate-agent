// @vitest-environment jsdom
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import type { Table } from '@tanstack/react-table'
import TablePagination from './TablePagination'

describe('TablePagination', () => {
  beforeAll(() => {
    Object.defineProperty(window.HTMLElement.prototype, 'scrollIntoView', {
      configurable: true,
      value: vi.fn(),
    })
  })

  it('always shows the current page size as a selectable option', async () => {
    const tableMock = {
      getState: () => ({ pagination: { pageIndex: 0, pageSize: 25 } }),
      getPageCount: () => 1,
      getRowCount: () => 50,
      previousPage: vi.fn(),
      getCanPreviousPage: () => false,
      nextPage: vi.fn(),
      getCanNextPage: () => false,
      setPageSize: vi.fn(),
    } as unknown as Table<unknown>

    render(<TablePagination table={tableMock} pageSizeOptions={[10, 50, 100]} />)

    const trigger = screen.getByRole('combobox')
    fireEvent.click(trigger)

    const option = await screen.findByRole('option', { name: '25' })
    expect(option).toBeInTheDocument()
  })
})
