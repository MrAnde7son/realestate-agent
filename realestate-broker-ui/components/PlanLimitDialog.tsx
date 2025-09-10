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
    message: string
    current_plan: string
    asset_limit: number
    assets_used: number
    remaining: number
  }
}

const planIcons = {
  free: Star,
  basic: Zap,
  pro: Crown,
}

const planNames = {
  free: 'חבילה חינמית',
  basic: 'חבילה בסיסית',
  pro: 'חבילה מקצועית',
}

export default function PlanLimitDialog({ open, onOpenChange, error }: PlanLimitDialogProps) {
  const router = useRouter()
  const Icon = planIcons[error.current_plan as keyof typeof planIcons] || Star

  const handleUpgrade = () => {
    onOpenChange(false)
    router.push('/billing')
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-amber-500" />
            <DialogTitle>הגעת למגבלת הנכסים</DialogTitle>
          </div>
          <DialogDescription>
            {error.message}
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Current Plan Info */}
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <Icon className="h-4 w-4 text-primary" />
              <span className="font-medium">
                {planNames[error.current_plan as keyof typeof planNames] || error.current_plan}
              </span>
            </div>
            <Badge variant="outline">
              {error.assets_used} / {error.asset_limit} נכסים
            </Badge>
          </div>

          {/* Usage Details */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>נכסים בשימוש:</span>
              <span className="font-medium">{error.assets_used}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>מגבלה:</span>
              <span className="font-medium">{error.asset_limit}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>נותרו:</span>
              <span className="font-medium text-red-600">{error.remaining}</span>
            </div>
          </div>

          {/* Upgrade Benefits */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium">שדרוג החבילה יאפשר לך:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• עד 25 נכסים במעקב (חבילה בסיסית)</li>
              <li>• נכסים ללא הגבלה (חבילה מקצועית)</li>
              <li>• תכונות מתקדמות נוספות</li>
              <li>• תמיכה מועדפת</li>
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
