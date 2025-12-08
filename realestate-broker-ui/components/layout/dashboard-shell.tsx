import { cn } from "@/lib/utils"
import React from "react"

interface DashboardShellProps extends React.HTMLAttributes<HTMLDivElement> {
  scrollable?: boolean
}

export function DashboardShell({
  children,
  className,
  scrollable = false,
  ...props
}: DashboardShellProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-4 py-6 pb-20 md:py-8 md:pb-8 min-h-full w-full px-4 sm:px-6 lg:px-8",
        scrollable && "overflow-y-auto max-h-[calc(100dvh-4rem)] h-[calc(100dvh-4rem)]",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

interface DashboardHeaderProps {
  heading: string | React.ReactNode
  text?: string
  children?: React.ReactNode
}

export function DashboardHeader({
  heading,
  text,
  children,
}: DashboardHeaderProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between px-2">
      <div className="grid gap-1">
        <h1 className="font-bold text-2xl md:text-3xl lg:text-4xl text-end">{heading}</h1>
        {text && <p className="text-base md:text-lg text-muted-foreground text-end">{text}</p>}
      </div>
      {children && <div className="w-full sm:w-auto">{children}</div>}
    </div>
  )
}
