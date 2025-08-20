/* eslint-env jest */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ListingsPage from './page';
import type { Listing } from '@/lib/data';
import { vi } from 'vitest';
import { AuthProvider } from '@/lib/auth-context';

vi.mock('next/link', () => ({
  default: ({ children, href, ...rest }: any) => <a href={href} {...rest}>{children}</a>,
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe('ListingsPage', () => {
  it('loads and displays listings from the API', async () => {
    const sampleListings: Listing[] = [
      {
        id: '1',
        address: 'Demo St 1',
        price: 1000000,
        bedrooms: 3,
        bathrooms: 2,
        area: 80,
        type: 'דירה',
        status: 'active',
        images: [],
        description: '',
        features: [],
        contactInfo: { agent: '', phone: '', email: '' },
        city: 'תל אביב',
        netSqm: 80,
      },
    ];

    const fetchMock = vi.fn().mockResolvedValue({
      json: () => Promise.resolve({ rows: sampleListings }),
    });
    vi.stubGlobal('fetch', fetchMock);

    render(
      <AuthProvider>
        <ListingsPage />
      </AuthProvider>
    );

    expect(await screen.findByText('Demo St 1')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith('/api/listings');
  });
});
