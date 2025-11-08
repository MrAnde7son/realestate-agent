import React, { type HTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const cardVariants = cva(
  'relative flex flex-col rounded-xl border text-card-foreground transition-shadow duration-200',
  {
    variants: {
      variant: {
        default: 'bg-card/95 border-border/60 shadow-sm backdrop-blur-sm',
        elevated: 'bg-card border-border/40 shadow-lg backdrop-blur-sm',
        outlined: 'bg-card/95 border-2 border-border shadow-none backdrop-blur-sm',
      },
      interactive: {
        flat: '',
        interactive:
          'hover:border-border/80 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background',
      },
    },
    defaultVariants: {
      variant: 'default',
      interactive: 'flat',
    },
  }
)

type CardVariant = NonNullable<VariantProps<typeof cardVariants>['variant']>

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant
  /**
   * Adds interactive hover and focus styles for clickable cards.
   */
  interactive?: boolean
}

export function Card({
  variant = 'default',
  interactive = false,
  className,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        cardVariants({ variant, interactive: interactive ? 'interactive' : 'flat' }),
        className,
      )}
      {...props}
    />
  )
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('flex flex-col space-y-1.5 p-6', className)}
      {...props}
    />
  )
}

export function CardBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('p-6 pt-0', className)} {...props} />
}

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('p-6 pt-0', className)} {...props} />
}

export const CardTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => {
    return (
      <h3
        ref={ref}
        className={cn('text-2xl font-semibold leading-none tracking-tight text-end', className)}
        {...props}
      />
    )
  }
)
CardTitle.displayName = 'CardTitle'

export function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn('text-sm text-muted-foreground text-end', className)}
      {...props}
    />
  )
}

export function CardFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('flex items-center p-6 pt-0', className)}
      {...props}
    />
  )
}

export { cardVariants }
export default Card
