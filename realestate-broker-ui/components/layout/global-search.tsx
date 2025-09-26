'use client'

import * as React from "react"
import { useRouter } from "next/navigation"
import { Command as CommandPrimitive } from "cmdk"
import { Search, Users, UserCheck, Building, Phone, Mail, Tag } from "lucide-react"
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
import { useAnalytics } from "@/hooks/useAnalytics"
import { CrmApi, Contact, Lead } from "@/lib/api/crm"
import { useAuth } from "@/lib/auth-context"

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
    title: "לקוחות",
    href: "/crm",
    icon: "👥",
    description: "ניהול לקוחות ולידים"
  },
  {
    title: "התראות",
    href: "/alerts",
    icon: "🔔",
    description: "התראות ועדכונים"
  },
  {
    title: "דוחות",
    href: "/reports",
    icon: "📊",
    description: "דוחות שוק וניתוחים"
  },
  {
    title: "מחשבון הוצאות",
    href: "/deal-expenses",
    icon: "🧾",
    description: "חישוב הוצאות עסקה"
  },
  {
    title: "מחשבון משכנתא",
    href: "/mortgage/analyze",
    icon: "💰",
    description: "חישוב משכנתא וניתוח"
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
  const [searchQuery, setSearchQuery] = React.useState("")
  const [crmContacts, setCrmContacts] = React.useState<Contact[]>([])
  const [crmLeads, setCrmLeads] = React.useState<Lead[]>([])
  const [isSearchingCrm, setIsSearchingCrm] = React.useState(false)
  const { trackSearch, trackFeatureUsage } = useAnalytics()
  const { user } = useAuth()
  const canAccessCrm = ['broker', 'appraiser', 'admin'].includes(user?.role || '')

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

  // Reset search when dialog closes
  React.useEffect(() => {
    if (!open) {
      setSearchQuery("")
      setCrmContacts([])
      setCrmLeads([])
      setIsSearchingCrm(false)
    }
  }, [open])

  // CRM search functionality
  const searchCrm = React.useCallback(async (query: string) => {
    if (!canAccessCrm || !query.trim()) {
      setCrmContacts([])
      setCrmLeads([])
      return
    }

    setIsSearchingCrm(true)
    try {
      const [contacts, leads] = await Promise.all([
        CrmApi.searchContacts(query),
        CrmApi.getLeads()
      ])
      
      // Filter leads by search query
      const filteredLeads = leads.filter(lead => 
        lead.contact.name.toLowerCase().includes(query.toLowerCase()) ||
        lead.contact.email.toLowerCase().includes(query.toLowerCase()) ||
        lead.asset_address.toLowerCase().includes(query.toLowerCase())
      )
      
      setCrmContacts(contacts.slice(0, 5)) // Limit to 5 contacts
      setCrmLeads(filteredLeads.slice(0, 5)) // Limit to 5 leads
    } catch (error) {
      console.error('CRM search error:', error)
      setCrmContacts([])
      setCrmLeads([])
    } finally {
      setIsSearchingCrm(false)
    }
  }, [canAccessCrm])

  // Debounced CRM search
  React.useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchQuery.trim()) {
        searchCrm(searchQuery)
      } else {
        setCrmContacts([])
        setCrmLeads([])
      }
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [searchQuery, searchCrm])

  const runCommand = React.useCallback((command: () => unknown, searchQuery?: string) => {
    setOpen(false)
    
    // Track search usage
    if (searchQuery) {
      trackSearch(searchQuery, {}, 1)
    }
    
    // Track feature usage
    trackFeatureUsage('global_search')
    
    command()
  }, [trackSearch, trackFeatureUsage])

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
          value={searchQuery}
          onValueChange={(value) => {
            setSearchQuery(value)
            if (value.trim()) {
              trackSearch(value.trim(), {}, 0)
            }
          }}
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
          
          {/* CRM Search Results */}
          {canAccessCrm && searchQuery.trim() && (
            <>
              {/* Contacts Results */}
              {crmContacts.length > 0 && (
                <CommandGroup heading="לקוחות" className="text-right">
                  {crmContacts.map((contact) => (
                    <CommandItem
                      key={`contact-${contact.id}`}
                      onSelect={() => runCommand(() => router.push('/crm/contacts'), searchQuery)}
                      className="group"
                    >
                      <Users className="ml-3 h-4 w-4 text-blue-500" />
                      <div className="flex-1 text-right">
                        <div className="font-semibold group-hover:text-[var(--brand-teal)] transition-colors duration-200">
                          {contact.name}
                        </div>
                        <div className="text-sm text-muted-foreground group-hover:text-foreground transition-colors duration-200">
                          {contact.email && (
                            <div className="flex items-center gap-1">
                              <Mail className="h-3 w-3" />
                              {contact.email}
                            </div>
                          )}
                          {contact.phone && (
                            <div className="flex items-center gap-1">
                              <Phone className="h-3 w-3" />
                              {contact.phone}
                            </div>
                          )}
                          {contact.tags.length > 0 && (
                            <div className="flex items-center gap-1 mt-1">
                              <Tag className="h-3 w-3" />
                              {contact.tags.join(', ')}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground group-hover:text-foreground transition-colors duration-200 opacity-60 group-hover:opacity-100">
                        לקוח
                      </div>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}

              {/* Leads Results */}
              {crmLeads.length > 0 && (
                <CommandGroup heading="לידים" className="text-right">
                  {crmLeads.map((lead) => (
                    <CommandItem
                      key={`lead-${lead.id}`}
                      onSelect={() => runCommand(() => router.push('/crm/leads'), searchQuery)}
                      className="group"
                    >
                      <UserCheck className="ml-3 h-4 w-4 text-green-500" />
                      <div className="flex-1 text-right">
                        <div className="font-semibold group-hover:text-[var(--brand-teal)] transition-colors duration-200">
                          {lead.contact.name} - {lead.asset_address}
                        </div>
                        <div className="text-sm text-muted-foreground group-hover:text-foreground transition-colors duration-200">
                          <div className="flex items-center gap-1">
                            <Building className="h-3 w-3" />
                            {lead.asset_price ? new Intl.NumberFormat('he-IL').format(lead.asset_price) + ' ₪' : 'מחיר לא זמין'}
                          </div>
                          <div className="text-xs mt-1">
                            סטטוס: {lead.status === 'new' ? 'חדש' : 
                                   lead.status === 'contacted' ? 'הותחל קשר' :
                                   lead.status === 'interested' ? 'מעוניין' :
                                   lead.status === 'negotiating' ? 'במשא ומתן' :
                                   lead.status === 'closed-won' ? 'נסגר בהצלחה' :
                                   lead.status === 'closed-lost' ? 'נסגר ללא הצלחה' : lead.status}
                          </div>
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground group-hover:text-foreground transition-colors duration-200 opacity-60 group-hover:opacity-100">
                        ליד
                      </div>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}

              {/* Loading State */}
              {isSearchingCrm && (
                <CommandGroup heading="חיפוש CRM" className="text-right">
                  <CommandItem disabled>
                    <div className="flex-1 text-right">
                      <div className="text-sm text-muted-foreground">מחפש ב-CRM...</div>
                    </div>
                  </CommandItem>
                </CommandGroup>
              )}
            </>
          )}
        </CommandList>
      </CommandDialog>
    </>
  )
}
