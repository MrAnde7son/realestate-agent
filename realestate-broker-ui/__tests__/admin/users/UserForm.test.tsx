import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UserForm } from '../../../app/admin/users/UserForm';
import { vi } from 'vitest';

// Mock the form components
vi.mock('react-hook-form', () => ({
  useForm: () => ({
    control: {},
    handleSubmit: (fn: any) => fn,
    formState: { errors: {} },
  }),
}));

vi.mock('@hookform/resolvers/zod', () => ({
  zodResolver: () => ({}),
}));

// Mock the UI components
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, ...props }: any) => (
    <button onClick={onClick} {...props}>
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/input', () => ({
  Input: (props: any) => <input {...props} />,
}));

vi.mock('@/components/ui/label', () => ({
  Label: ({ children, ...props }: any) => <label {...props}>{children}</label>,
}));

vi.mock('@/components/ui/checkbox', () => ({
  Checkbox: ({ checked, onCheckedChange, ...props }: any) => (
    <input
      type="checkbox"
      checked={checked}
      onChange={(e) => onCheckedChange(e.target.checked)}
      {...props}
    />
  ),
}));

vi.mock('@/components/ui/select', () => ({
  Select: ({ children, onValueChange, defaultValue }: any) => (
    <select onChange={(e) => onValueChange(e.target.value)} defaultValue={defaultValue}>
      {children}
    </select>
  ),
  SelectContent: ({ children }: any) => <div role="listbox">{children}</div>,
  SelectItem: ({ children, value }: any) => <option value={value}>{children}</option>,
  SelectTrigger: ({ children }: any) => <button type="button" role="combobox">{children}</button>,
  SelectValue: ({ placeholder }: any) => <span>{placeholder}</span>,
}));

vi.mock('@/components/ui/form', () => ({
  Form: ({ children }: any) => <form>{children}</form>,
  FormControl: ({ children }: any) => <div>{children}</div>,
  FormField: ({ render }: any) => render({ field: { value: '', onChange: vi.fn() } }),
  FormItem: ({ children }: any) => <div>{children}</div>,
  FormLabel: ({ children }: any) => <label>{children}</label>,
  FormMessage: () => <div />,
}));

describe('UserForm', () => {
  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders create user form correctly', () => {
    render(
      <UserForm
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('פרטי משתמש')).toBeInTheDocument();
    expect(screen.getByText('סטטוס משתמש')).toBeInTheDocument();
    expect(screen.getByText('סיסמה')).toBeInTheDocument();
    expect(screen.getByText('הגדרות')).toBeInTheDocument();
    expect(screen.getByText('התראות')).toBeInTheDocument();
  });

  it('renders edit user form correctly', () => {
    const user = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      phone: '050-1234567',
      company: 'Test Company',
      role: 'broker',
      is_active: true,
      is_verified: false,
      is_demo: false,
      is_staff: false,
      language: 'he',
      timezone: 'Asia/Jerusalem',
      currency: 'ils',
      date_format: 'dd/mm/yyyy',
      notify_email: true,
      notify_whatsapp: false,
      notify_urgent: true,
      notification_time: '09:00',
    };

    render(
      <UserForm
        user={user}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('פרטי משתמש')).toBeInTheDocument();
  });

  it('calls onSubmit when form is submitted', async () => {
    render(
      <UserForm
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    // Fill in required fields
    const usernameInput = screen.getByLabelText('שם משתמש *');
    const emailInput = screen.getByLabelText('אימייל *');
    const passwordInput = screen.getByLabelText('סיסמה *');
    const confirmPasswordInput = screen.getByLabelText('אישור סיסמה *');

    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });

    const submitButton = screen.getByText('צור משתמש');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled();
    });
  });

  it('calls onCancel when cancel button is clicked', () => {
    render(
      <UserForm
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    const cancelButton = screen.getByText('ביטול');
    fireEvent.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('shows correct button text for edit mode', () => {
    const user = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      phone: '050-1234567',
      company: 'Test Company',
      role: 'broker',
      is_active: true,
      is_verified: false,
      is_demo: false,
      is_staff: false,
      language: 'he',
      timezone: 'Asia/Jerusalem',
      currency: 'ils',
      date_format: 'dd/mm/yyyy',
      notify_email: true,
      notify_whatsapp: false,
      notify_urgent: true,
      notification_time: '09:00',
    };

    render(
      <UserForm
        user={user}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('עדכן משתמש')).toBeInTheDocument();
  });
});
