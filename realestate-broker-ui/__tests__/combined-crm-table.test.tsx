import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CombinedCrmTable } from '@/components/crm/combined-crm-table';
import { CrmApi } from '@/lib/api/crm';

const toastMock = vi.fn();

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: toastMock }),
}));

vi.mock('@/components/crm/contact-form', () => ({
  ContactForm: ({ onSubmit }: any) => (
    <div data-testid="contact-form">
      <button onClick={() => onSubmit({ name: 'New Contact' })}>submit-contact</button>
    </div>
  ),
}));

vi.mock('@/components/crm/lead-status-badge', () => ({
  LeadStatusBadge: ({ status }: { status: string }) => (
    <span data-testid="status-badge">{status}</span>
  ),
}));

vi.mock('@/components/crm/lead-task-summary', () => ({
  LeadTaskSummary: () => <div data-testid="task-summary" />,
}));

vi.mock('@/components/crm/lead-row-actions', () => ({
  LeadRowActions: ({ lead, onUpdate, onDelete }: any) => (
    <div>
      <button onClick={() => onUpdate()}>update-lead</button>
      <button onClick={() => onDelete(lead.id)}>delete-lead</button>
    </div>
  ),
}));

vi.mock('@/components/crm/task-form', () => ({
  TaskForm: ({ onSubmit }: any) => (
    <div data-testid="task-form">
      <button onClick={() => onSubmit({ title: 'Task' })}>submit-task</button>
    </div>
  ),
}));

vi.mock('@/lib/api/crm', () => ({
  CrmApi: {
    getTasks: vi.fn(),
    createContact: vi.fn(),
    createLead: vi.fn(),
    updateContact: vi.fn(),
    deleteContact: vi.fn(),
    deleteLead: vi.fn(),
    createTask: vi.fn(),
    completeTask: vi.fn(),
    deleteTask: vi.fn(),
  },
}));

describe('CombinedCrmTable', () => {
  const mockRefresh = vi.fn();
  let confirmSpy: ReturnType<typeof vi.spyOn>;

  const contact = {
    id: 1,
    name: 'Alice',
    phone: '123',
    email: 'alice@example.com',
    equity: null,
    city: 'תל אביב',
    streets: '',
    asset_type: '',
    area_min: null,
    area_max: null,
    floor: '',
    notes: 'Important client',
    tags: ['VIP'],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  } as any;

  const lead = {
    id: 10,
    contact_id: 1,
    contact,
    asset_id: 99,
    asset_id_read: 99,
    asset_address: 'Example Street 5',
    asset_price: 1000000,
    asset_rooms: 4,
    asset_area: 120,
    status: 'new',
    notes: [],
    last_activity_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
  } as any;

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(CrmApi.getTasks).mockResolvedValue([]);
    vi.mocked(CrmApi.createContact).mockResolvedValue({ id: 2 });
    vi.mocked(CrmApi.createLead).mockResolvedValue({});
    vi.mocked(CrmApi.updateContact).mockResolvedValue({});
    vi.mocked(CrmApi.deleteContact).mockResolvedValue(undefined);
    vi.mocked(CrmApi.deleteLead).mockResolvedValue(undefined);
    vi.mocked(CrmApi.createTask).mockResolvedValue({});
    vi.mocked(CrmApi.completeTask).mockResolvedValue({});
    vi.mocked(CrmApi.deleteTask).mockResolvedValue(undefined);
    mockRefresh.mockReset();
    mockRefresh.mockResolvedValue(undefined);
    (window as any).open = vi.fn();
    confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  afterEach(() => {
    confirmSpy.mockRestore();
  });

  it('renders contacts and leads information', async () => {
    render(
      <CombinedCrmTable
        contacts={[contact]}
        leads={[lead]}
        onRefresh={mockRefresh}
      />
    );

    await waitFor(() => {
      expect(CrmApi.getTasks).toHaveBeenCalled();
    });

    expect(screen.getByText('Alice')).toBeInTheDocument();

    const toggleButton = screen.getByRole('button', { name: 'פתיחת פרטי לקוח' });
    fireEvent.click(toggleButton);

    expect(screen.getByText('נכסים משויכים')).toBeInTheDocument();
    expect(screen.getAllByText('Example Street 5').length).toBeGreaterThan(0);
  });

  it('creates a new contact through the dialog', async () => {
    render(
      <CombinedCrmTable
        contacts={[contact]}
        leads={[lead]}
        onRefresh={mockRefresh}
      />
    );

    fireEvent.click(screen.getByText('לקוח חדש'));

    const formButton = await screen.findByText('submit-contact');
    fireEvent.click(formButton);

    await waitFor(() => {
      expect(CrmApi.createContact).toHaveBeenCalled();
      expect(mockRefresh).toHaveBeenCalled();
    });
  });

  it('deletes a contact when confirmed', async () => {
    render(
      <CombinedCrmTable
        contacts={[contact]}
        leads={[lead]}
        onRefresh={mockRefresh}
      />
    );

    const deleteButton = screen.getByRole('button', { name: /מחק/ });
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(CrmApi.deleteContact).toHaveBeenCalledWith(1);
      expect(mockRefresh).toHaveBeenCalled();
    });
  });

  it('deletes a lead from the expanded view', async () => {
    render(
      <CombinedCrmTable
        contacts={[contact]}
        leads={[lead]}
        onRefresh={mockRefresh}
      />
    );

    const toggleButton = screen.getByRole('button', { name: 'פתיחת פרטי לקוח' });
    fireEvent.click(toggleButton);

    const deleteLeadButton = await screen.findByText('delete-lead');
    fireEvent.click(deleteLeadButton);

    await waitFor(() => {
      expect(CrmApi.deleteLead).toHaveBeenCalledWith(10);
      expect(mockRefresh).toHaveBeenCalled();
    });
  });
});
