import React, {
  createContext,
  useContext,
  type HTMLAttributes,
  forwardRef,
} from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const cardVariants = cva(
  'relative flex flex-col rounded-[var(--radius-2)] bg-card/95 text-card-foreground shadow-[var(--shadow-2)] backdrop-blur-sm transition-shadow duration-200',
  {
    variants: {
      variant: {
        elevated: 'border border-border/60 shadow-[var(--shadow-2)] bg-card/95',
        outline: 'border border-border/70 bg-background/95 shadow-none',
        ghost: 'border border-transparent bg-transparent shadow-none backdrop-blur-none',
      },
      size: {
        sm: '',
        md: '',
        lg: '',
      },
    },
    defaultVariants: {
      variant: 'elevated',
      size: 'md',
    },
  }
)

type CardVariantProps = VariantProps<typeof cardVariants>
type CardSize = Exclude<CardVariantProps['size'], null | undefined>
type CardVariant = Exclude<CardVariantProps['variant'], null | undefined>

const CardContext = createContext<{ size: CardSize }>({ size: 'md' })

function useCardContext() {
  return useContext(CardContext)
}

const headerPadding: Record<CardSize, string> = {
  sm: 'px-4 py-3',
  md: 'px-6 py-4',
  lg: 'px-8 py-6',
}

const headerGap: Record<CardSize, string> = {
  sm: 'gap-2',
  md: 'gap-3',
  lg: 'gap-4',
}

const sectionPadding: Record<CardSize, string> = {
  sm: 'px-4 pb-4 pt-0',
  md: 'px-6 pb-6 pt-0',
  lg: 'px-8 pb-8 pt-0',
}

const footerPadding: Record<CardSize, string> = {
  sm: 'px-4 pb-4 pt-0',
  md: 'px-6 pb-6 pt-0',
  lg: 'px-8 pb-8 pt-0',
}

export interface CardProps extends Omit<HTMLAttributes<HTMLDivElement>, 'size'> {
  /**
   * Visual density applied to the card and automatically propagated to its sections.
   */
  size?: CardSize
  /**
   * Surface treatment for the card shell.
   */
  variant?: CardVariant
}

export const Card = forwardRef<HTMLDivElement, CardProps>(function Card(
  { size = 'md', className, variant, ...props },
  ref
) {
  const resolvedSize: CardSize = size ?? 'md'
  return (
    <CardContext.Provider value={{ size: resolvedSize }}>
      <div
        ref={ref}
        className={cn(cardVariants({ size: resolvedSize, variant }), className)}
        {...props}
      />
    </CardContext.Provider>
  )
})

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(function CardHeader(
  { className, ...props },
  ref
) {
  const { size } = useCardContext()
  return (
    <div
      ref={ref}
      className={cn('flex flex-col', headerGap[size], headerPadding[size], className)}
      {...props}
    />
  )
})

export const CardBody = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(function CardBody(
  { className, ...props },
  ref
) {
  const { size } = useCardContext()
  return (
    <div
      ref={ref}
      className={cn(sectionPadding[size], className)}
      {...props}
    />
  )
})

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(function CardContent(
  { className, ...props },
  ref
) {
  const { size } = useCardContext()
  return (
    <div
      ref={ref}
      className={cn(sectionPadding[size], className)}
      {...props}
    />
  )
})

export const CardTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => {
    return (
      <h3
        ref={ref}
        className={cn('text-2xl font-semibold leading-none tracking-tight', className)}
        {...props}
      />
    )
  }
)
CardTitle.displayName = 'CardTitle'

export function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn('text-sm text-muted-foreground', className)}
      {...props}
    />
  )
}

export const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(function CardFooter(
  { className, ...props },
  ref
) {
  const { size } = useCardContext()
  return (
    <div
      ref={ref}
      className={cn('flex items-center', footerPadding[size], className)}
      {...props}
    />
  )
})

export { cardVariants }
export default Card
