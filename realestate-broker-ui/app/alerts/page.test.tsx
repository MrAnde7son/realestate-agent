/* eslint-env jest */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AlertsPage from './page';

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/dashboard-shell', () => ({
  DashboardShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DashboardHeader: ({ children, heading, text }: { children: React.ReactNode; heading: string; text: string }) => (
    <div>
      <h1>{heading}</h1>
      <p>{text}</p>
      {children}
    </div>
  ),
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
    
    // Check main content sections - wait for async rendering
    await waitFor(() => {
      expect(screen.getByText('התראות אחרונות')).toBeInTheDocument();
    });
    
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

  it('displays alert statistics correctly', async () => {
    render(<AlertsPage />);
    
    // Wait for the component to fully render
    await waitFor(() => {
      expect(screen.getByText('סטטיסטיקות מהירות')).toBeInTheDocument();
    });
    
    // Check that statistics are displayed
    expect(screen.getByText('סה״כ התראות')).toBeInTheDocument();
    expect(screen.getByText('לא נקראו')).toBeInTheDocument();
    expect(screen.getByText('היום')).toBeInTheDocument();
  });

  it('shows filter options for alerts', async () => {
    render(<AlertsPage />);
    
    // Wait for the component to fully render
    await waitFor(() => {
      expect(screen.getByText('סינון התראות')).toBeInTheDocument();
    });
    
    // Check priority filters
    expect(screen.getByText('עדיפות')).toBeInTheDocument();
    expect(screen.getByText('חשוב')).toBeInTheDocument();
    expect(screen.getByText('בינוני')).toBeInTheDocument();
    expect(screen.getByText('נמוך')).toBeInTheDocument();
    
    // Check type filters
    expect(screen.getByText('סוג התראה')).toBeInTheDocument();
  });

  it('renders alert items correctly', async () => {
    render(<AlertsPage />);
    
    // Wait for alerts to render
    await waitFor(() => {
      expect(screen.getByText('התראות אחרונות')).toBeInTheDocument();
    });
    
    // Check that some alert content is displayed
    expect(screen.getByText('ירידת מחיר בנכס')).toBeInTheDocument();
    expect(screen.getByText('נכס חדש התווסף')).toBeInTheDocument();
    expect(screen.getByText('שינוי בשוק הנדל״ן')).toBeInTheDocument();
  });

  it('displays the mark all as read button when there are unread alerts', async () => {
    render(<AlertsPage />);
    
    // Wait for the component to render
    await waitFor(() => {
      expect(screen.getByText('התראות אחרונות')).toBeInTheDocument();
    });
    
    // Check that the mark all as read button is present (since there are unread alerts)
    expect(screen.getByText(/סמן הכל כנקרא/)).toBeInTheDocument();
  });

  it('renders all expected text elements', async () => {
    render(<AlertsPage />);
    
    // Wait for the component to fully render
    await waitFor(() => {
      expect(screen.getByText('התראות אחרונות')).toBeInTheDocument();
    });
    
    // Check all the main text elements that should be visible
    const expectedTexts = [
      'התראות',
      'קבל עדכונים על שינויים בנכסים ובשוק הנדל״ן',
      'התראות אחרונות',
      'סוגי התראות',
      'סטטיסטיקות מהירות',
      'סינון התראות',
      'עדיפות',
      'סוג התראה',
      'ירידת מחיר',
      'נכס חדש',
      'שינוי בשוק',
      'עדכון מסמכים',
      'סטטוס היתרים'
    ];
    
    expectedTexts.forEach(text => {
      expect(screen.getByText(text)).toBeInTheDocument();
    });
  });
});
