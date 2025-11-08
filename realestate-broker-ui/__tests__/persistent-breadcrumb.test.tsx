import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PersistentBreadcrumb } from '@/components/ui/persistent-breadcrumb'

declare global {
  interface WindowEventMap {
    keydown: KeyboardEvent
  }
}

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

describe('PersistentBreadcrumb', () => {
  const baseItems = [
    { label: 'נכסים', href: '/assets' },
    { label: 'רחוב החירות 10' },
    { label: 'מסמכים' },
  ] as const

  it('allows collapsing and expanding via the action buttons', () => {
    render(<PersistentBreadcrumb items={[...baseItems]} showBackToAssets />)

    expect(screen.getByRole('region', { name: 'נתיב ניווט' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'הסתר נתיב ניווט' }))

    expect(screen.queryByRole('region', { name: 'נתיב ניווט' })).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'הצג נתיב ניווט' }))

    expect(screen.getByRole('region', { name: 'נתיב ניווט' })).toBeInTheDocument()
  })

  it('restores visibility and focuses the breadcrumb region when Cmd/Ctrl + B is pressed', async () => {
    render(<PersistentBreadcrumb items={[...baseItems]} />)

    fireEvent.click(screen.getByRole('button', { name: 'הסתר נתיב ניווט' }))

    fireEvent.keyDown(window, { key: 'b', metaKey: true })

    const regionAfterMeta = await screen.findByRole('region', { name: 'נתיב ניווט' })
    await waitFor(() => expect(regionAfterMeta).toHaveFocus())

    fireEvent.click(screen.getByRole('button', { name: 'הסתר נתיב ניווט' }))

    fireEvent.keyDown(window, { key: 'b', ctrlKey: true })

    const regionAfterCtrl = await screen.findByRole('region', { name: 'נתיב ניווט' })
    await waitFor(() => expect(regionAfterCtrl).toHaveFocus())
  })

  it('renders a borderless, mobile-first layout for controls', () => {
    render(
      <PersistentBreadcrumb
        items={[...baseItems]}
        showBackToAssets
        tabContext={{
          currentTab: 'documents',
          tabs: [
            { value: 'overview', label: 'סקירה' },
            { value: 'documents', label: 'מסמכים' },
          ],
        }}
      />
    )

    const region = screen.getByRole('region', { name: 'נתיב ניווט' })
    expect(region).toHaveClass('flex-col')
    expect(region.className).toContain('sm:flex-row')
    expect(region.className).not.toMatch(/border/)

    const collapseButton = screen.getByRole('button', { name: 'הסתר נתיב ניווט' })
    const controlsContainer = collapseButton.parentElement
    expect(controlsContainer).toBeTruthy()
    expect(controlsContainer).toHaveClass('flex-wrap')
    expect(controlsContainer?.className ?? '').toContain('sm:flex-nowrap')

    const tabButton = screen.getByRole('button', { name: 'מסמכים' })
    expect(tabButton.className).toContain('w-full')
    expect(tabButton.className).toContain('sm:w-auto')
  })
})
