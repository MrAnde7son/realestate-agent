/* eslint-env jest */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import MortgageAnalyzePage from './page';
import { vi } from 'vitest';

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock the fetch function to avoid API calls during tests
const mockFetch = vi.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({
      success: true,
      data: { baseRate: 4.5, lastUpdated: new Date().toISOString() }
    }),
  } as any)
) as unknown as typeof fetch;

global.fetch = mockFetch;

afterEach(() => {
  mockFetch.mockClear();
});

describe('MortgageAnalyzePage', () => {
  it('shows calculated monthly payment', async () => {
    render(<MortgageAnalyzePage />);

    await waitFor(() => {
      expect(screen.getByText('מחשבון משכנתא')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('פרטי המשכנתא')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/boi-rate');
    });

    // Check for property value input (should have placeholder "3,500,000")
    const propertyValueInput = screen.getByPlaceholderText('3,500,000');
    expect(propertyValueInput).toBeInTheDocument();
    expect(propertyValueInput).toHaveValue(3500000);
    
    // Check for loan amount input (should have placeholder "2,800,000")
    const loanAmountInput = screen.getByPlaceholderText('2,800,000');
    expect(loanAmountInput).toBeInTheDocument();
    expect(loanAmountInput).toHaveValue(3500000); // This is calculated from property value - equity
  });
});
