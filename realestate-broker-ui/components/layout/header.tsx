'use client'

import * as React from "react"
import { Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { ThemeToggle } from "@/components/ui/theme-toggle"
import Logo from "@/components/Logo"
import AppSidebar from "./app-sidebar"

interface HeaderProps {
  onToggleSidebar?: () => void
}

export default function Header({ onToggleSidebar }: HeaderProps) {
  return (
    <header className="flex h-16 items-center justify-between border-b bg-background px-6">
      <div className="flex items-center space-x-4">
        {/* Mobile menu trigger */}
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="md:hidden">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="p-0 w-64">
            <AppSidebar />
          </SheetContent>
        </Sheet>

        {/* Desktop sidebar toggle */}
        <Button 
          variant="ghost" 
          size="icon" 
          className="hidden md:flex"
          onClick={onToggleSidebar}
        >
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle sidebar</span>
        </Button>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <Logo variant="horizontal" size={32} color="var(--brand-teal)" />
          <div className="hidden md:block text-sm text-muted-foreground">
            נדל״ן חכם לשמאים, מתווכים ומשקיעים
          </div>
        </div>
        <ThemeToggle />
      </div>
    </header>
  )
}
