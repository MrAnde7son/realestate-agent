import React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

const typographyVariants = cva('', {
  variants: {
    variant: {
      h1: 'scroll-m-20 text-3xl font-bold tracking-tight text-foreground sm:text-4xl',
      h2: 'scroll-m-20 text-2xl font-semibold tracking-tight text-foreground sm:text-3xl',
      h3: 'scroll-m-20 text-xl font-semibold tracking-tight text-foreground sm:text-2xl',
      h4: 'scroll-m-20 text-lg font-semibold tracking-tight text-foreground',
      body: 'text-base leading-7 text-foreground',
      muted: 'text-sm leading-6 text-muted-foreground'
    }
  },
  defaultVariants: {
    variant: 'body'
  }
})

const defaultElementByVariant = {
  h1: 'h1',
  h2: 'h2',
  h3: 'h3',
  h4: 'h4',
  body: 'p',
  muted: 'p'
} as const satisfies Record<
  NonNullable<VariantProps<typeof typographyVariants>['variant']>,
  keyof JSX.IntrinsicElements
>

type TypographyVariant = VariantProps<typeof typographyVariants>['variant']

export type TypographyProps = React.HTMLAttributes<HTMLElement> & {
  as?: keyof JSX.IntrinsicElements
  variant?: TypographyVariant
}

export const Typography = React.forwardRef<HTMLElement, TypographyProps>(
  ({ as, variant = 'body', className, ...props }, ref) => {
    const resolvedVariant = (variant ?? 'body') as NonNullable<TypographyVariant>

    const Component = (as ?? defaultElementByVariant[resolvedVariant]) as keyof JSX.IntrinsicElements

    return (
      <Component
        ref={ref as React.Ref<HTMLElement>}
        className={cn(typographyVariants({ variant: resolvedVariant }), className)}
        {...props}
      />
    )
  }
)

Typography.displayName = 'Typography'

export { typographyVariants }
