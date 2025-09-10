'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PlanInfo } from '@/lib/auth'
import { authAPI } from '@/lib/auth'
import { AlertCircle, CheckCircle, Crown, Zap, Star } from 'lucide-react'

interface PlanInfoProps {
  className?: string
}

const planIcons = {
  free: Star,
  basic: Zap,
  pro: Crown,
}

export default function PlanInfoComponent({ className }: PlanInfoProps) {
  const [planInfo, setPlanInfo] = useState<PlanInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadPlanData()
  }, [])

  const loadPlanData = async () => {
    try {
      setLoading(true)
      const planInfoData = await authAPI.getPlanInfo()
      setPlanInfo(planInfoData)
    } catch (err) {
      console.error('Error loading plan data:', err)
      setError('Failed to load plan information')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error || !planInfo) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span>{error || 'Failed to load plan information'}</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  const Icon = planIcons[planInfo.plan_name as keyof typeof planIcons] || Star
  const isExpired = planInfo.is_expired
  const isUnlimited = planInfo.limits.assets.limit === -1

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">{planInfo.display_name}</CardTitle>
          </div>
          {isExpired && (
            <Badge variant="destructive">Expired</Badge>
          )}
        </div>
        <CardDescription>{planInfo.description}</CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Asset Usage */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>נכסים במעקב</span>
            <span className="font-medium">
              {planInfo.limits.assets.used} / {isUnlimited ? '∞' : planInfo.limits.assets.limit}
            </span>
          </div>
          {!isUnlimited && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{ 
                  width: `${Math.min((planInfo.limits.assets.used / planInfo.limits.assets.limit) * 100, 100)}%` 
                }}
              />
            </div>
          )}
          {planInfo.limits.assets.remaining === 0 && !isUnlimited && (
            <div className="flex items-center gap-1 text-sm text-amber-600">
              <AlertCircle className="h-3 w-3" />
              <span>הגעת למגבלת הנכסים שלך</span>
            </div>
          )}
        </div>

        {/* Features */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium">תכונות זמינות:</h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(planInfo.features).map(([feature, enabled]) => (
              <div key={feature} className="flex items-center gap-1">
                {enabled ? (
                  <CheckCircle className="h-3 w-3 text-green-500" />
                ) : (
                  <div className="h-3 w-3 rounded-full border border-gray-300" />
                )}
                <span className={enabled ? 'text-green-700' : 'text-gray-500'}>
                  {getFeatureName(feature)}
                </span>
              </div>
            ))}
          </div>
        </div>

      </CardContent>
    </Card>
  )
}

function getFeatureName(feature: string): string {
  const featureNames: Record<string, string> = {
    advanced_analytics: 'ניתוח מתקדם',
    data_export: 'ייצוא נתונים',
    api_access: 'גישת API',
    priority_support: 'תמיכה מועדפת',
    custom_reports: 'דוחות מותאמים',
  }
  return featureNames[feature] || feature
}
