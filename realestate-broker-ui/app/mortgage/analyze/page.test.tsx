/* eslint-env jest */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import MortgageAnalyzePage from './page';
import { vi } from 'vitest';

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe('MortgageAnalyzePage', () => {
  it('shows calculated monthly payment', () => {
    render(<MortgageAnalyzePage />);
    expect(screen.getByText('אנליזת משכנתא')).toBeInTheDocument();
    expect(screen.getAllByText('₪19,821')[0]).toBeInTheDocument();
  });
});
