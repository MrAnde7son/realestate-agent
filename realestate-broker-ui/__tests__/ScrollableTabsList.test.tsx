import React from 'react'
import { act, fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Tabs, TabsContent, TabsTrigger } from '@/components/ui/tabs'
import { ScrollableTabsList } from '@/components/navigation/ScrollableTabsList'

describe('ScrollableTabsList', () => {
  const renderTabs = () =>
    render(
      <Tabs defaultValue="tab-1">
        <ScrollableTabsList aria-label="טאבים נגללים">
          {Array.from({ length: 8 }).map((_, index) => (
            <TabsTrigger key={index} value={`tab-${index + 1}`}>
              Tab {index + 1}
            </TabsTrigger>
          ))}
        </ScrollableTabsList>
        <TabsContent value="tab-1">Tab one content</TabsContent>
      </Tabs>
    )

  it('shows scroll buttons when overflowing and allows navigation', async () => {
    renderTabs()

    const tabList = screen.getByRole('tablist') as HTMLDivElement & { scrollLeft: number }
    let scrollLeftValue = 0

    Object.defineProperty(tabList, 'scrollWidth', { value: 1200, configurable: true })
    Object.defineProperty(tabList, 'clientWidth', { value: 400, configurable: true })
    Object.defineProperty(tabList, 'scrollLeft', {
      configurable: true,
      get: () => scrollLeftValue,
      set: (value: number) => {
        scrollLeftValue = value
      },
    })

    tabList.scrollBy = ({ left }: ScrollToOptions) => {
      scrollLeftValue += typeof left === 'number' ? left : 0
      tabList.dispatchEvent(new Event('scroll'))
    }

    await act(async () => {
      window.dispatchEvent(new Event('resize'))
    })

    const forwardButton = screen.getByRole('button', { name: /גלול קדימה/ })
    const backButton = screen.getByRole('button', { name: /גלול אחורה/ })

    expect(forwardButton).toBeEnabled()
    expect(backButton).toBeDisabled()

    fireEvent.click(forwardButton)
    expect(scrollLeftValue).toBeGreaterThan(0)
    expect(backButton).toBeEnabled()

    await act(async () => {
      scrollLeftValue = 800
      tabList.dispatchEvent(new Event('scroll'))
    })

    expect(forwardButton).toBeDisabled()
  })
})
