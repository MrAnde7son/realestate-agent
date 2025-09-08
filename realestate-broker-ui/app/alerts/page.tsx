'use client'
import React, { useState, useEffect } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Bell, CheckCircle, Clock, TrendingDown, Home, FileText, Hammer, RefreshCw } from 'lucide-react'
import type { Alert } from '@/lib/data'

const getAlertIcon = (type: Alert['type']) => {
  switch (type) {
    case 'price_drop':
      return <TrendingDown className="h-5 w-5 text-red-500" />
    case 'new_asset':
      return <Home className="h-5 w-5 text-blue-500" />
    case 'market_change':
      return <Bell className="h-5 w-5 text-orange-500" />
    case 'document_update':
      return <FileText className="h-5 w-5 text-purple-500" />
    case 'permit_status':
      return <Hammer className="h-5 w-5 text-green-500" />
    default:
      return <Bell className="h-5 w-5 text-gray-500" />
  }
}

const getPriorityColor = (priority: Alert['priority']) => {
  switch (priority) {
    case 'high':
      return 'error'
    case 'medium':
      return 'warning'
    case 'low':
      return 'neutral'
    default:
      return 'neutral'
  }
}

const getPriorityText = (priority: Alert['priority']) => {
  switch (priority) {
    case 'high':
      return 'חשוב'
    case 'medium':
      return 'בינוני'
    case 'low':
      return 'נמוך'
    default:
      return 'רגיל'
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
  
  if (diffInHours < 1) return 'לפני פחות משעה'
  if (diffInHours < 24) return `לפני ${diffInHours} שעות`
  if (diffInHours < 48) return 'אתמול'
  return date.toLocaleDateString('he-IL')
}

export default function AlertsPage() {
  const [alertsData, setAlertsData] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedPriorities, setSelectedPriorities] = useState<Alert['priority'][]>([])
  const [selectedTypes, setSelectedTypes] = useState<Alert['type'][]>([])

  // Fetch alerts from API
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/alerts')
        if (response.ok) {
          const data = await response.json()
          setAlertsData(data.alerts || data || [])
        } else {
          setError('שגיאה בטעינת ההתראות')
        }
      } catch (err) {
        console.error('Error fetching alerts:', err)
        setError('שגיאה בטעינת ההתראות')
      } finally {
        setLoading(false)
      }
    }

    fetchAlerts()
  }, [])

  const togglePriority = (priority: Alert['priority']) => {
    setSelectedPriorities(prev =>
      prev.includes(priority) ? prev.filter(p => p !== priority) : [...prev, priority]
    )
  }

  const toggleType = (type: Alert['type']) => {
    setSelectedTypes(prev =>
      prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
    )
  }

  const markAsRead = async (alertId: number) => {
    try {
      const response = await fetch('/api/alerts', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alertId, isRead: true })
      })
      
      if (response.ok) {
        // Update local state
        setAlertsData(prev =>
          prev.map(alert =>
            alert.id === alertId ? { ...alert, isRead: true } : alert
          )
        )
        
        // Refresh data from server to ensure consistency
        const refreshResponse = await fetch('/api/alerts')
        if (refreshResponse.ok) {
          const data = await refreshResponse.json()
          setAlertsData(data.alerts || data || [])
        }
      }
    } catch (err) {
      console.error('Error marking alert as read:', err)
    }
  }

  const markAllAsRead = async () => {
    try {
      const response = await fetch('/api/alerts', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ markAllAsRead: true })
      })
      
      if (response.ok) {
        // Update local state
        setAlertsData(prev =>
          prev.map(alert => ({ ...alert, isRead: true }))
        )
        
        // Refresh data from server to ensure consistency
        const refreshResponse = await fetch('/api/alerts')
        if (refreshResponse.ok) {
          const data = await refreshResponse.json()
          setAlertsData(data.alerts || data || [])
        }
      }
    } catch (err) {
      console.error('Error marking all alerts as read:', err)
    }
  }

  const filteredAlerts = alertsData.filter(alert => {
    const priorityMatch =
      selectedPriorities.length === 0 || selectedPriorities.includes(alert.priority)
    const typeMatch = selectedTypes.length === 0 || selectedTypes.includes(alert.type)
    return priorityMatch && typeMatch
  })

  const unreadCount = filteredAlerts.filter(alert => !alert.isRead).length

  if (loading) {
    return (
      <DashboardLayout>
        <DashboardShell>
          <DashboardHeader 
            heading="התראות" 
            text="טוען התראות..."
          />
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <Card key={i}>
                <CardContent className="p-6">
                  <div className="space-y-3">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                    <Skeleton className="h-3 w-1/4" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </DashboardShell>
      </DashboardLayout>
    )
  }

  if (error) {
    return (
      <DashboardLayout>
        <DashboardShell>
          <DashboardHeader 
            heading="התראות" 
            text="שגיאה בטעינת ההתראות"
          />
          <Card>
            <CardContent className="p-6 text-center">
              <div className="space-y-4">
                <div className="w-16 h-16 rounded-full bg-error/10 flex items-center justify-center mx-auto">
                  <Bell className="h-8 w-8 text-error" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-foreground">שגיאה בטעינת ההתראות</h3>
                  <p className="text-muted-foreground">{error}</p>
                </div>
                <Button onClick={() => window.location.reload()} variant="outline">
                  <RefreshCw className="h-4 w-4 ms-2" />
                  נסה שוב
                </Button>
              </div>
            </CardContent>
          </Card>
        </DashboardShell>
      </DashboardLayout>
    )
  }
  
  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader 
          heading="התראות" 
          text="קבל עדכונים על שינויים בנכסים ובשוק הנדל״ן"
        >
          {unreadCount > 0 && (
            <Button onClick={markAllAsRead} variant="outline" className="w-full sm:w-auto">
              <CheckCircle className="h-4 w-4 ms-2" />
              סמן הכל כנקרא ({unreadCount})
            </Button>
          )}
        </DashboardHeader>

        {/* Main Content Grid */}
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
          {/* Alerts List - Takes 2 columns on large screens, full width on mobile */}
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <span>התראות אחרונות</span>
                  {unreadCount > 0 && (
                    <Badge variant="accent" className="w-fit">{unreadCount} לא נקראו</Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {filteredAlerts.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 space-y-4">
                    <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
                      <Bell className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <div className="text-center">
                      <h3 className="text-lg font-semibold text-foreground">אין התראות</h3>
                      <p className="text-muted-foreground">
                        {selectedPriorities.length > 0 || selectedTypes.length > 0
                          ? 'לא נמצאו התראות לפי הסינון שנבחר'
                          : 'אין התראות זמינות כרגע'}
                      </p>
                      {(selectedPriorities.length > 0 || selectedTypes.length > 0) && (
                        <Button 
                          variant="outline" 
                          className="mt-4"
                          onClick={() => {
                            setSelectedPriorities([])
                            setSelectedTypes([])
                          }}
                        >
                          נקה סינון
                        </Button>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {filteredAlerts.map((alert) => (
                      <div 
                        key={alert.id} 
                        className={`flex flex-col sm:flex-row sm:items-start gap-4 p-4 border rounded-lg transition-colors ${
                          alert.isRead ? 'bg-muted/50' : 'bg-card hover:bg-muted/50'
                        }`}
                      >
                        <div className="flex-shrink-0 flex justify-center sm:justify-start">
                          {getAlertIcon(alert.type)}
                        </div>
                        
                        <div className="flex-1 min-w-0 space-y-3">
                          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                            <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                              <h3 className={`font-medium text-sm sm:text-base ${!alert.isRead ? 'text-primary' : 'text-muted-foreground'}`}>
                                {alert.title}
                              </h3>
                              <div className="flex items-center gap-2">
                                <Badge variant={getPriorityColor(alert.priority)} className="text-xs">
                                  {getPriorityText(alert.priority)}
                                </Badge>
                                {!alert.isRead && (
                                  <div className="w-2 h-2 bg-blue-500 rounded-full" />
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              <span>{formatDate(alert.createdAt)}</span>
                            </div>
                          </div>
                          
                          <p className="text-sm text-muted-foreground">{alert.message}</p>
                          
                          {alert.assetAddress && (
                            <p className="text-xs text-muted-foreground">
                              📍 {alert.assetAddress}
                            </p>
                          )}
                          
                          <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
                            {alert.actionUrl && (
                              <Button size="sm" variant="outline" asChild className="w-full sm:w-auto">
                                <a href={alert.actionUrl}>צפה בנכס</a>
                              </Button>
                            )}
                            {!alert.isRead && (
                              <Button 
                                size="sm" 
                                variant="ghost"
                                onClick={() => markAsRead(alert.id)}
                                className="w-full sm:w-auto"
                              >
                                סמן כנקרא
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Takes 1 column on large screens, full width on mobile */}
          <div className="space-y-4">
            {/* Quick Stats Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">סטטיסטיקות מהירות</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">סה״כ התראות</span>
                  <span className="font-semibold">{filteredAlerts.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">לא נקראו</span>
                  <span className="font-semibold text-blue-600">{unreadCount}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">היום</span>
                  <span className="font-semibold">
                    {filteredAlerts.filter(alert => {
                      const alertDate = new Date(alert.createdAt)
                      const today = new Date()
                      return alertDate.toDateString() === today.toDateString()
                    }).length}
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Filter Options Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">סינון התראות</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">עדיפות</label>
                  <div className="flex flex-wrap gap-2">
                    {['high', 'medium', 'low'].map((priority) => (
                      <Badge
                        key={priority}
                        variant={
                          selectedPriorities.includes(priority as Alert['priority'])
                            ? 'default'
                            : 'neutral'
                        }
                        className="cursor-pointer"
                        onClick={() => togglePriority(priority as Alert['priority'])}
                      >
                        {getPriorityText(priority as Alert['priority'])}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">סוג התראה</label>
                  <div className="flex flex-wrap gap-2">
                    {['price_drop', 'new_asset', 'market_change', 'document_update', 'permit_status'].map((type) => (
                      <Badge
                        key={type}
                        variant={
                          selectedTypes.includes(type as Alert['type'])
                            ? 'default'
                            : 'neutral'
                        }
                        className="cursor-pointer"
                        onClick={() => toggleType(type as Alert['type'])}
                      >
                        {type === 'price_drop' && 'ירידת מחיר'}
                        {type === 'new_asset' && 'נכס חדש'}
                        {type === 'market_change' && 'שינוי בשוק'}
                        {type === 'document_update' && 'עדכון מסמכים'}
                        {type === 'permit_status' && 'סטטוס היתרים'}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Alert Types Info - Full width, responsive grid */}
        <Card>
          <CardHeader>
            <CardTitle>סוגי התראות</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 md:grid-cols-5">
              <div className="flex flex-col items-center gap-2 text-center p-3 rounded-lg hover:bg-muted/50 transition-colors">
                <TrendingDown className="h-6 w-6 text-red-500" />
                <span className="text-sm">ירידת מחיר</span>
              </div>
              <div className="flex flex-col items-center gap-2 text-center p-3 rounded-lg hover:bg-muted/50 transition-colors">
                <Home className="h-6 w-6 text-blue-500" />
                <span className="text-sm">נכס חדש</span>
              </div>
              <div className="flex flex-col items-center gap-2 text-center p-3 rounded-lg hover:bg-muted/50 transition-colors">
                <Bell className="h-6 w-6 text-orange-500" />
                <span className="text-sm">שינוי בשוק</span>
              </div>
              <div className="flex flex-col items-center gap-2 text-center p-3 rounded-lg hover:bg-muted/50 transition-colors">
                <FileText className="h-6 w-6 text-purple-500" />
                <span className="text-sm">עדכון מסמכים</span>
              </div>
              <div className="flex flex-col items-center gap-2 text-center p-3 rounded-lg hover:bg-muted/50 transition-colors">
                <Hammer className="h-6 w-6 text-green-500" />
                <span className="text-sm">סטטוס היתרים</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </DashboardShell>
    </DashboardLayout>
  )
}