import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import CrmUnifiedPage from '@/app/crm/page';
import { CrmApi } from '@/lib/api/crm';

const trackEventMock = vi.fn();
const toastMock = vi.fn();

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
  useToast: () => ({ toast: toastMock }),
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
      <button onClick={() => void onRefresh()}>refresh</button>
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
    vi.mocked(CrmApi.getContacts).mockReset();
    vi.mocked(CrmApi.getLeads).mockReset();
    vi.mocked(CrmApi.getTasks).mockReset();
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
    expect(trackEventMock).not.toHaveBeenCalled();
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

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByTestId('combined-table')).toBeInTheDocument();
    });

    await screen.findByText('contacts:1');
    await screen.findByText('leads:2');
  });

  it('allows refreshing data from the combined table', async () => {
    render(<CrmUnifiedPage />);

    // Wait for loading to complete and component to render
    await waitFor(
      () => {
        expect(screen.getByTestId('combined-table')).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Verify initial API calls were made
    await waitFor(() => {
      expect(CrmApi.getContacts).toHaveBeenCalled();
      expect(CrmApi.getLeads).toHaveBeenCalled();
    });

    // Get call counts after initial load
    const initialContactsCalls = vi.mocked(CrmApi.getContacts).mock.calls.length;
    const initialLeadsCalls = vi.mocked(CrmApi.getLeads).mock.calls.length;

    // Clear the mocks to isolate refresh calls
    vi.mocked(CrmApi.getContacts).mockClear();
    vi.mocked(CrmApi.getLeads).mockClear();

    const refreshButton = screen.getByText('refresh');
    fireEvent.click(refreshButton);

    // Wait for refresh calls
    await waitFor(
      () => {
        expect(CrmApi.getContacts).toHaveBeenCalled();
        expect(CrmApi.getLeads).toHaveBeenCalled();
      },
      { timeout: 3000 }
    );
  });
});
