'use client'

import * as React from "react"
import AppSidebar from "./app-sidebar"
import Header from "./header"
import { cn } from "@/lib/utils"

interface DashboardLayoutProps {
  children: React.ReactNode
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = React.useState(true)
  const [mounted, setMounted] = React.useState(false)

  // Initialize sidebar state from localStorage
  React.useEffect(() => {
    const savedSidebarState = localStorage.getItem('sidebar-open')
    if (savedSidebarState !== null) {
      setSidebarOpen(JSON.parse(savedSidebarState))
    }
    setMounted(true)
  }, [])

  // Save sidebar state to localStorage when it changes
  const handleToggleSidebar = () => {
    const newState = !sidebarOpen
    setSidebarOpen(newState)
    localStorage.setItem('sidebar-open', JSON.stringify(newState))
  }

  return (
    <div className="flex min-h-[100dvh] supports-[height:100dvh]:min-h-[100dvh] bg-background overflow-hidden">
      {/* Sidebar - hidden on mobile, visible on medium screens and larger */}
      <div className="hidden md:flex-shrink-0 md:block">
        <AppSidebar isCollapsed={!sidebarOpen} />
      </div>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header onToggleSidebar={handleToggleSidebar} />

        <main className="flex-1 pt-16">
          <div className="min-h-[calc(100dvh-4rem)] supports-[height:100dvh]:min-h-[calc(100dvh-4rem)]">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
