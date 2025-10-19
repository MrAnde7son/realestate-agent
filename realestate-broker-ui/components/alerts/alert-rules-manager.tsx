"use client"
import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/Badge'
import { Separator } from '@/components/ui/separator'
import { Plus, Trash2, TestTube, Bell, Building } from 'lucide-react'
import { useAuth } from '@/lib/auth-context'
import { api } from '@/lib/api-client'
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
import type { Asset } from '@/lib/normalizers/asset'

interface AlertRule {
  id?: number
  trigger_type: AlertType
  params: Record<string, any>
  channels: AlertChannel[]
  frequency: AlertFrequency
  scope: AlertScope
  asset?: number // Backend expects 'asset', not 'asset_id'
  active: boolean
}

interface AlertRulesManagerProps {
  assetId?: number
  editingRule?: AlertRule | null
  onRuleSaved?: () => void
}

export default function AlertRulesManager({ assetId, editingRule, onRuleSaved }: AlertRulesManagerProps) {
  const { refreshUser } = useAuth()
  const [rules, setRules] = useState<AlertRule[]>([])
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [assets, setAssets] = useState<Asset[]>([])
  const [assetsLoading, setAssetsLoading] = useState(false)

  // Helper functions for translation
  const translateTriggerType = (type: string) => {
    return ALERT_TYPE_LABELS[type as keyof typeof ALERT_TYPE_LABELS] || type
  }

  const translateScope = (scope: string) => {
    return ALERT_SCOPE_LABELS[scope as keyof typeof ALERT_SCOPE_LABELS] || scope
  }

  useEffect(() => {
    if (editingRule) {
      // When editing, only show the specific rule being edited
      const frontendRule: AlertRule = {
        id: editingRule.id,
        trigger_type: editingRule.trigger_type as AlertType,
        params: editingRule.params,
        channels: editingRule.channels as AlertChannel[],
        frequency: editingRule.frequency as AlertFrequency,
        scope: editingRule.scope as AlertScope,
        asset: editingRule.asset,
        active: editingRule.active
      }
      setRules([frontendRule])
    } else {
      // When not editing, load all rules
      loadRules()
    }
    loadAssets()
  }, [assetId, editingRule])

  const loadRules = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/alerts')
      if (response.ok) {
        setRules(response.data?.rules || [])
      }
    } catch (error) {
      console.error('Failed to load alert rules:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadAssets = async () => {
    try {
      setAssetsLoading(true)
      const response = await api.get('/api/assets')
      if (response.ok) {
        setAssets(response.data?.rows || [])
      }
    } catch (error) {
      console.error('Failed to load assets:', error)
    } finally {
      setAssetsLoading(false)
    }
  }

  const getSelectedAsset = (assetId?: number) => {
    if (!assetId) return null
    return assets.find(asset => asset.id === assetId) || null
  }

  const addRule = () => {
    const newRule: AlertRule = {
      trigger_type: ALERT_TYPES.PRICE_DROP,
      params: ALERT_DEFAULT_PARAMS[ALERT_TYPES.PRICE_DROP],
      channels: [ALERT_CHANNELS.EMAIL],
      frequency: ALERT_FREQUENCIES.IMMEDIATE,
      scope: assetId ? ALERT_SCOPES.ASSET : ALERT_SCOPES.GLOBAL,
      asset: assetId, // Backend expects 'asset', not 'asset_id'
      active: true
    }
    setRules([...rules, newRule])
  }

  const updateRule = (index: number, updates: Partial<AlertRule>) => {
    const updatedRules = [...rules]
    updatedRules[index] = { ...updatedRules[index], ...updates }
    
    // Update params when trigger type changes
    if (updates.trigger_type) {
      updatedRules[index].params = ALERT_DEFAULT_PARAMS[updates.trigger_type as keyof typeof ALERT_DEFAULT_PARAMS] || {}
    }
    
    // Update scope and asset when scope changes
    if (updates.scope) {
      if (updates.scope === ALERT_SCOPES.ASSET) {
        // If changing to asset scope, keep current asset or set to first available
        updatedRules[index].asset = updatedRules[index].asset || (assets.length > 0 ? assets[0].id : undefined)
      } else {
        // If changing to global scope, clear asset
        updatedRules[index].asset = undefined
      }
    }
    
    // Update scope when asset changes
    if (updates.asset !== undefined) {
      if (updates.asset) {
        updatedRules[index].scope = ALERT_SCOPES.ASSET
      } else {
        updatedRules[index].scope = ALERT_SCOPES.GLOBAL
      }
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
      
      // Debug logging
      console.log('🔍 Frontend - Sending alert rule:', rule)
      
      const isUpdate = !!rule.id
      const url = isUpdate ? `/api/alerts?id=${rule.id}` : '/api/alerts'
      
      const response = isUpdate 
        ? await api.put(url, rule)
        : await api.post(url, rule)
      
      if (response.ok) {
        const updatedRules = [...rules]
        updatedRules[index] = { ...rule, id: response.data?.id || rule.id }
        setRules(updatedRules)
        
        // Refresh user data to update onboarding progress
        await refreshUser()
        
        // Call the callback if provided
        if (onRuleSaved) {
          onRuleSaved()
        }
      } else {
        alert(`Failed to save rule: ${response.error || 'Unknown error'}`)
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
      const response = await api.post('/api/alerts', { test: true })
      
      if (response.ok) {
        alert('Test alert sent successfully!')
      } else {
        alert(`Failed to send test: ${response.error || 'Unknown error'}`)
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
            dir="ltr"
            inputMode="numeric"
            className="text-left"
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
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              {editingRule ? 'עריכת כלל התראה' : 'כללי התראות'}
            </CardTitle>
            <CardDescription>
              {editingRule 
                ? 'ערוך את הגדרות כלל ההתראה הנבחר'
                : 'הגדר התראות אוטומטיות על שינויים בנכסים'
              }
            </CardDescription>
            {editingRule && (
              <div className="mt-2 p-2 bg-blue-50 dark:bg-blue-950/20 rounded-md border border-blue-200 dark:border-blue-800">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  <strong>עורך כלל:</strong> {translateTriggerType(editingRule.trigger_type)} - {translateScope(editingRule.scope)}
                </p>
                {editingRule.scope === 'asset' && editingRule.asset && (() => {
                  const asset = assets.find(a => a.id === editingRule.asset)
                  if (asset) {
                    return (
                      <div className="mt-2 text-xs text-blue-600 dark:text-blue-400">
                        <div className="font-medium">נכס נבחר:</div>
                        <div>📍 {asset.address || 'כתובת לא זמינה'}</div>
                        <div>🏙️ {asset.city || 'עיר לא זמינה'}</div>
                        {asset.type && <div>🏠 {asset.type}</div>}
                        {asset.area && <div>📐 {asset.area} מ&quot;ר</div>}
                      </div>
                    )
                  }
                  return (
                    <div className="mt-2 text-xs text-blue-600 dark:text-blue-400">
                      נכס ספציפי (ID: {editingRule.asset})
                    </div>
                  )
                })()}
              </div>
            )}
          </div>
          <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
            {!editingRule && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={testChannels}
                  disabled={testing}
                  className="w-full sm:w-auto"
                >
                  <TestTube className="h-4 w-4 ms-2" />
                  {testing ? 'שולח...' : 'בדוק ערוצים'}
                </Button>
                <Button size="sm" onClick={addRule} className="w-full sm:w-auto">
                  <Plus className="h-4 w-4 ms-2" />
                  הוסף כלל
                </Button>
              </>
            )}
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
            <p className="text-sm">לחץ על &quot;הוסף כלל&quot; כדי להתחיל</p>
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
                  <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
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
                          <div key={key} className="flex items-center space-x-2 rtl:space-x-reverse">
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

                    {/* Asset Selection - Only show when scope is ASSET and not pre-selected from asset table */}
                    {rule.scope === ALERT_SCOPES.ASSET && !assetId && (
                      <div className="space-y-2">
                        <Label>נכס ספציפי</Label>
                        <Select
                          value={rule.asset?.toString() || ''}
                          onValueChange={(value) => updateRule(index, { asset: value ? parseInt(value) : undefined })}
                          disabled={assetsLoading}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder={assetsLoading ? "טוען נכסים..." : "בחר נכס"} />
                          </SelectTrigger>
                          <SelectContent>
                            {assets.map((asset) => (
                              <SelectItem key={asset.id} value={asset.id.toString()}>
                                <div className="flex items-center gap-2">
                                  <Building className="h-4 w-4" />
                                  <div className="flex flex-col">
                                    <span className="font-medium">{asset.address}</span>
                                    <span className="text-xs text-muted-foreground">
                                      {asset.city} • {asset.type} • {asset.area ? `${asset.area} מ"ר` : '—'}
                                    </span>
                                  </div>
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        {rule.asset && (
                          <div className="text-xs text-muted-foreground">
                            נכס נבחר: {getSelectedAsset(rule.asset)?.address || 'לא נמצא'}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Show selected asset info when asset is pre-selected from asset table */}
                    {assetId && rule.scope === ALERT_SCOPES.ASSET && (
                      <div className="space-y-2">
                        <Label>נכס נבחר</Label>
                        <div className="p-3 bg-muted rounded-lg">
                          <div className="flex items-center gap-2">
                            <Building className="h-4 w-4" />
                            <div>
                              <div className="font-medium">{getSelectedAsset(assetId)?.address || 'טוען...'}</div>
                              <div className="text-xs text-muted-foreground">
                                {getSelectedAsset(assetId)?.city} • {getSelectedAsset(assetId)?.type}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Parameters */}
                  {ALERT_PARAM_VALIDATION[rule.trigger_type as keyof typeof ALERT_PARAM_VALIDATION] && (
                    <div className="space-y-4">
                      <Separator />
                      <h4 className="font-medium">פרמטרים</h4>
                      <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
                        {Object.entries(ALERT_PARAM_VALIDATION[rule.trigger_type as keyof typeof ALERT_PARAM_VALIDATION]).map(([paramKey, paramConfig]) => (
                          <div key={paramKey} className="space-y-2">
                            <Label>{(paramConfig as any).label || ALERT_PARAM_LABELS[paramKey as keyof typeof ALERT_PARAM_LABELS] || paramKey}</Label>
                            {renderParameterInput(rule, paramKey, paramConfig as any)}
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
