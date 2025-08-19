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
    href: "/listings",
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

  const runCommand = React.useCallback((command: () => unknown) => {
    setOpen(false)
    command()
  }, [])

  return (
    <>
      <Button
        variant="outline"
        className="relative h-9 w-9 p-0 xl:h-10 xl:w-60 xl:justify-start xl:px-3 xl:py-2"
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
        <CommandInput placeholder="חפש בכל האתר..." />
        <CommandList>
          <CommandEmpty>לא נמצאו תוצאות.</CommandEmpty>
          <CommandGroup heading="ניווט מהיר">
            {searchItems.map((item) => (
              <CommandItem
                key={item.href}
                onSelect={() => runCommand(() => router.push(item.href))}
              >
                <span className="mr-2 text-lg">{item.icon}</span>
                <div>
                  <div className="font-medium">{item.title}</div>
                  <div className="text-sm text-muted-foreground">
                    {item.description}
                  </div>
                </div>
              </CommandItem>
            ))}
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  )
}
