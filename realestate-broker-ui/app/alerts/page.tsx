'use client'
import React, { useState, useEffect } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Bell, CheckCircle, Clock, TrendingDown, Home, FileText, Hammer, RefreshCw, Plus, Settings, Edit, Trash2 } from 'lucide-react'
import { ALERT_TYPE_LABELS } from '@/lib/alert-constants'
import AlertRulesManager from '@/components/alerts/alert-rules-manager'
import { api } from '@/lib/api-client'

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
      return <TrendingDown className="h-5 w-5 text-error" />
    case 'NEW_LISTING':
      return <Home className="h-5 w-5 text-brand-blue" />
    case 'MARKET_TREND':
      return <Bell className="h-5 w-5 text-warning" />
    case 'DOCS_UPDATE':
      return <FileText className="h-5 w-5 text-info" />
    case 'PERMIT_STATUS':
      return <Hammer className="h-5 w-5 text-success" />
    case 'NEW_GOV_TX':
      return <FileText className="h-5 w-5 text-success" />
    case 'LISTING_REMOVED':
      return <TrendingDown className="h-5 w-5 text-muted-foreground" />
    default:
      return <Bell className="h-5 w-5 text-muted-foreground" />
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

interface AlertRule {
  id: number
  trigger_type: string
  trigger_type_display: string
  scope: string
  scope_display: string
  asset?: number
  params: Record<string, any>
  channels: string[]
  frequency: string
  frequency_display: string
  active: boolean
  created_at: string
  updated_at: string
}

export default function AlertsPage() {
  const [alertsData, setAlertsData] = useState<AlertEvent[]>([])
  const [alertRules, setAlertRules] = useState<AlertRule[]>([])
  const [assets, setAssets] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTypes, setSelectedTypes] = useState<string[]>([])
  const [alertRulesModalOpen, setAlertRulesModalOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null)

  // Fetch alerts from API
  const fetchAlerts = async () => {
    try {
      setLoading(true)
      // Fetch alert rules
      const rulesResponse = await api.get('/api/alerts')
      if (rulesResponse.ok) {
        setAlertRules(rulesResponse.data?.rules || [])
      }
      
      // Fetch alert events
      const eventsResponse = await api.get('/api/alerts?since=2024-01-01')
      if (eventsResponse.ok) {
        setAlertsData(eventsResponse.data?.events || [])
      }
    } catch (err) {
      console.error('Error fetching alerts:', err)
      setError('שגיאה בטעינת ההתראות')
    } finally {
      setLoading(false)
    }
  }

  // Fetch assets from API
  const fetchAssets = async () => {
    try {
      const response = await api.get('/api/assets')
      if (response.ok) {
        setAssets(response.data?.rows || [])
      }
    } catch (err) {
      console.error('Failed to fetch assets:', err)
    }
  }

  useEffect(() => {
    fetchAlerts()
    fetchAssets()
  }, [])

  // Helper function to get asset by ID
  const getAssetById = (assetId: number) => {
    return assets.find(asset => asset.id === assetId)
  }

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

  const handleEditRule = (rule: AlertRule) => {
    setEditingRule(rule)
    setAlertRulesModalOpen(true)
  }

  const handleDeleteRule = async (ruleId: number) => {
    if (!confirm('האם אתה בטוח שברצונך למחוק את כלל ההתראה?')) {
      return
    }

    try {
      const response = await fetch(`/api/alerts?ruleId=${ruleId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        setAlertRules(prev => prev.filter(rule => rule.id !== ruleId))
      } else {
        alert('שגיאה במחיקת כלל ההתראה')
      }
    } catch (err) {
      console.error('Error deleting alert rule:', err)
      alert('שגיאה במחיקת כלל ההתראה')
    }
  }

  const handleRuleSaved = () => {
    // Refresh alert rules after saving
    fetchAlerts()
    setEditingRule(null)
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
          <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
            <Button 
              onClick={() => setAlertRulesModalOpen(true)} 
              className="w-full sm:w-auto"
            >
              <Plus className="h-4 w-4 ms-2" />
              הוסף כלל התראה
            </Button>
            {unreadCount > 0 && (
              <Button onClick={markAllAsRead} variant="outline" className="w-full sm:w-auto">
                <CheckCircle className="h-4 w-4 ms-2" />
                סמן הכל כנקרא ({unreadCount})
              </Button>
            )}
          </div>
        </DashboardHeader>

        {/* Main Content Grid */}
        <div className="grid gap-6 grid-cols-1 xl:grid-cols-3">
          {/* Alerts List - Takes 2 columns on xl screens, full width on mobile */}
          <div className="xl:col-span-2 space-y-4">
            {/* Alert Rules Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <span>כללי התראות ({alertRules.length})</span>
                  <Button 
                    onClick={() => setAlertRulesModalOpen(true)} 
                    size="sm"
                    variant="outline"
                  >
                    <Plus className="h-4 w-4 ms-2" />
                    הוסף כלל
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {alertRules.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-8 space-y-4">
                    <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                      <Bell className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <div className="text-center">
                      <h3 className="text-lg font-semibold text-foreground">אין כללי התראות</h3>
                      <p className="text-muted-foreground">הגדר כללי התראות כדי לקבל עדכונים</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {alertRules.map((rule) => (
                      <div 
                        key={rule.id} 
                        className={`flex flex-col sm:flex-row sm:items-center justify-between p-3 border rounded-lg transition-colors gap-3 ${
                          editingRule?.id === rule.id 
                            ? 'bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800 ring-2 ring-blue-200 dark:ring-blue-800' 
                            : 'bg-card hover:bg-muted/50'
                        }`}
                      >
                        <div className="flex flex-col gap-3 flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant={rule.active ? "default" : "secondary"} className="text-xs">
                              {rule.active ? "פעיל" : "לא פעיל"}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {rule.trigger_type_display}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {rule.scope_display}
                            </Badge>
                          </div>
                          
                          {/* Rule Parameters */}
                          <div className="space-y-1">
                            <div className="text-sm text-muted-foreground">
                              {rule.frequency_display} • {rule.channels.map(channel => {
                                switch(channel) {
                                  case 'email': return 'אימייל'
                                  case 'whatsapp': return 'ווטסאפ'
                                  case 'sms': return 'SMS'
                                  default: return channel
                                }
                              }).join(", ")}
                            </div>
                            
                            {/* Show specific parameters based on trigger type */}
                            {rule.trigger_type === 'PRICE_DROP' && rule.params.pct && (
                              <div className="text-xs text-muted-foreground">
                                התראה על ירידה של {rule.params.pct}% במחיר
                              </div>
                            )}
                            {rule.trigger_type === 'MARKET_TREND' && rule.params.delta_pct && (
                              <div className="text-xs text-muted-foreground">
                                התראה על שינוי של {rule.params.delta_pct}% במחיר למ&quot;ר
                              </div>
                            )}
                            {rule.trigger_type === 'MARKET_TREND' && rule.params.window_days && (
                              <div className="text-xs text-muted-foreground">
                                חישוב ממוצע על {rule.params.window_days} ימים
                              </div>
                            )}
                            {rule.scope === 'asset' && rule.asset && (
                              <div className="text-xs text-muted-foreground">
                                {(() => {
                                  const asset = getAssetById(rule.asset)
                                  if (asset) {
                                    return `נכס: ${asset.address || 'כתובת לא זמינה'}, ${asset.city || 'עיר לא זמינה'}`
                                  } else {
                                    return `נכס ספציפי (ID: ${rule.asset})`
                                  }
                                })()}
                              </div>
                            )}
                            {rule.scope === 'GLOBAL' && (
                              <div className="text-xs text-muted-foreground">
                                כל הנכסים במערכת
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center justify-between sm:justify-end gap-2">
                          <div className="text-xs text-muted-foreground">
                            {new Date(rule.created_at).toLocaleDateString('he-IL')}
                          </div>
                          <div className="flex items-center gap-1">
                            {editingRule?.id === rule.id ? (
                              <div className="flex items-center gap-2 text-xs text-blue-600 dark:text-blue-400">
                                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                                עורך
                              </div>
                            ) : (
                              <>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleEditRule(rule)}
                                  className="h-9 w-9 p-0 touch-manipulation"
                                >
                                  <Edit className="h-4 w-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleDeleteRule(rule.id)}
                                  className="h-9 w-9 p-0 text-destructive hover:text-destructive touch-manipulation"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Alert Events Section */}
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
                      <div className="flex flex-col sm:flex-row gap-2 mt-4">
                        {selectedTypes.length > 0 ? (
                          <Button 
                            variant="outline" 
                            onClick={() => {
                              setSelectedTypes([])
                            }}
                          >
                            נקה סינון
                          </Button>
                        ) : (
                          <Button 
                            onClick={() => setAlertRulesModalOpen(true)}
                            className="w-full sm:w-auto"
                          >
                            <Plus className="h-4 w-4 ms-2" />
                            הגדר התראות חדשות
                          </Button>
                        )}
                      </div>
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
                          
                          {/* Show specific alert details based on payload */}
                          {alert.payload && (
                            <div className="space-y-1">
                              {alert.payload.price_change && (
                                <div className="text-xs text-muted-foreground">
                                  שינוי במחיר: {alert.payload.price_change > 0 ? '+' : ''}{alert.payload.price_change}%
                                </div>
                              )}
                              {alert.payload.new_price && (
                                <div className="text-xs text-muted-foreground">
                                  מחיר חדש: ₪{alert.payload.new_price.toLocaleString()}
                                </div>
                              )}
                              {alert.payload.old_price && (
                                <div className="text-xs text-muted-foreground">
                                  מחיר קודם: ₪{alert.payload.old_price.toLocaleString()}
                                </div>
                              )}
                              {alert.payload.area && (
                                <div className="text-xs text-muted-foreground">
                                  שטח: {alert.payload.area} מ&quot;ר
                                </div>
                              )}
                              {alert.payload.price_per_sqm && (
                                <div className="text-xs text-muted-foreground">
                                  מחיר למ&quot;ר: ₪{alert.payload.price_per_sqm.toLocaleString()}
                                </div>
                              )}
                            </div>
                          )}
                          
                          {/* Show asset details if available */}
                          {(() => {
                            // Try different possible asset ID fields
                            const assetId = alert.payload?.asset_id || alert.payload?.assetId || alert.payload?.asset
                            if (assetId) {
                              const asset = getAssetById(assetId)
                              if (asset) {
                                return (
                                  <div className="text-xs text-muted-foreground space-y-1">
                                    <div className="font-medium">פרטי הנכס:</div>
                                    <div>📍 {asset.address || 'כתובת לא זמינה'}</div>
                                    <div>🏙️ {asset.city || 'עיר לא זמינה'}</div>
                                    {asset.type && <div>🏠 {asset.type}</div>}
                                    {asset.area && <div>📐 {asset.area} מ&quot;ר</div>}
                                    {asset.price && <div>💰 ₪{asset.price.toLocaleString()}</div>}
                                  </div>
                                )
                              } else {
                                // Debug: show what we're looking for
                                console.log('Asset not found for ID:', assetId, 'Available assets:', assets.map(a => ({ id: a.id, address: a.address })))
                                return (
                                  <div className="text-xs text-muted-foreground">
                                    נכס לא נמצא (ID: {assetId})
                                  </div>
                                )
                              }
                            }
                            return null
                          })()}
                          
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

          {/* Sidebar - Takes 1 column on xl screens, full width on mobile */}
          <div className="space-y-4 order-first xl:order-last">
            {/* Quick Stats Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">סטטיסטיקות מהירות</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <div className="text-2xl font-bold text-foreground">{alertRules.length}</div>
                    <div className="text-xs text-muted-foreground">כללי התראות</div>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <div className="text-2xl font-bold text-green-600">
                      {alertRules.filter(rule => rule.active).length}
                    </div>
                    <div className="text-xs text-muted-foreground">פעילים</div>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <div className="text-2xl font-bold text-foreground">{filteredAlerts.length}</div>
                    <div className="text-xs text-muted-foreground">התראות</div>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <div className="text-2xl font-bold text-blue-600">{unreadCount}</div>
                    <div className="text-xs text-muted-foreground">לא נקראו</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Filter Options Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">סינון התראות</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <label className="text-sm font-medium">סוג התראה</label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {Object.entries(ALERT_TYPE_LABELS).map(([key, label]) => (
                      <Badge
                        key={key}
                        variant={
                          selectedTypes.includes(key)
                            ? 'default'
                            : 'neutral'
                        }
                        className="cursor-pointer text-center py-2 px-3 touch-manipulation"
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
            <div className="grid gap-3 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
              {Object.entries(ALERT_TYPE_LABELS).map(([key, label]) => (
                <div key={key} className="flex flex-col items-center gap-2 text-center p-3 rounded-lg hover:bg-muted/50 transition-colors touch-manipulation">
                  <div className="w-8 h-8 flex items-center justify-center">
                    {getAlertIcon(key)}
                  </div>
                  <span className="text-xs sm:text-sm leading-tight">{label}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Alert Rules Modal */}
        <Dialog open={alertRulesModalOpen} onOpenChange={(open) => {
          setAlertRulesModalOpen(open)
          if (!open) {
            setEditingRule(null)
          }
        }}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto mx-4 sm:mx-0">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-lg sm:text-xl">
                <Settings className="h-5 w-5" />
                {editingRule ? 'עריכת כלל התראה' : 'ניהול כללי התראות'}
              </DialogTitle>
            </DialogHeader>
            <div className="mt-4">
              <AlertRulesManager 
                editingRule={editingRule as any}
                onRuleSaved={handleRuleSaved}
              />
            </div>
          </DialogContent>
        </Dialog>
      </DashboardShell>
    </DashboardLayout>
  )
}