import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import ImportHistoryPage from '@/app/imports/page'

const toastMock = vi.fn()

vi.mock('@/components/layout/dashboard-layout', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: toastMock }),
}))

describe('ImportHistoryPage', () => {
  beforeEach(() => {
    toastMock.mockReset()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows guidance steps and empty state alert', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({ results: [] }),
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<ImportHistoryPage />)

    expect(await screen.findByText('כיצד מתבצע הייבוא?')).toBeInTheDocument()
    expect(
      screen.getByText('התחילו תהליך ייבוא חדש ממסך הייבוא, או חזרו לכאן לאחר שהדאטה סונכרנה.')
    ).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/imports', expect.any(Object))
  })

  it('renders inline error alert and triggers destructive toast', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      json: vi.fn().mockResolvedValue({ error: 'שגיאת שרת' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<ImportHistoryPage />)

    expect(await screen.findByText('שגיאת שרת')).toBeInTheDocument()

    await waitFor(() => {
      expect(toastMock).toHaveBeenCalledWith(
        expect.objectContaining({
          variant: 'destructive',
          description: 'שגיאת שרת',
        })
      )
    })
  })
})
