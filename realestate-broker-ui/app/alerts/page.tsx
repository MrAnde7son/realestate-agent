'use client'
import React, { useState, useEffect } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Bell, CheckCircle, Clock, TrendingDown, Home, FileText, Hammer, RefreshCw } from 'lucide-react'
import { ALERT_TYPE_LABELS } from '@/lib/alert-constants'

interface AlertEvent {
  id: number
  alert_rule: {
    id: number
    trigger_type: string
    trigger_type_display: string
  }
  asset_address?: string
  occurred_at: string
  payload: any
  delivered_at?: string
}

const getAlertIcon = (triggerType: string) => {
  switch (triggerType) {
    case 'PRICE_DROP':
      return <TrendingDown className="h-5 w-5 text-red-500" />
    case 'NEW_LISTING':
      return <Home className="h-5 w-5 text-blue-500" />
    case 'MARKET_TREND':
      return <Bell className="h-5 w-5 text-orange-500" />
    case 'DOCS_UPDATE':
      return <FileText className="h-5 w-5 text-purple-500" />
    case 'PERMIT_STATUS':
      return <Hammer className="h-5 w-5 text-green-500" />
    case 'NEW_GOV_TX':
      return <FileText className="h-5 w-5 text-green-500" />
    case 'LISTING_REMOVED':
      return <TrendingDown className="h-5 w-5 text-gray-500" />
    default:
      return <Bell className="h-5 w-5 text-gray-500" />
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
  const [alertsData, setAlertsData] = useState<AlertEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTypes, setSelectedTypes] = useState<string[]>([])

  // Fetch alerts from API
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/alerts?since=2024-01-01')
        if (response.ok) {
          const data = await response.json()
          setAlertsData(data.events || data || [])
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

  const toggleType = (type: string) => {
    setSelectedTypes(prev =>
      prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
    )
  }

  const markAsRead = async (alertId: number) => {
    try {
      // For now, just update local state since we don't have a backend endpoint for this yet
      setAlertsData(prev =>
        prev.map(alert =>
          alert.id === alertId ? { ...alert, delivered_at: new Date().toISOString() } : alert
        )
      )
    } catch (err) {
      console.error('Error marking alert as read:', err)
    }
  }

  const markAllAsRead = async () => {
    try {
      // For now, just update local state since we don't have a backend endpoint for this yet
      setAlertsData(prev =>
        prev.map(alert => ({ ...alert, delivered_at: new Date().toISOString() }))
      )
    } catch (err) {
      console.error('Error marking all alerts as read:', err)
    }
  }

  const filteredAlerts = alertsData.filter(alert => {
    const typeMatch = selectedTypes.length === 0 || selectedTypes.includes(alert.alert_rule.trigger_type)
    return typeMatch
  })

  const unreadCount = filteredAlerts.filter(alert => !alert.delivered_at).length

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
                        {selectedTypes.length > 0
                          ? 'לא נמצאו התראות לפי הסינון שנבחר'
                          : 'אין התראות זמינות כרגע'}
                      </p>
                      {selectedTypes.length > 0 && (
                        <Button 
                          variant="outline" 
                          className="mt-4"
                          onClick={() => {
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
                          alert.delivered_at ? 'bg-muted/50' : 'bg-card hover:bg-muted/50'
                        }`}
                      >
                        <div className="flex-shrink-0 flex justify-center sm:justify-start">
                          {getAlertIcon(alert.alert_rule.trigger_type)}
                        </div>
                        
                        <div className="flex-1 min-w-0 space-y-3">
                          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                            <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                              <h3 className={`font-medium text-sm sm:text-base ${!alert.delivered_at ? 'text-primary' : 'text-muted-foreground'}`}>
                                {ALERT_TYPE_LABELS[alert.alert_rule.trigger_type as keyof typeof ALERT_TYPE_LABELS] || alert.alert_rule.trigger_type_display}
                              </h3>
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="text-xs">
                                  {alert.alert_rule.trigger_type_display}
                                </Badge>
                                {!alert.delivered_at && (
                                  <div className="w-2 h-2 bg-blue-500 rounded-full" />
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              <span>{formatDate(alert.occurred_at)}</span>
                            </div>
                          </div>
                          
                          <p className="text-sm text-muted-foreground">
                            {alert.payload?.message || 'התראה חדשה'}
                          </p>
                          
                          {alert.asset_address && (
                            <p className="text-xs text-muted-foreground">
                              📍 {alert.asset_address}
                            </p>
                          )}
                          
                          <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
                            {alert.payload?.asset_url && (
                              <Button size="sm" variant="outline" asChild className="w-full sm:w-auto">
                                <a href={alert.payload.asset_url}>צפה בנכס</a>
                              </Button>
                            )}
                            {!alert.delivered_at && (
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
                      const alertDate = new Date(alert.occurred_at)
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
                  <label className="text-sm font-medium">סוג התראה</label>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(ALERT_TYPE_LABELS).map(([key, label]) => (
                      <Badge
                        key={key}
                        variant={
                          selectedTypes.includes(key)
                            ? 'default'
                            : 'neutral'
                        }
                        className="cursor-pointer"
                        onClick={() => toggleType(key)}
                      >
                        {label}
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
              {Object.entries(ALERT_TYPE_LABELS).map(([key, label]) => (
                <div key={key} className="flex flex-col items-center gap-2 text-center p-3 rounded-lg hover:bg-muted/50 transition-colors">
                  {getAlertIcon(key)}
                  <span className="text-sm">{label}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </DashboardShell>
    </DashboardLayout>
  )
}