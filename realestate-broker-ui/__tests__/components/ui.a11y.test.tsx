import { render, screen } from '@testing-library/react';

import { Button, buttonVariants } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { TableHead } from '@/components/ui/table';

describe('shared UI accessibility affordances', () => {
  it('keeps explicit focus-ring utilities on buttons', () => {
    const classes = buttonVariants();

    expect(classes).toContain('focus-visible:ring-2');
    expect(classes).toContain('focus-visible:ring-ring');
    expect(classes).toContain('focus-visible:ring-offset-2');
    expect(classes).toContain('focus-visible:ring-offset-background');
  });

  it('exposes accessible name support for icon buttons', () => {
    render(
      <Button size='icon' aria-label='Open menu'>
        <span aria-hidden='true'>+</span>
      </Button>
    );

    expect(screen.getByRole('button', { name: 'Open menu' })).toBeInTheDocument();
  });

  it('applies focus ring offset tokens to inputs', () => {
    const { container } = render(<Input aria-label='Search' />);

    expect(container.querySelector('input')).toHaveClass(
      'focus-visible:ring-offset-background'
    );
  });

  it('defaults table headers to column scope', () => {
    render(
      <table>
        <thead>
          <tr>
            <TableHead>Label</TableHead>
          </tr>
        </thead>
      </table>
    );

    expect(screen.getByText('Label').closest('th')).toHaveAttribute('scope', 'col');
  });
});
