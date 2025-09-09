'use client'

import * as React from "react"
import { useRouter } from "next/navigation"
import { Command as CommandPrimitive } from "cmdk"
import { Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  DialogTitle,
} from "@/components/ui/dialog"

const searchItems = [
  {
    title: "בית",
    href: "/",
    icon: "🏠",
    description: "דף הבית והסקירה הכללית"
  },
  {
    title: "נכסים",
    href: "/assets",
    icon: "🏢",
    description: "ניהול נכסים ועסקאות"
  },
  {
    title: "התראות",
    href: "/alerts",
    icon: "🔔",
    description: "התראות ועדכונים"
  },
  {
    title: "מחשבון משכנתא",
    href: "/mortgage/analyze",
    icon: "🧮",
    description: "חישוב משכנתא וניתוח"
  },
  {
    title: "דוחות",
    href: "/reports",
    icon: "📊",
    description: "דוחות שוק וניתוחים"
  },
  {
    title: "פרופיל",
    href: "/profile",
    icon: "👤",
    description: "הגדרות פרופיל אישי"
  },
  {
    title: "חבילות ותשלומים",
    href: "/billing",
    icon: "💳",
    description: "ניהול חבילות ותשלומים"
  },
  {
    title: "הגדרות",
    href: "/settings",
    icon: "⚙️",
    description: "הגדרות מערכת"
  }
]

export function GlobalSearch() {
  const router = useRouter()
  const [open, setOpen] = React.useState(false)

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }

    document.addEventListener("keydown", down)
    return () => document.removeEventListener("keydown", down)
  }, [])

  // Close dialog on escape
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false)
      }
    }

    if (open) {
      document.addEventListener("keydown", handleEscape)
      return () => document.removeEventListener("keydown", handleEscape)
    }
  }, [open])

  const runCommand = React.useCallback((command: () => unknown) => {
    setOpen(false)
    command()
  }, [])

  return (
    <>
      <Button
        variant="outline"
        className="relative h-9 w-9 p-0 xl:h-10 xl:w-60 xl:justify-start xl:px-3 xl:py-2 hover:bg-accent hover:text-accent-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        onClick={() => setOpen(true)}
      >
        <Search className="h-4 w-4 xl:ml-2" />
        <span className="hidden xl:inline-flex">חפש בכל האתר...</span>
        <kbd className="pointer-events-none absolute right-1.5 top-2 hidden h-6 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 xl:flex">
          <span className="text-xs">⌘</span>K
        </kbd>
      </Button>
      <CommandDialog open={open} onOpenChange={setOpen}>
        <DialogTitle className="sr-only">חיפוש גלובלי</DialogTitle>
        <CommandInput 
          placeholder="חפש בכל האתר..." 
          className="text-right border-0 focus:ring-0"
          dir="rtl"
        />
        <CommandList className="max-h-[400px] overflow-y-auto">
          <CommandEmpty className="py-6 text-center text-sm text-muted-foreground">לא נמצאו תוצאות.</CommandEmpty>
          <CommandGroup heading="ניווט מהיר" className="text-right">
            {searchItems.map((item) => (
              <CommandItem
                key={item.href}
                onSelect={() => runCommand(() => router.push(item.href))}
                className="group"
              >
                <span className="ml-3 text-xl group-hover:scale-110 transition-transform duration-200">{item.icon}</span>
                <div className="flex-1 text-right">
                  <div className="font-semibold group-hover:text-[var(--brand-teal)] transition-colors duration-200">{item.title}</div>
                  <div className="text-sm text-muted-foreground group-hover:text-foreground transition-colors duration-200">
                    {item.description}
                  </div>
                </div>
                <div className="text-xs text-muted-foreground group-hover:text-foreground transition-colors duration-200 opacity-60 group-hover:opacity-100">
                  Enter
                </div>
              </CommandItem>
            ))}
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  )
}
