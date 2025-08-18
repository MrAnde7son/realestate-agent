/* eslint-env jest */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ReportsPage from './page';
import { vi } from 'vitest';

vi.mock('next/link', () => ({
  default: ({ children, href, ...rest }: any) => <a href={href} {...rest}>{children}</a>,
}));

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe('ReportsPage', () => {
  it('loads and displays reports from the API', async () => {
    const sampleReports = [
      { id: 'r1', listingId: 'l1', address: 'Demo St 1', filename: 'r1.pdf', createdAt: new Date().toISOString() }
    ];

    const fetchMock = vi.fn().mockResolvedValue({
      json: () => Promise.resolve({ reports: sampleReports })
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<ReportsPage />);
    expect(await screen.findByText('Demo St 1')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith('/api/reports');
  });
});
