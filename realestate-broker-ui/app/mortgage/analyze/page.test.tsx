/* eslint-env jest */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import MortgageAnalyzePage from './page';
import { vi } from 'vitest';

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock the fetch function to avoid API calls during tests
global.fetch = vi.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({
      success: true,
      data: { baseRate: 4.5, lastUpdated: new Date().toISOString() }
    }),
  } as any)
) as any;

describe('MortgageAnalyzePage', () => {
  it('shows calculated monthly payment', () => {
    render(<MortgageAnalyzePage />);
    expect(screen.getByText('מחשבון משכנתא')).toBeInTheDocument();
    expect(screen.getByText('פרטי המשכנתא')).toBeInTheDocument();
    expect(screen.getByDisplayValue('3500000')).toBeInTheDocument();
    expect(screen.getByDisplayValue('2800000')).toBeInTheDocument();
  });
});
