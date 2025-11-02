"use client"

import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from "@/components/ui/toast"
import { AlertCircle, CheckCircle2, Info, TriangleAlert } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

export function Toaster() {
  const { toasts } = useToast()

  const iconMap = {
    default: Info,
    info: Info,
    success: CheckCircle2,
    warning: TriangleAlert,
    destructive: AlertCircle,
  }

  return (
    <ToastProvider>
      {toasts.map(function ({ id, title, description, action, ...props }) {
        const variant = (props.variant ?? "default") as keyof typeof iconMap
        const Icon = iconMap[variant] ?? iconMap.default
        return (
          <Toast key={id} {...props}>
            <div className="flex w-full items-start gap-3">
              <Icon aria-hidden="true" className="mt-0.5 h-4 w-4 flex-shrink-0" />
              <div className="grid gap-1 flex-1">
                {title && <ToastTitle>{title}</ToastTitle>}
                {description && (
                  <ToastDescription>{description}</ToastDescription>
                )}
                {action && <div className="pt-2">{action}</div>}
              </div>
              <ToastClose />
            </div>
          </Toast>
        )
      })}
      <ToastViewport />
    </ToastProvider>
  )
}
