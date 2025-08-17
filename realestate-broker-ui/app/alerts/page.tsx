'use client'
import React, { useState } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Bell, CheckCircle, Clock, TrendingDown, Home, FileText, Hammer } from 'lucide-react'
import { alerts, type Alert } from '@/lib/data'

const getAlertIcon = (type: Alert['type']) => {
  switch (type) {
    case 'price_drop':
      return <TrendingDown className="h-5 w-5 text-red-500" />
    case 'new_listing':
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
      return 'destructive'
    case 'medium':
      return 'default'
    case 'low':
      return 'secondary'
    default:
      return 'outline'
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
  const [email, setEmail] = useState('user@example.com')
  const [phone, setPhone] = useState('+972-50-123-4567')
  const [priceThreshold, setPriceThreshold] = useState(50000)
  const [alertsData, setAlertsData] = useState(alerts)
  
  const markAsRead = (alertId: string) => {
    setAlertsData(prev => 
      prev.map(alert => 
        alert.id === alertId ? { ...alert, isRead: true } : alert
      )
    )
  }

  const markAllAsRead = () => {
    setAlertsData(prev => 
      prev.map(alert => ({ ...alert, isRead: true }))
    )
  }

  const unreadCount = alertsData.filter(alert => !alert.isRead).length
  
  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader 
          heading="התראות" 
          text="קבל עדכונים על שינויים בנכסים ובשוק הנדל״ן"
        >
          {unreadCount > 0 && (
            <Button onClick={markAllAsRead} variant="outline">
              <CheckCircle className="h-4 w-4 mr-2" />
              סמן הכל כנקרא ({unreadCount})
            </Button>
          )}
        </DashboardHeader>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Alert Settings */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>הגדרות התראות</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">כתובת אימייל</label>
                <Input 
                  type="email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="user@example.com"
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">מספר טלפון</label>
                <Input 
                  type="tel" 
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+972-50-123-4567"
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">סף התרעה לירידת מחיר (₪)</label>
                <Input 
                  type="number" 
                  value={priceThreshold}
                  onChange={(e) => setPriceThreshold(Number(e.target.value))}
                  placeholder="50,000"
                />
              </div>
              
              <Button className="w-full">שמור הגדרות</Button>
            </CardContent>
          </Card>

          {/* Alerts List */}
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>התראות אחרונות</span>
                  <Badge variant="outline">{unreadCount} לא נקראו</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {alertsData.map((alert) => (
                    <div 
                      key={alert.id} 
                      className={`flex items-start space-x-4 p-4 border rounded-lg transition-colors ${
                        alert.isRead ? 'bg-muted/50' : 'bg-card hover:bg-muted/50'
                      }`}
                    >
                      <div className="flex-shrink-0 mt-1">
                        {getAlertIcon(alert.type)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <h3 className={`font-medium ${!alert.isRead ? 'text-primary' : 'text-muted-foreground'}`}>
                              {alert.title}
                            </h3>
                            <Badge variant={getPriorityColor(alert.priority)} className="text-xs">
                              {getPriorityText(alert.priority)}
                            </Badge>
                            {!alert.isRead && (
                              <div className="w-2 h-2 bg-blue-500 rounded-full" />
                            )}
                          </div>
                          <div className="flex items-center space-x-2">
                            <Clock className="h-3 w-3 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">
                              {formatDate(alert.createdAt)}
                            </span>
                          </div>
                        </div>
                        
                        <p className="text-sm text-muted-foreground mt-1">{alert.message}</p>
                        
                        {alert.listingAddress && (
                          <p className="text-xs text-muted-foreground mt-1">
                            📍 {alert.listingAddress}
                          </p>
                        )}
                        
                        <div className="flex items-center space-x-2 mt-3">
                          {alert.actionUrl && (
                            <Button size="sm" variant="outline" asChild>
                              <a href={alert.actionUrl}>צפה בנכס</a>
                            </Button>
                          )}
                          {!alert.isRead && (
                            <Button 
                              size="sm" 
                              variant="ghost"
                              onClick={() => markAsRead(alert.id)}
                            >
                              סמן כנקרא
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Alert Types Info */}
        <Card>
          <CardHeader>
            <CardTitle>סוגי התראות</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
              <div className="flex items-center space-x-2">
                <TrendingDown className="h-4 w-4 text-red-500" />
                <span className="text-sm">ירידת מחיר</span>
              </div>
              <div className="flex items-center space-x-2">
                <Home className="h-4 w-4 text-blue-500" />
                <span className="text-sm">נכס חדש</span>
              </div>
              <div className="flex items-center space-x-2">
                <Bell className="h-4 w-4 text-orange-500" />
                <span className="text-sm">שינוי בשוק</span>
              </div>
              <div className="flex items-center space-x-2">
                <FileText className="h-4 w-4 text-purple-500" />
                <span className="text-sm">עדכון מסמכים</span>
              </div>
              <div className="flex items-center space-x-2">
                <Hammer className="h-4 w-4 text-green-500" />
                <span className="text-sm">סטטוס היתרים</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </DashboardShell>
    </DashboardLayout>
  )
}