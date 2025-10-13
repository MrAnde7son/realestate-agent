import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import CrmUnifiedPage from '@/app/crm/page';
import { CrmApi } from '@/lib/api/crm';

const mockReplace = vi.fn();
let mockSearchParams = new URLSearchParams();
const trackEventMock = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: mockReplace }),
  useSearchParams: () => mockSearchParams,
}));

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

vi.mock('@/components/crm/LeadsList', () => ({
  __esModule: true,
  default: ({ onConvertedToClient }: { onConvertedToClient?: (id: number) => void }) => (
    <div data-testid="leads-list">
      <button onClick={() => onConvertedToClient?.(123)}>convert</button>
    </div>
  ),
}));

vi.mock('@/components/crm/ContactsList', () => ({
  __esModule: true,
  default: () => <div data-testid="contacts-list" />,
}));

vi.mock('@/lib/api/crm', () => ({
  CrmApi: {
    getContacts: vi.fn(),
    getLeads: vi.fn(),
  },
}));

describe('CrmUnifiedPage', () => {
  beforeEach(() => {
    mockReplace.mockReset();
    trackEventMock.mockReset();
    mockSearchParams = new URLSearchParams();
    vi.mocked(CrmApi.getContacts).mockResolvedValue([]);
    vi.mocked(CrmApi.getLeads).mockResolvedValue([]);
  });

  it('renders clients tab by default and tracks CRM open', async () => {
    render(<CrmUnifiedPage />);

    await waitFor(() => {
      expect(CrmApi.getContacts).toHaveBeenCalled();
      expect(CrmApi.getLeads).toHaveBeenCalled();
    });

    expect(screen.getByTestId('contacts-list')).toBeInTheDocument();
    expect(trackEventMock).toHaveBeenCalledWith({
      event: 'crm_opened',
      meta: { tab: 'clients' },
    });
  });

  it('shows leads tab when tab query is leads', async () => {
    mockSearchParams = new URLSearchParams('tab=leads');
    render(<CrmUnifiedPage />);

    await waitFor(() => {
      expect(CrmApi.getContacts).toHaveBeenCalled();
      expect(CrmApi.getLeads).toHaveBeenCalled();
    });

    expect(screen.getByTestId('leads-list')).toBeInTheDocument();
  });

  it('updates the URL and analytics when switching tabs', async () => {
    render(<CrmUnifiedPage />);

    await waitFor(() => {
      expect(CrmApi.getContacts).toHaveBeenCalled();
      expect(CrmApi.getLeads).toHaveBeenCalled();
    }, { timeout: 5000 });

    // Wait for the component to finish loading
    await waitFor(() => {
      expect(screen.getByTestId('contacts-list')).toBeInTheDocument();
    }, { timeout: 5000 });

    trackEventMock.mockClear();
    const leadsTabButton = screen.getByRole('tab', { name: 'לידים' });

    fireEvent.mouseDown(leadsTabButton);

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/crm?tab=leads');
    });

    expect(trackEventMock).toHaveBeenCalledWith({
      event: 'crm_tab_changed',
      meta: { tab: 'leads' },
    });
  });

  it('tracks analytics when KPI card is clicked', async () => {
    render(<CrmUnifiedPage />);

    await waitFor(() => {
      expect(CrmApi.getContacts).toHaveBeenCalled();
      expect(CrmApi.getLeads).toHaveBeenCalled();
    }, { timeout: 5000 });

    // Wait for the component to finish loading
    await waitFor(() => {
      expect(screen.getByTestId('contacts-list')).toBeInTheDocument();
    }, { timeout: 5000 });

    trackEventMock.mockClear();
    const leadsCardHeading = screen.getByRole('heading', { name: 'לידים' });
    fireEvent.click(leadsCardHeading);

    expect(trackEventMock).toHaveBeenCalledWith({
      event: 'crm_card_clicked',
      meta: { target: 'leads' },
    });
    expect(trackEventMock).toHaveBeenCalledWith({
      event: 'crm_tab_changed',
      meta: { tab: 'leads' },
    });
  });

  it('navigates to clients when lead is converted', async () => {
    mockSearchParams = new URLSearchParams('tab=leads');
    render(<CrmUnifiedPage />);

    await waitFor(() => {
      expect(CrmApi.getContacts).toHaveBeenCalled();
      expect(CrmApi.getLeads).toHaveBeenCalled();
    });

    trackEventMock.mockClear();
    const convertButton = screen.getByText('convert');
    fireEvent.click(convertButton);

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/crm?tab=clients');
    });

    expect(trackEventMock).toHaveBeenCalledWith({
      event: 'crm_tab_changed',
      meta: { tab: 'clients' },
    });
  });
});
