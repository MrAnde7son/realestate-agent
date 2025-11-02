import React, { type HTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const cardVariants = cva(
  'rounded-lg bg-card/95 backdrop-blur-sm text-card-foreground shadow-md',
  {
    variants: {
      variant: {
        default: 'bg-card/95 backdrop-blur-sm shadow-md',
        elevated: 'bg-card backdrop-blur-md shadow-lg',
        outlined: 'bg-card/95 backdrop-blur-sm border-2 border-border shadow-md',
        ghost: 'bg-transparent backdrop-blur-none shadow-none',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface CardProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

export function Card({ variant = 'default', className, ...props }: CardProps) {
  return (
    <div
      className={cn(cardVariants({ variant }), className)}
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
