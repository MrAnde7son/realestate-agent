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
  beforeEach(() => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({ rows: [] }),
      } as any)
    ) as any;
  });

  it('renders alerts page with all main components', async () => {
    render(<AlertsPage />);
    
    // Check main page title
    expect(screen.getByText('התראות')).toBeInTheDocument();
    
    // Check main content sections
    expect(await screen.findByText('התראות אחרונות')).toBeInTheDocument();
    expect(screen.getByText('סוגי התראות')).toBeInTheDocument();
    
    // Check sidebar content
    expect(screen.getByText('סטטיסטיקות מהירות')).toBeInTheDocument();
    expect(screen.getByText('סינון התראות')).toBeInTheDocument();
    
    // Check alert type icons
    expect(screen.getByText('ירידת מחיר')).toBeInTheDocument();
    expect(screen.getByText('נכס חדש')).toBeInTheDocument();
    expect(screen.getByText('שינוי בשוק')).toBeInTheDocument();
    expect(screen.getByText('עדכון מסמכים')).toBeInTheDocument();
    expect(screen.getByText('סטטוס היתרים')).toBeInTheDocument();
  });

  it('displays alert statistics correctly', () => {
    render(<AlertsPage />);
    
    // Check that statistics are displayed
    expect(screen.getByText('סה״כ התראות')).toBeInTheDocument();
    expect(screen.getByText('לא נקראו')).toBeInTheDocument();
    expect(screen.getByText('היום')).toBeInTheDocument();
  });

  it('shows filter options for alerts', () => {
    render(<AlertsPage />);
    
    // Check priority filters
    expect(screen.getByText('עדיפות')).toBeInTheDocument();
    expect(screen.getByText('חשוב')).toBeInTheDocument();
    expect(screen.getByText('בינוני')).toBeInTheDocument();
    expect(screen.getByText('נמוך')).toBeInTheDocument();
    
    // Check type filters
    expect(screen.getByText('סוג התראה')).toBeInTheDocument();
  });
});
