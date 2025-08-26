import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface PageLoaderProps {
  message?: string
  showLogo?: boolean
}

export function PageLoader({ message = "טוען...", showLogo = false }: PageLoaderProps) {
  return (
    <div className="flex min-h-[100dvh] items-center justify-center">
      <div className="flex flex-col items-center space-y-4">
        {showLogo && (
          <div className="w-12 h-12 bg-brand-teal rounded-full flex items-center justify-center mb-4">
            <span className="text-white font-bold text-lg">נ</span>
          </div>
        )}
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">{message}</p>
      </div>
    </div>
  )
}

export function FullPageLoader({ message = "טוען...", showLogo = true }: PageLoaderProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="flex flex-col items-center justify-center space-y-4 rounded-lg bg-card p-8 shadow-lg">
        {showLogo && (
          <div className="w-12 h-12 bg-brand-teal rounded-full flex items-center justify-center">
            <span className="text-white font-bold text-lg">נ</span>
          </div>
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
