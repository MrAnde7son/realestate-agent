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

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <div className={cn(
        "hidden md:flex transition-all duration-300 ease-in-out",
        sidebarOpen ? "w-64" : "w-0"
      )}>
        <AppSidebar />
      </div>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
        
        <main className="flex-1 overflow-y-auto bg-background">
          {children}
        </main>
      </div>
    </div>
  )
}
