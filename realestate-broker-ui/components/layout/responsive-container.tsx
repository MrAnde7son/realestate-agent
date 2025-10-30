import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cn } from "@/lib/utils"

interface ResponsiveContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  asChild?: boolean
  /**
   * When true the container keeps horizontal padding but stretches to the edge of the viewport.
   * Useful for sections that need to bleed into the full width while preserving responsive spacing
   * within nested elements.
   */
  bleed?: boolean
}

/**
 * ResponsiveContainer centralises layout spacing rules so that application pages share a
 * consistent maximum width and horizontal rhythm on both desktop and mobile displays.
 */
export function ResponsiveContainer({
  asChild,
  bleed = false,
  className,
  children,
  ...props
}: ResponsiveContainerProps) {
  const Comp = asChild ? Slot : "div"
  return (
    <Comp
      className={cn(
        "w-full",
        bleed ? "px-0" : "mx-auto max-w-7xl px-4 sm:px-6 lg:px-8",
        className
      )}
      {...props}
    >
      {children}
    </Comp>
  )
}

export default ResponsiveContainer
