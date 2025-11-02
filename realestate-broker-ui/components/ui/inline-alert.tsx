"use client"

import type * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { AlertCircle, CheckCircle2, Info, TriangleAlert } from "lucide-react"

import { cn } from "@/lib/utils"

const inlineAlertVariants = cva(
  "flex gap-3 items-start rounded-lg border px-4 py-3 text-sm shadow-xs",
  {
    variants: {
      variant: {
        info: "border-info/50 bg-info/10 text-info-foreground",
        success: "border-success/50 bg-success/10 text-success-foreground",
        warning: "border-warning/50 bg-warning/10 text-warning-foreground",
        destructive:
          "border-destructive/50 bg-destructive/10 text-destructive-foreground",
      },
    },
    defaultVariants: {
      variant: "info",
    },
  }
)

const ICONS = {
  info: Info,
  success: CheckCircle2,
  warning: TriangleAlert,
  destructive: AlertCircle,
}

export interface InlineAlertProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof inlineAlertVariants> {
  title?: React.ReactNode
  description?: React.ReactNode
}

export function InlineAlert({
  title,
  description,
  children,
  variant,
  className,
  role,
  ...props
}: InlineAlertProps) {
  const Icon = ICONS[variant ?? "info"] ?? ICONS.info
  const body = description ?? children
  const computedRole = role ?? (variant === "destructive" ? "alert" : "status")

  return (
    <div
      role={computedRole}
      className={cn(inlineAlertVariants({ variant }), className)}
      {...props}
    >
      <Icon aria-hidden="true" className="mt-0.5 h-4 w-4 flex-shrink-0" />
      <div className="space-y-1 text-sm">
        {title && <p className="font-medium">{title}</p>}
        {body && <div className="text-[0.9rem] leading-relaxed">{body}</div>}
      </div>
    </div>
  )
}
