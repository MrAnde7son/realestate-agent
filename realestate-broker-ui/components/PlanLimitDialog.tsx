'use client'

import React from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/Badge'
import { AlertCircle, Crown, Zap, Star } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface PlanLimitDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  error: {
    message?: string
    current_plan?: string
    asset_limit?: number
    assets_used?: number
    remaining?: number
  }
}

const planIcons = {
  free: Star,
  basic: Zap,
  pro: Crown,
}

const planNames = {
  free: 'פרטי',
  basic: 'בסיסי',
  pro: 'עיסקי',
}

export default function PlanLimitDialog({ open, onOpenChange, error }: PlanLimitDialogProps) {
  const router = useRouter()
  const Icon = planIcons[error.current_plan as keyof typeof planIcons] || Star

  const handleUpgrade = () => {
    onOpenChange(false)
    router.push('/billing')
  }

  // Safe access to error properties with defaults
  const currentPlan = error?.current_plan || 'basic';
  const assetLimit = error?.asset_limit ?? 0;
  const assetsUsed = error?.assets_used ?? 0;
  const remaining = error?.remaining ?? 0;
  const errorMessage = error?.message || (error as any)?.error || 'הגעת למגבלת הנכסים בחשבונך';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-amber-500" />
            <DialogTitle>הגעת למגבלת הנכסים</DialogTitle>
          </div>
          <DialogDescription>
            {errorMessage}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Current Plan Info */}
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <Icon className="h-4 w-4 text-primary" />
              <span className="font-medium">
                {planNames[currentPlan as keyof typeof planNames] || currentPlan}
              </span>
            </div>
            <Badge variant="outline">
              {assetsUsed} / {assetLimit} נכסים
            </Badge>
          </div>

          {/* Usage Details */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>נכסים בשימוש:</span>
              <span className="font-medium">{assetsUsed}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>מגבלה:</span>
              <span className="font-medium">{assetLimit}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>נותרו:</span>
              <span className="font-medium text-red-600">{remaining}</span>
            </div>
          </div>

          {/* Upgrade Benefits */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium">שדרוג המסלול יאפשר לך:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• עד 10 נכסים בחודש (מסלול בסיסי)</li>
              <li>• דוחות עד 25 בחודש (מסלול בסיסי)</li>
              <li>• נכסים והתראות ללא הגבלה (מסלול עיסקי)</li>
              <li>• יכולות מתקדמות, כולל תמיכה עדיפה ו-AI</li>
            </ul>
          </div>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            ביטול
          </Button>
          <Button onClick={handleUpgrade} className="w-full sm:w-auto">
            שדרוג חבילה
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
