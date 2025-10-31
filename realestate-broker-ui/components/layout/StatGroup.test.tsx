// @vitest-environment jsdom
import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { describe, it, expect } from 'vitest'
import StatGroup, { StatGroupItem } from './StatGroup'

describe('StatGroup', () => {
  it('arranges stats in a responsive grid with tone and trend styles', () => {
    render(
      <StatGroup data-testid="stat-group" columns={2}>
        <StatGroup.Item
          label="הכנסה חודשית"
          value="₪12,000"
          helperText="+12% לעומת החודש הקודם"
          tone="positive"
          trend={{ direction: 'up', label: '+12%' }}
        />
        <StatGroupItem
          label="שיעור נטישה"
          value="4.2%"
          tone="negative"
          trend={{ direction: 'down', label: '-0.4%' }}
        >
          <span data-testid="stat-children">תוספת</span>
        </StatGroupItem>
      </StatGroup>
    )

    const group = screen.getByTestId('stat-group')
    const grid = group.querySelector('div')
    expect(grid).toHaveClass('grid', 'sm:grid-cols-2')

    expect(screen.getByText('₪12,000')).toHaveClass('text-success')
    expect(screen.getByText('4.2%')).toHaveClass('text-destructive')

    const trends = screen.getAllByTestId('stat-group-trend')
    expect(trends).toHaveLength(2)
    expect(trends[0]).toHaveTextContent('+12%')
    expect(trends[1]).toHaveTextContent('-0.4%')

    expect(screen.getByTestId('stat-children')).toBeInTheDocument()
    expect(screen.getAllByTestId('stat-group-helper')[0]).toHaveTextContent('+12% לעומת החודש הקודם')
  })
})
