import React from 'react';
import { render, screen, cleanup } from '@testing-library/react';
import { afterEach, beforeAll } from 'vitest';
import AnalyticsClient from './AnalyticsClient';

beforeAll(() => {
  class MockResizeObserver {
    private callback: ResizeObserverCallback;

    constructor(callback: ResizeObserverCallback) {
      this.callback = callback;
    }

    observe(target: Element) {
      const width = (target as HTMLElement).clientWidth || 1200;
      const height = (target as HTMLElement).clientHeight || 800;

      this.callback(
        [
          {
            target,
            contentRect: {
              width,
              height,
              top: 0,
              left: 0,
              bottom: height,
              right: width,
              x: 0,
              y: 0,
            },
          } as ResizeObserverEntry,
        ],
        this,
      );
    }

    unobserve() {}

    disconnect() {}
  }

  // @ts-expect-error - jsdom does not implement ResizeObserver
  global.ResizeObserver = MockResizeObserver;
});

const renderWithDimensions = (ui: React.ReactElement) => {
  const container = document.createElement('div');
  Object.assign(container.style, {
    width: '1200px',
    height: '800px',
  });
  document.body.appendChild(container);

  const result = render(ui, { container });

  return {
    ...result,
    unmount: () => {
      result.unmount();
      if (container.parentNode) {
        container.parentNode.removeChild(container);
      }
    },
  };
};

afterEach(() => {
  cleanup();
});

const mockDailyData = [
  {
    date: '2024-01-01',
    users: 5,
    assets: 10,
    reports: 3,
    alerts: 7,
    errors: 1,
  },
  {
    date: '2024-01-02',
    users: 3,
    assets: 8,
    reports: 5,
    alerts: 4,
    errors: 0,
  },
];

const mockTopFailures = [
  {
    source: 'yad2',
    error_code: '500',
    count: 3,
  },
  {
    source: 'gis',
    error_code: 'timeout',
    count: 1,
  },
];

describe('AnalyticsClient', () => {
  it('displays alerts KPI card with correct data', () => {
    renderWithDimensions(<AnalyticsClient daily={mockDailyData} topFailures={mockTopFailures} />);
    
    // Check that the alerts card is displayed
    expect(screen.getByRole('heading', { name: 'התראות' })).toBeInTheDocument();
    expect(screen.getByText('11')).toBeInTheDocument(); // Total alerts: 7 + 4
    expect(screen.getByText('התראות שנוצרו')).toBeInTheDocument();
  });

  it('displays all KPI cards', () => {
    renderWithDimensions(<AnalyticsClient daily={mockDailyData} topFailures={mockTopFailures} />);
    
    // Check all KPI cards are present
    expect(screen.getByRole('heading', { name: 'משתמשים' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'נכסים' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'דוחות' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'התראות' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'שגיאות' })).toBeInTheDocument();
  });

  it('calculates totals correctly', () => {
    renderWithDimensions(<AnalyticsClient daily={mockDailyData} topFailures={mockTopFailures} />);
    
    // Check calculated totals - use getAllByText since numbers appear multiple times
    expect(screen.getAllByText('8').length).toBeGreaterThan(0); // Total users: 5 + 3
    expect(screen.getByText('18')).toBeInTheDocument(); // Total assets: 10 + 8
    expect(screen.getAllByText('8').length).toBeGreaterThan(0); // Total reports: 3 + 5
    expect(screen.getByText('11')).toBeInTheDocument(); // Total alerts: 7 + 4
    expect(screen.getAllByText('1').length).toBeGreaterThan(0); // Total errors: 1 + 0
  });

  it('handles empty data gracefully', () => {
    renderWithDimensions(<AnalyticsClient daily={[]} topFailures={[]} />);
    
    // Should still display the KPI cards with 0 values
    expect(screen.getByRole('heading', { name: 'התראות' })).toBeInTheDocument();
    expect(screen.getAllByText('0').length).toBeGreaterThan(0);
  });
});
