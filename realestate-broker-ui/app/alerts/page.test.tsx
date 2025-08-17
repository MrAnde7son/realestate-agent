/* eslint-env jest */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import AlertsPage from './page';
import { vi } from 'vitest';

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe('AlertsPage', () => {
  it('renders alert rule form', () => {
    render(<AlertsPage />);
    expect(screen.getByText('חוקי התראות')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('3–4 חד בת״א עד 8.5מיל ללא סיכון')).toBeInTheDocument();
  });
});
