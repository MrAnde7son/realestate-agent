'use client'
import React, { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface PropertyTypeRow {
  property_type: string
  count: number
}

interface MarketActivityRow {
  area: string
  count: number
}

export default function AnalyticsPage() {
  const [propertyTypes, setPropertyTypes] = useState<PropertyTypeRow[]>([])
  const [marketActivity, setMarketActivity] = useState<MarketActivityRow[]>([])

  useEffect(() => {
    fetch('/api/analytics/property-types')
      .then(res => res.json())
      .then(data => setPropertyTypes(data.rows || []))
      .catch(err => console.error('Error loading property types:', err))

    fetch('/api/analytics/market-activity')
      .then(res => res.json())
      .then(data => setMarketActivity(data.rows || []))
      .catch(err => console.error('Error loading market activity:', err))
  }, [])

  const totalTypes = propertyTypes.reduce((sum, r) => sum + r.count, 0)
  const maxArea = marketActivity.reduce((max, r) => Math.max(max, r.count), 0)

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <h1 className="text-3xl font-bold">אנליטיקה</h1>
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>התפלגות סוגי נכסים</CardTitle>
            </CardHeader>
            <CardContent>
              {propertyTypes.length === 0 && (
                <p className="text-sm text-muted-foreground">אין נתונים</p>
              )}
              {propertyTypes.map(pt => {
                const pct = totalTypes ? Math.round((pt.count / totalTypes) * 100) : 0
                return (
                  <div key={pt.property_type} className="space-y-1 mb-2">
                    <div className="flex justify-between text-sm">
                      <span>{pt.property_type}</span>
                      <span>{pt.count}</span>
                    </div>
                    <div className="h-2 bg-primary/20 rounded">
                      <div className="h-full bg-primary rounded" style={{ width: `${pct}%` }}></div>
                    </div>
                  </div>
                )
              })}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>פעילות שוק לפי אזור</CardTitle>
            </CardHeader>
            <CardContent>
              {marketActivity.length === 0 && (
                <p className="text-sm text-muted-foreground">אין נתונים</p>
              )}
              {marketActivity.map(ma => {
                const pct = maxArea ? Math.round((ma.count / maxArea) * 100) : 0
                return (
                  <div key={ma.area} className="space-y-1 mb-2">
                    <div className="flex justify-between text-sm">
                      <span>{ma.area}</span>
                      <span>{ma.count}</span>
                    </div>
                    <div className="h-2 bg-primary/20 rounded">
                      <div className="h-full bg-primary rounded" style={{ width: `${pct}%` }}></div>
                    </div>
                  </div>
                )
              })}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
