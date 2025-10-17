import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import PlansTable from '@/components/PlansTable';

vi.mock('@/hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackFeatureUsage: vi.fn(),
  }),
}));

describe('PlansTable', () => {
  it('renders the plan title column and value when provided', () => {
    render(
      <PlansTable
        data={[
          {
            id: '1',
            plan_number: '123',
            title: 'תכנית מתאר',
            description: '',
            status: 'מאושר',
            source: 'rami',
          },
        ]}
      />
    );

    expect(screen.getByText('שם תוכנית')).toBeInTheDocument();
    expect(screen.getByText('תכנית מתאר')).toBeInTheDocument();
  });
});
