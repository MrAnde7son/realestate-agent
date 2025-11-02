import { render, screen } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

import { Button, buttonVariants } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { TableHead } from '@/components/ui/table';

describe('shared UI accessibility affordances', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

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

  it('warns when icon buttons render without an accessible name', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    render(
      <Button size='icon'>
        <svg aria-hidden='true' />
      </Button>
    );

    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('accessible name')
    );
  });

  it('accepts visually hidden text as an accessible name for icon buttons', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    render(
      <Button size='icon'>
        <span className='sr-only'>Toggle menu</span>
      </Button>
    );

    expect(warnSpy).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Toggle menu' })).toBeInTheDocument();
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
