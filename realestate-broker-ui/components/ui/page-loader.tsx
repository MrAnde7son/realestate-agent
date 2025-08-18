import * as React from "react"
import { Loader2 } from "lucide-react"
import Logo from "@/components/Logo"
import { cn } from "@/lib/utils"

interface PageLoaderProps {
  message?: string
  showLogo?: boolean
  className?: string
}

export function PageLoader({ message = "טוען...", showLogo = true, className }: PageLoaderProps) {
  return (
    <div className={cn("flex h-[50vh] w-full flex-col items-center justify-center space-y-4", className)}>
      {showLogo && (
        <Logo variant="symbol" size={48} color="var(--brand-teal)" />
      )}
      <div className="flex items-center space-x-2 space-x-reverse">
        <Loader2 className="h-6 w-6 animate-spin text-brand-teal" />
        <span className="text-muted-foreground">{message}</span>
      </div>
    </div>
  )
}

export function FullPageLoader({ message = "טוען...", showLogo = true }: PageLoaderProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="flex flex-col items-center justify-center space-y-4 rounded-lg bg-card p-8 shadow-lg">
        {showLogo && (
          <Logo variant="symbol" size={48} color="var(--brand-teal)" />
        )}
        <div className="flex items-center space-x-2 space-x-reverse">
          <Loader2 className="h-8 w-8 animate-spin text-brand-teal" />
          <span className="text-lg text-muted-foreground">{message}</span>
        </div>
      </div>
    </div>
  )
}

// For button loading states
export function ButtonLoader({ size = "sm" }: { size?: "sm" | "md" | "lg" }) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-5 w-5", 
    lg: "h-6 w-6"
  }
  
  return (
    <Loader2 className={cn("animate-spin", sizeClasses[size])} />
  )
}
