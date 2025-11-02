import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '@/lib/utils';

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
  {
    variants: {
      variant: {
        default:
          'bg-primary text-primary-foreground shadow-xs hover:bg-primary/90',
        destructive:
          'bg-destructive text-white shadow-xs hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60',
        outline:
          'border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground dark:bg-input/30 dark:border-input dark:hover:bg-input/50',
        secondary:
          'bg-secondary text-secondary-foreground shadow-xs hover:bg-secondary/80',
        ghost:
          'hover:bg-accent hover:text-accent-foreground dark:hover:bg-accent/50',
        link: 'text-primary underline-offset-4 hover:underline',
        // Keep compatibility with your existing 'primary' variant
        primary: 'bg-primary text-primary-foreground shadow-xs hover:bg-primary/90'
      },
      size: {
        default: 'h-9 px-4 py-2 has-[>svg]:px-3',
        sm: 'h-8 rounded-md gap-1.5 px-3 has-[>svg]:px-2.5',
        lg: 'h-10 rounded-md px-6 has-[>svg]:px-4',
        icon: 'size-9'
      }
    },
    defaultVariants: {
      variant: 'default',
      size: 'default'
    }
  }
);

type ButtonVariantProps = VariantProps<typeof buttonVariants>;

type ButtonProps = Omit<React.ComponentPropsWithoutRef<'button'>, 'size'> &
  Omit<ButtonVariantProps, 'size'> & {
    size?: ButtonVariantProps['size'];
    asChild?: boolean;
  };

const Button = React.forwardRef<React.ElementRef<'button'>, ButtonProps>(
  ({ className, variant, size, asChild = false, children, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    const resolvedSize = size ?? 'default';

    if (process.env.NODE_ENV !== 'production' && resolvedSize === 'icon') {
      const ariaLabel = props['aria-label'];
      const ariaLabelledby = props['aria-labelledby'];
      const title = props.title;
      const hasExplicitAccessibleName =
        typeof ariaLabel === 'string' ||
        typeof ariaLabelledby === 'string' ||
        typeof title === 'string';
      const hasTextualChildren = React.Children.toArray(children).some(
        childHasAccessibleText
      );

      if (!hasExplicitAccessibleName && !hasTextualChildren) {
        console.warn(
          'Button with size="icon" should include an accessible name via aria-label, aria-labelledby, title, or textual children.'
        );
      }
    }

    return (
      <Comp
        ref={ref}
        data-slot='button'
        className={cn(
          buttonVariants({ variant, size: resolvedSize }),
          className
        )}
        {...props}
      >
        {children}
      </Comp>
    );
  }
);

Button.displayName = 'Button';

function childHasAccessibleText(node: React.ReactNode): boolean {
  if (node == null || typeof node === 'boolean') {
    return false;
  }

  if (typeof node === 'string') {
    return node.trim().length > 0;
  }

  if (typeof node === 'number') {
    return true;
  }

  if (Array.isArray(node)) {
    return node.some(childHasAccessibleText);
  }

  if (React.isValidElement(node)) {
    const ariaHidden = node.props['aria-hidden'];

    if (ariaHidden === true || ariaHidden === 'true') {
      return false;
    }

    return React.Children.toArray(node.props.children).some(
      childHasAccessibleText
    );
  }

  return false;
}

export { Button, buttonVariants };
