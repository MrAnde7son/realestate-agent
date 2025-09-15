import Link from "next/link"
import { cn } from "@/lib/utils"

export function Navbar() {
  return (
    <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <nav className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        <div className="flex items-center space-x-4">
          <Link href="/" className="flex items-center space-x-2">
            <span className="text-xl font-bold">🏠 Real Estate Pro</span>
          </Link>
        </div>

        <div className="flex items-center space-x-4">
          <Link
            href="/assets"
            className={cn(
              "text-sm font-medium transition-colors hover:text-primary",
              "text-muted-foreground"
            )}
          >
            נכסים
          </Link>
          <Link
            href="/alerts"
            className={cn(
              "text-sm font-medium transition-colors hover:text-primary",
              "text-muted-foreground"
            )}
          >
            התראות
          </Link>
          <Link
            href="/mortgage/analyze"
            className={cn(
              "text-sm font-medium transition-colors hover:text-primary",
              "text-muted-foreground"
            )}
          >
            משכנתא
          </Link>
          <Link
            href="/deal-expenses"
            className={cn(
              "text-sm font-medium transition-colors hover:text-primary",
              "text-muted-foreground"
            )}
          >
            מחשבון הוצאות
          </Link>
        </div>
      </nav>
    </div>
  )
}

