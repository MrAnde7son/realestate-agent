"use client"
import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Plus, Trash2, TestTube, Bell } from 'lucide-react'
import { 
  ALERT_TYPES, 
  ALERT_TYPE_LABELS, 
  ALERT_FREQUENCIES, 
  ALERT_FREQUENCY_LABELS,
  ALERT_SCOPES,
  ALERT_SCOPE_LABELS,
  ALERT_CHANNELS,
  ALERT_CHANNEL_LABELS,
  ALERT_DEFAULT_PARAMS,
  ALERT_PARAM_VALIDATION,
  ALERT_PARAM_LABELS,
  type AlertType,
  type AlertFrequency,
  type AlertScope,
  type AlertChannel
} from '@/lib/alert-constants'

interface AlertRule {
  id?: number
  trigger_type: AlertType
  params: Record<string, any>
  channels: AlertChannel[]
  frequency: AlertFrequency
  scope: AlertScope
  asset_id?: number
  active: boolean
}

interface AlertRulesManagerProps {
  assetId?: number
}

export default function AlertRulesManager({ assetId }: AlertRulesManagerProps) {
  const [rules, setRules] = useState<AlertRule[]>([])
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)

  useEffect(() => {
    loadRules()
  }, [assetId])

  const loadRules = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/alerts')
      if (response.ok) {
        const data = await response.json()
        setRules(data.rules || [])
      }
    } catch (error) {
      console.error('Failed to load alert rules:', error)
    } finally {
      setLoading(false)
    }
  }

  const addRule = () => {
    const newRule: AlertRule = {
      trigger_type: ALERT_TYPES.PRICE_DROP,
      params: ALERT_DEFAULT_PARAMS[ALERT_TYPES.PRICE_DROP],
      channels: [ALERT_CHANNELS.EMAIL],
      frequency: ALERT_FREQUENCIES.IMMEDIATE,
      scope: assetId ? ALERT_SCOPES.ASSET : ALERT_SCOPES.GLOBAL,
      asset_id: assetId,
      active: true
    }
    setRules([...rules, newRule])
  }

  const updateRule = (index: number, updates: Partial<AlertRule>) => {
    const updatedRules = [...rules]
    updatedRules[index] = { ...updatedRules[index], ...updates }
    
    // Update params when trigger type changes
    if (updates.trigger_type) {
      updatedRules[index].params = ALERT_DEFAULT_PARAMS[updates.trigger_type] || {}
    }
    
    setRules(updatedRules)
  }

  const removeRule = (index: number) => {
    const updatedRules = rules.filter((_, i) => i !== index)
    setRules(updatedRules)
  }

  const saveRule = async (rule: AlertRule, index: number) => {
    try {
      setLoading(true)
      const response = await fetch('/api/alerts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(rule)
      })
      
      if (response.ok) {
        const data = await response.json()
        const updatedRules = [...rules]
        updatedRules[index] = { ...rule, id: data.id }
        setRules(updatedRules)
      } else {
        const errorData = await response.json()
        alert(`Failed to save rule: ${errorData.error || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Failed to save rule:', error)
      alert('Failed to save rule')
    } finally {
      setLoading(false)
    }
  }

  const testChannels = async () => {
    try {
      setTesting(true)
      const response = await fetch('/api/alerts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ test: true })
      })
      
      if (response.ok) {
        alert('Test alert sent successfully!')
      } else {
        const errorData = await response.json()
        alert(`Failed to send test: ${errorData.error || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Failed to send test:', error)
      alert('Failed to send test')
    } finally {
      setTesting(false)
    }
  }

  const renderParameterInput = (rule: AlertRule, paramKey: string, paramConfig: any) => {
    const value = rule.params[paramKey] || paramConfig.min || 0
    
    if (paramConfig.type === 'number' || paramConfig.type === 'integer') {
      return (
        <div className="space-y-1">
          <Input
            type="number"
            value={value}
            min={paramConfig.min}
            max={paramConfig.max}
            onChange={(e) => {
              const newValue = paramConfig.type === 'integer' ? parseInt(e.target.value) : parseFloat(e.target.value)
              updateRule(rules.indexOf(rule), {
                params: { ...rule.params, [paramKey]: newValue }
              })
            }}
          />
          <p className="text-xs text-muted-foreground">
            {paramKey === 'pct' && 'אחוז הירידה הנדרש כדי להפעיל התראה'}
            {paramKey === 'delta_pct' && 'אחוז השינוי הנדרש במחיר למ"ר'}
            {paramKey === 'window_days' && 'מספר הימים לחישוב הממוצע'}
            {paramKey === 'radius_km' && 'רדיוס החיפוש בקילומטרים'}
            {paramKey === 'radius_m' && 'רדיוס החיפוש במטרים'}
            {paramKey === 'misses' && 'מספר הפעמים שהנכס צריך להיות חסר'}
          </p>
        </div>
      )
    }
    
    return null
  }

  if (loading) {
    return <div className="text-center py-4">טוען...</div>
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              כללי התראות
            </CardTitle>
            <CardDescription>
              הגדר התראות אוטומטיות על שינויים בנכסים
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={testChannels}
              disabled={testing}
            >
              <TestTube className="h-4 w-4 ml-2" />
              {testing ? 'שולח...' : 'בדוק ערוצים'}
            </Button>
            <Button size="sm" onClick={addRule}>
              <Plus className="h-4 w-4 ml-2" />
              הוסף כלל
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Information about notification setup */}
        <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">הגדרת ערוצי התראות</h4>
          <p className="text-sm text-blue-700 dark:text-blue-300 mb-2">
            כדי לקבל התראות, וודא שהגדרת את פרטי הקשר שלך:
          </p>
          <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
            <li>• <strong>אימייל:</strong> מוגדר בפרופיל המשתמש</li>
            <li>• <strong>טלפון:</strong> מוגדר בפרופיל המשתמש (לווטסאפ) - <a href="/profile" className="underline">לחץ כאן לעריכה</a></li>
            <li>• <strong>העדפות התראות:</strong> מוגדרות בפרופיל המשתמש - <a href="/profile" className="underline">לחץ כאן לעריכה</a></li>
          </ul>
        </div>

        {rules.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Bell className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>אין כללי התראות מוגדרים</p>
            <p className="text-sm">לחץ על "הוסף כלל" כדי להתחיל</p>
          </div>
        ) : (
          rules.map((rule, index) => (
            <Card key={index} className="border-l-4 border-l-blue-500">
              <CardContent className="pt-4">
                <div className="space-y-4">
                  {/* Rule Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">
                        {ALERT_TYPE_LABELS[rule.trigger_type]}
                      </Badge>
                      <Badge variant="secondary">
                        {ALERT_FREQUENCY_LABELS[rule.frequency]}
                      </Badge>
                      <Badge variant="outline">
                        {ALERT_SCOPE_LABELS[rule.scope]}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={rule.active}
                        onCheckedChange={(checked) => updateRule(index, { active: checked })}
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeRule(index)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <Separator />

                  {/* Rule Configuration */}
                  <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label>סוג התראה</Label>
                      <Select
                        value={rule.trigger_type}
                        onValueChange={(value) => updateRule(index, { trigger_type: value as AlertType })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(ALERT_TYPE_LABELS).map(([key, label]) => (
                            <SelectItem key={key} value={key}>
                              {label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>תדירות</Label>
                      <Select
                        value={rule.frequency}
                        onValueChange={(value) => updateRule(index, { frequency: value as AlertFrequency })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(ALERT_FREQUENCY_LABELS).map(([key, label]) => (
                            <SelectItem key={key} value={key}>
                              {label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>ערוצי התראה</Label>
                      <div className="space-y-2">
                        {Object.entries(ALERT_CHANNEL_LABELS).map(([key, label]) => (
                          <div key={key} className="flex items-center space-x-2">
                            <Switch
                              checked={rule.channels.includes(key as AlertChannel)}
                              onCheckedChange={(checked) => {
                                const newChannels = checked
                                  ? [...rule.channels, key as AlertChannel]
                                  : rule.channels.filter(c => c !== key)
                                updateRule(index, { channels: newChannels })
                              }}
                            />
                            <Label className="text-sm">{label}</Label>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>היקף</Label>
                      <Select
                        value={rule.scope}
                        onValueChange={(value) => updateRule(index, { scope: value as AlertScope })}
                        disabled={!!assetId} // Disable if asset-specific
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(ALERT_SCOPE_LABELS).map(([key, label]) => (
                            <SelectItem key={key} value={key}>
                              {label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Parameters */}
                  {ALERT_PARAM_VALIDATION[rule.trigger_type] && (
                    <div className="space-y-4">
                      <Separator />
                      <h4 className="font-medium">פרמטרים</h4>
                      <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
                        {Object.entries(ALERT_PARAM_VALIDATION[rule.trigger_type]).map(([paramKey, paramConfig]) => (
                          <div key={paramKey} className="space-y-2">
                            <Label>{paramConfig.label || ALERT_PARAM_LABELS[paramKey as keyof typeof ALERT_PARAM_LABELS] || paramKey}</Label>
                            {renderParameterInput(rule, paramKey, paramConfig)}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Save Button */}
                  <div className="flex justify-end">
                    <Button
                      size="sm"
                      onClick={() => saveRule(rule, index)}
                      disabled={loading}
                    >
                      {rule.id ? 'עדכן' : 'שמור'}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </CardContent>
    </Card>
  )
}
