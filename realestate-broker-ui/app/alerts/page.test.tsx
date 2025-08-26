/* eslint-env jest */
import React from 'react';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
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
    
    // Check alert type icons - use getAllByText since these appear in multiple places
    // Check that the text exists at least once (more flexible assertion)
    expect(screen.getAllByText('ירידת מחיר').length).toBeGreaterThan(0);
    expect(screen.getAllByText('נכס חדש').length).toBeGreaterThan(0);
    expect(screen.getAllByText('שינוי בשוק').length).toBeGreaterThan(0);
    expect(screen.getAllByText('עדכון מסמכים').length).toBeGreaterThan(0);
    expect(screen.getAllByText('סטטוס היתרים').length).toBeGreaterThan(0);
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
    // Use getAllByText since priority badges appear multiple times
    // Check that the text exists at least once (more flexible assertion)
    expect(screen.getAllByText('חשוב').length).toBeGreaterThan(0);
    expect(screen.getAllByText('בינוני').length).toBeGreaterThan(0);
    expect(screen.getAllByText('נמוך').length).toBeGreaterThan(0);
    
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

  it('filters alerts by priority and type selections', async () => {
    render(<AlertsPage />);

    await waitFor(() => {
      expect(screen.getByText('התראות אחרונות')).toBeInTheDocument();
    });

    const filterCard = screen.getByText('סינון התראות').parentElement!.parentElement!;
    const highPriorityBadge = within(filterCard).getByText('חשוב');
    fireEvent.click(highPriorityBadge);

    const alertsCard = screen
      .getByText('התראות אחרונות')
      .parentElement!.parentElement!.parentElement!;
    expect(within(alertsCard).queryByText('נכס חדש התווסף')).not.toBeInTheDocument();

    const priceDropBadge = within(filterCard).getByText('ירידת מחיר');
    fireEvent.click(priceDropBadge);

    expect(within(alertsCard).getByText('ירידת מחיר בנכס')).toBeInTheDocument();
    expect(within(alertsCard).queryByText('עדכון מסמכים')).not.toBeInTheDocument();
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
      'סוג התראה'
    ];
    
    expectedTexts.forEach(text => {
      expect(screen.getByText(text)).toBeInTheDocument();
    });
    
    // Check that alert type texts exist (they appear multiple times, so use getAllByText)
    const alertTypes = ['ירידת מחיר', 'נכס חדש', 'שינוי בשוק', 'עדכון מסמכים', 'סטטוס היתרים'];
    alertTypes.forEach(text => {
      expect(screen.getAllByText(text).length).toBeGreaterThan(0);
    });
    
    // Check that priority texts exist (they appear multiple times)
    const priorities = ['חשוב', 'בינוני', 'נמוך'];
    priorities.forEach(text => {
      expect(screen.getAllByText(text).length).toBeGreaterThan(0);
    });
  });
});
