import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import AnalyticsClient from './AnalyticsClient';

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
  let originalOffsetHeight: PropertyDescriptor | undefined;
  let originalOffsetWidth: PropertyDescriptor | undefined;
  let originalGetBoundingClientRect: typeof HTMLElement.prototype.getBoundingClientRect;

  beforeAll(() => {
    originalOffsetHeight = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetHeight');
    originalOffsetWidth = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetWidth');
    originalGetBoundingClientRect = HTMLElement.prototype.getBoundingClientRect;

    Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
      configurable: true,
      get() {
        return 480;
      },
    });

    Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
      configurable: true,
      get() {
        return 640;
      },
    });

    HTMLElement.prototype.getBoundingClientRect = () => ({
      width: 640,
      height: 480,
      top: 0,
      left: 0,
      right: 640,
      bottom: 480,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    } as DOMRect);
  });

  afterAll(() => {
    if (originalOffsetHeight) {
      Object.defineProperty(HTMLElement.prototype, 'offsetHeight', originalOffsetHeight);
    } else {
      delete (HTMLElement.prototype as any).offsetHeight;
    }

    if (originalOffsetWidth) {
      Object.defineProperty(HTMLElement.prototype, 'offsetWidth', originalOffsetWidth);
    } else {
      delete (HTMLElement.prototype as any).offsetWidth;
    }

    HTMLElement.prototype.getBoundingClientRect = originalGetBoundingClientRect;
  });

  it('displays alerts KPI card with correct data', () => {
    render(<AnalyticsClient daily={mockDailyData} topFailures={mockTopFailures} />);

    // Check that the alerts card is displayed
    expect(screen.getAllByText('התראות').length).toBeGreaterThan(0);
    expect(screen.getByText('11')).toBeInTheDocument(); // Total alerts: 7 + 4
    expect(screen.getByText('התראות שנוצרו')).toBeInTheDocument();
  });

  it('displays all KPI cards', () => {
    render(<AnalyticsClient daily={mockDailyData} topFailures={mockTopFailures} />);

    // Check all KPI cards are present
    expect(screen.getAllByText('משתמשים').length).toBeGreaterThan(0);
    expect(screen.getAllByText('נכסים').length).toBeGreaterThan(0);
    expect(screen.getAllByText('דוחות').length).toBeGreaterThan(0);
    expect(screen.getAllByText('התראות').length).toBeGreaterThan(0);
    expect(screen.getAllByText('שגיאות').length).toBeGreaterThan(0);
  });

  it('calculates totals correctly', () => {
    render(<AnalyticsClient daily={mockDailyData} topFailures={mockTopFailures} />);
    
    // Check calculated totals - use getAllByText since numbers appear multiple times
    expect(screen.getAllByText('8').length).toBeGreaterThan(0); // Total users: 5 + 3
    expect(screen.getByText('18')).toBeInTheDocument(); // Total assets: 10 + 8
    expect(screen.getAllByText('8').length).toBeGreaterThan(0); // Total reports: 3 + 5
    expect(screen.getByText('11')).toBeInTheDocument(); // Total alerts: 7 + 4
    expect(screen.getAllByText('1').length).toBeGreaterThan(0); // Total errors: 1 + 0
  });

  it('handles empty data gracefully', async () => {
    render(<AnalyticsClient daily={[]} topFailures={[]} />);

    await waitFor(() => {
      expect(screen.getAllByText('התראות').length).toBeGreaterThan(0);
    });
    await waitFor(() => {
      expect(screen.getAllByText('0').length).toBeGreaterThan(0);
    });
  });
});
