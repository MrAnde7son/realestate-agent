/* eslint-env jest */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ListingDetail from './page';
import { vi } from 'vitest';

vi.mock('next/link', () => ({
  default: ({ children, href, ...rest }: any) => <a href={href} {...rest}>{children}</a>,
}));

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const push = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push }),
}));

describe('ListingDetail', () => {
  it('calls report generation endpoint', async () => {
    const sampleListing = {
      id: '1',
      address: 'Demo St 1',
      city: 'Tel Aviv',
      type: 'house',
      netSqm: 100,
      documents: [],
      confidencePct: 80,
      capRatePct: 5,
      priceGapPct: 0,
      remainingRightsSqm: 0,
      noiseLevel: 3,
      price: 1000000,
    };
    const fetchMock = vi.fn((url: string) => {
      if (url === '/api/listings/1') {
        return Promise.resolve({
          json: () => Promise.resolve({ listing: sampleListing }),
        });
      }
      if (url === '/api/reports') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      }
      return Promise.reject(new Error('unknown url'));
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<ListingDetail params={Promise.resolve({ id: '1' })} />);

    const button = await screen.findByRole('button', { name: 'צור דוח' });
    fireEvent.click(button);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/reports', expect.any(Object));
      expect(push).toHaveBeenCalledWith('/reports');
    });
  });
});
