import { render, screen } from '@testing-library/react';
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
  it('displays alerts KPI card with correct data', () => {
    render(<AnalyticsClient daily={mockDailyData} topFailures={mockTopFailures} />);
    
    // Check that the alerts card is displayed
    expect(screen.getByText('התראות')).toBeInTheDocument();
    expect(screen.getByText('11')).toBeInTheDocument(); // Total alerts: 7 + 4
    expect(screen.getByText('התראות שנוצרו')).toBeInTheDocument();
  });

  it('displays all KPI cards', () => {
    render(<AnalyticsClient daily={mockDailyData} topFailures={mockTopFailures} />);
    
    // Check all KPI cards are present
    expect(screen.getByText('משתמשים')).toBeInTheDocument();
    expect(screen.getByText('נכסים')).toBeInTheDocument();
    expect(screen.getByText('דוחות')).toBeInTheDocument();
    expect(screen.getByText('התראות')).toBeInTheDocument();
    expect(screen.getByText('שגיאות')).toBeInTheDocument();
  });

  it('calculates totals correctly', () => {
    render(<AnalyticsClient daily={mockDailyData} topFailures={mockTopFailures} />);
    
    // Check calculated totals
    expect(screen.getByText('8')).toBeInTheDocument(); // Total users: 5 + 3
    expect(screen.getByText('18')).toBeInTheDocument(); // Total assets: 10 + 8
    expect(screen.getByText('8')).toBeInTheDocument(); // Total reports: 3 + 5
    expect(screen.getByText('11')).toBeInTheDocument(); // Total alerts: 7 + 4
    expect(screen.getByText('1')).toBeInTheDocument(); // Total errors: 1 + 0
  });

  it('handles empty data gracefully', () => {
    render(<AnalyticsClient daily={[]} topFailures={[]} />);
    
    // Should still display the KPI cards with 0 values
    expect(screen.getByText('התראות')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
  });
});
