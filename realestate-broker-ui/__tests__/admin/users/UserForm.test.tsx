import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UserForm } from '../app/admin/users/UserForm';

// Mock the form components
jest.mock('react-hook-form', () => ({
  useForm: () => ({
    control: {},
    handleSubmit: (fn: any) => fn,
    formState: { errors: {} },
  }),
}));

jest.mock('@hookform/resolvers/zod', () => ({
  zodResolver: () => ({}),
}));

// Mock the UI components
jest.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, ...props }: any) => (
    <button onClick={onClick} {...props}>
      {children}
    </button>
  ),
}));

jest.mock('@/components/ui/input', () => ({
  Input: (props: any) => <input {...props} />,
}));

jest.mock('@/components/ui/label', () => ({
  Label: ({ children, ...props }: any) => <label {...props}>{children}</label>,
}));

jest.mock('@/components/ui/checkbox', () => ({
  Checkbox: ({ checked, onCheckedChange, ...props }: any) => (
    <input
      type="checkbox"
      checked={checked}
      onChange={(e) => onCheckedChange(e.target.checked)}
      {...props}
    />
  ),
}));

jest.mock('@/components/ui/select', () => ({
  Select: ({ children, onValueChange, defaultValue }: any) => (
    <select onChange={(e) => onValueChange(e.target.value)} defaultValue={defaultValue}>
      {children}
    </select>
  ),
  SelectContent: ({ children }: any) => <div>{children}</div>,
  SelectItem: ({ children, value }: any) => <option value={value}>{children}</option>,
  SelectTrigger: ({ children }: any) => <div>{children}</div>,
  SelectValue: ({ placeholder }: any) => <span>{placeholder}</span>,
}));

jest.mock('@/components/ui/form', () => ({
  Form: ({ children }: any) => <form>{children}</form>,
  FormControl: ({ children }: any) => <div>{children}</div>,
  FormField: ({ render }: any) => render({ field: { value: '', onChange: jest.fn() } }),
  FormItem: ({ children }: any) => <div>{children}</div>,
  FormLabel: ({ children }: any) => <label>{children}</label>,
  FormMessage: () => <div />,
}));

describe('UserForm', () => {
  const mockOnSubmit = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders create user form correctly', () => {
    render(
      <UserForm
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('מידע בסיסי')).toBeInTheDocument();
    expect(screen.getByText('תפקיד והרשאות')).toBeInTheDocument();
    expect(screen.getByText('סיסמה')).toBeInTheDocument();
    expect(screen.getByText('העדפות')).toBeInTheDocument();
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

    expect(screen.getByText('ערוך משתמש')).toBeInTheDocument();
  });

  it('calls onSubmit when form is submitted', async () => {
    render(
      <UserForm
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    const submitButton = screen.getByText('צור');
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

    expect(screen.getByText('עדכן')).toBeInTheDocument();
  });
});
