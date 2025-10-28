import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import CrmUnifiedPage from '@/app/crm/page';
import { CrmApi } from '@/lib/api/crm';

const trackEventMock = vi.fn();

vi.mock('@/hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackEvent: trackEventMock,
    trackPageView: vi.fn(),
    trackSearch: vi.fn(),
    trackFeatureUsage: vi.fn(),
    trackPerformance: vi.fn(),
    trackCalculatorUsage: vi.fn(),
    trackCalculatorCalculation: vi.fn(),
    trackCalculatorExport: vi.fn(),
  }),
}));

vi.mock('@/lib/auth-context', () => ({
  useAuth: () => ({ user: { role: 'broker' }, isLoading: false }),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

vi.mock('@/components/layout/dashboard-layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dashboard-layout">{children}</div>
  ),
}));

vi.mock('@/components/crm/combined-crm-table', () => ({
  CombinedCrmTable: ({ contacts, leads, onRefresh }: any) => (
    <div data-testid="combined-table">
      <div>contacts:{contacts.length}</div>
      <div>leads:{leads.length}</div>
      <button onClick={() => onRefresh()}>refresh</button>
    </div>
  ),
}));

vi.mock('@/lib/api/crm', () => ({
  CrmApi: {
    getContacts: vi.fn(),
    getLeads: vi.fn(),
    getTasks: vi.fn(),
  },
}));

describe('CrmUnifiedPage', () => {
  beforeEach(() => {
    trackEventMock.mockReset();
    vi.mocked(CrmApi.getContacts).mockResolvedValue([]);
    vi.mocked(CrmApi.getLeads).mockResolvedValue([]);
    vi.mocked(CrmApi.getTasks).mockResolvedValue([]);
  });

  it('renders combined CRM table and tracks open event', async () => {
    render(<CrmUnifiedPage />);

    await waitFor(() => {
      expect(CrmApi.getContacts).toHaveBeenCalled();
      expect(CrmApi.getLeads).toHaveBeenCalled();
    });

    expect(screen.getByTestId('combined-table')).toBeInTheDocument();
    expect(trackEventMock).toHaveBeenCalledWith({
      event: 'crm_opened',
      meta: { view: 'combined' },
    });
  });

  it('shows KPI cards with correct values', async () => {
    vi.mocked(CrmApi.getContacts).mockResolvedValue([
      { id: 1, name: 'Contact A' },
    ] as any);
    vi.mocked(CrmApi.getLeads).mockResolvedValue([
      { id: 1, status: 'new', contact: { name: 'Contact A' }, last_activity_at: new Date().toISOString() },
      { id: 2, status: 'closed-won', contact: { name: 'Contact B' }, last_activity_at: new Date().toISOString() },
    ] as any);

    render(<CrmUnifiedPage />);

    await screen.findByText('contacts:1');
    await screen.findByText('leads:2');
  });

  it('allows refreshing data from the combined table', async () => {
    render(<CrmUnifiedPage />);

    await screen.findByTestId('combined-table');

    expect(CrmApi.getContacts).toHaveBeenCalled();
    expect(CrmApi.getLeads).toHaveBeenCalled();

    const initialContactsCalls = vi.mocked(CrmApi.getContacts).mock.calls.length;
    const initialLeadsCalls = vi.mocked(CrmApi.getLeads).mock.calls.length;

    const refreshButton = await screen.findByText('refresh');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(vi.mocked(CrmApi.getContacts).mock.calls.length).toBeGreaterThan(initialContactsCalls);
      expect(vi.mocked(CrmApi.getLeads).mock.calls.length).toBeGreaterThan(initialLeadsCalls);
    });
  });
});
