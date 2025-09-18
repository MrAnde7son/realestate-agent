import { useState, useEffect } from 'react'
import { api } from './api-client'
import { useAuth } from './auth-context'

export interface DashboardData {
  totalassets: number
  activeAlerts: number
  totalReports: number
  averageReturn: number
  marketTrend: 'up' | 'down' | 'stable'
  recentActivity: Array<{
    id: string
    type: 'asset' | 'alert' | 'client' | 'transaction'
    title: string
    timestamp: string
    value?: number
  }>
  marketData: Array<{
    month: string
    avgPrice: number
    transactions: number
    volume: number
  }>
  propertyTypes: Array<{
    type: string
    count: number
    percentage: number
  }>
  topAreas: Array<{
    area: string
    assets: number
    avgPrice: number
    trend: number
  }>
}

export function useDashboardData() {
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Don't fetch data if auth is still loading
    if (authLoading) {
      setLoading(false)
      setError(null)
      setData(null)
      return
    }

    // For unauthenticated users, only fetch public data (assets)
    // For authenticated users, fetch all data

    const fetchDashboardData = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch data from multiple API endpoints
        // For unauthenticated users, only fetch assets (public data)
        // For authenticated users, fetch all data
        const apiCalls = isAuthenticated 
          ? [
              api.get('/api/assets'),
              api.get('/api/alerts'),
              api.get('/api/reports')
            ]
          : [api.get('/api/assets')] // Only fetch assets for guests

        const responses = await Promise.allSettled(apiCalls)
        
        // Extract responses based on authentication status
        const [assetsRes, alertsRes, reportsRes] = isAuthenticated 
          ? responses
          : [responses[0], { status: 'rejected', reason: new Error('Not authenticated') }, { status: 'rejected', reason: new Error('Not authenticated') }]

        // Process assets data
        let totalassets = 0
        let propertyTypes: Array<{ type: string; count: number; percentage: number }> = []
        let topAreas: Array<{ area: string; assets: number; avgPrice: number; trend: number }> = []
        let totalPropertyValue = 0
        let propertyReturns: number[] = []
        let assetPriceByMonth: Record<string, { sum: number; count: number }> = {}

        if (assetsRes.status === 'fulfilled' && assetsRes.value.ok) {
          const assets = assetsRes.value.data?.rows || []
          totalassets = assets.length

          // Analyze property types and calculate individual returns
          const typeCounts: Record<string, number> = {}
          const areaData: Record<string, { count: number; totalPrice: number; totalRent: number }> = {}

          assets.forEach((asset: any) => {
            // Count property types
            const type = asset.propertyType || asset.type || 'לא ידוע'
            typeCounts[type] = (typeCounts[type] || 0) + 1

            // Use cap rate if available, otherwise fallback to rent/price
            if (asset.capRatePct !== undefined && asset.capRatePct !== null) {
              propertyReturns.push(asset.capRatePct)
            } else {
              const price = asset.price || 0
              const rent = asset.monthlyRent || asset.rent || 0
              if (price > 0 && rent > 0) {
                const annualReturn = (rent * 12 / price) * 100
                propertyReturns.push(annualReturn)
              }
            }

            const price = asset.price || 0
            totalPropertyValue += price

            // Track average price by month
            if (price > 0 && asset.created_at) {
              const d = new Date(asset.created_at)
              const key = `${d.getFullYear()}-${d.getMonth()}`
              if (!assetPriceByMonth[key]) {
                assetPriceByMonth[key] = { sum: 0, count: 0 }
              }
              assetPriceByMonth[key].sum += price
              assetPriceByMonth[key].count++
            }

            // Analyze areas
            const area = asset.city || 'לא ידוע'
            if (!areaData[area]) {
              areaData[area] = { count: 0, totalPrice: 0, totalRent: 0 }
            }
            areaData[area].count++
            areaData[area].totalPrice += price
            areaData[area].totalRent += asset.monthlyRent || asset.rent || 0
          })

          // Convert to arrays
          propertyTypes = Object.entries(typeCounts).map(([type, count]) => ({
            type,
            count,
            percentage: Math.round((count / totalassets) * 100)
          }))

          topAreas = Object.entries(areaData)
            .map(([area, data]) => ({
              area,
              assets: data.count,
              avgPrice: Math.round(data.totalPrice / data.count),
              trend: Math.floor(Math.random() * 10) - 2 // Mock trend data
            }))
            .sort((a, b) => b.assets - a.assets)
            .slice(0, 4)
        }

        // Calculate average return as the mean of individual property returns
        let averageReturn = 0
        if (propertyReturns.length > 0) {
          const sumReturns = propertyReturns.reduce((sum, ret) => sum + ret, 0)
          averageReturn = Math.round((sumReturns / propertyReturns.length) * 100) / 100
        }

        // Process alerts data (only for authenticated users)
        let activeAlerts = 0
        if (isAuthenticated && alertsRes.status === 'fulfilled' && alertsRes.value?.ok) {
          const alerts = alertsRes.value.data?.alerts || []
          // Count unread alerts as active alerts
          activeAlerts = alerts.filter((alert: any) => !alert.isRead).length
        }

        // Process reports data (only for authenticated users)
        let totalReports = 0
        if (isAuthenticated && reportsRes.status === 'fulfilled' && reportsRes.value?.ok) {
          const reports = reportsRes.value.data?.rows || reportsRes.value.data?.reports || []
          totalReports = reports.length
        }

        // Fetch comparables for all assets to build market data (only for authenticated users)
        let comparables: any[] = []
        if (isAuthenticated && assetsRes.status === 'fulfilled' && assetsRes.value.ok) {
          const assets = assetsRes.value.data?.rows || []
          const compResponses = await Promise.allSettled(
            assets.map((a: any) => api.get(`/api/assets/${a.id}/appraisal`))
          )
          compResponses.forEach(res => {
            if (res.status === 'fulfilled' && res.value.ok) {
              comparables.push(...(res.value.data?.comps || []))
            }
          })
        }

        const compByMonth: Record<string, { count: number; volume: number }> = {}
        comparables.forEach(comp => {
          if (comp.date && comp.price) {
            const d = new Date(comp.date)
            const key = `${d.getFullYear()}-${d.getMonth()}`
            if (!compByMonth[key]) {
              compByMonth[key] = { count: 0, volume: 0 }
            }
            compByMonth[key].count++
            compByMonth[key].volume += comp.price
          }
        })

        // Build last six months keys and labels
        const monthEntries: Array<{ key: string; label: string }> = []
        const now = new Date()
        for (let i = 5; i >= 0; i--) {
          const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
          monthEntries.push({
            key: `${d.getFullYear()}-${d.getMonth()}`,
            label: d.toLocaleString('he-IL', { month: 'long' })
          })
        }

        const marketData = monthEntries.map(({ key, label }) => {
          const priceInfo = assetPriceByMonth[key]
          const compInfo = compByMonth[key]
          return {
            month: label,
            avgPrice: priceInfo ? Math.round(priceInfo.sum / priceInfo.count) : 0,
            transactions: compInfo?.count || 0,
            volume: compInfo?.volume || 0
          }
        })

        // Calculate market trend based on actual data
        let marketTrend: 'up' | 'down' | 'stable' = 'stable'
        if (marketData.length >= 2) {
          const firstMonth = marketData[0].avgPrice
          const lastMonth = marketData[marketData.length - 1].avgPrice
          const change = ((lastMonth - firstMonth) / firstMonth) * 100
          
          if (change > 2) marketTrend = 'up'
          else if (change < -2) marketTrend = 'down'
          else marketTrend = 'stable'
        }

        // Build recent activity from assets and alerts
        const recentActivity: Array<{
          id: string
          type: 'asset' | 'alert' | 'client' | 'transaction'
          title: string
          timestamp: string
          value?: number
        }> = []

        if (assetsRes.status === 'fulfilled' && assetsRes.value.ok) {
          const assets = assetsRes.value.data?.rows || []
          assets.forEach((a: any) => {
            if (a.created_at) {
              recentActivity.push({
                id: String(a.id),
                type: 'asset',
                title: `נכס חדש - ${a.address}`,
                timestamp: a.created_at,
                value: a.price
              })
            }
          })
        }

        if (isAuthenticated && alertsRes.status === 'fulfilled' && alertsRes.value?.ok) {
          const alerts = alertsRes.value.data?.alerts || []
          alerts.forEach((alert: any) => {
            recentActivity.push({
              id: String(alert.id || alert.ruleId || Math.random()),
              type: 'alert',
              title: alert.name || alert.title || 'התראה חדשה',
              timestamp: alert.created_at || new Date().toISOString()
            })
          })
        }

        recentActivity.sort(
          (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        )
        recentActivity.splice(4)

        const dashboardData: DashboardData = {
          totalassets,
          activeAlerts,
          totalReports,
          averageReturn,
          marketTrend,
          recentActivity,
          marketData,
          propertyTypes,
          topAreas
        }

        setData(dashboardData)
      } catch (err: any) {
        console.error('Failed to fetch dashboard data:', err)
        
        // Provide more specific error messages
        if (err.message?.includes('401') || err.message?.includes('Unauthorized')) {
          setError('Session expired. Please log in again.')
        } else if (err.message?.includes('Network') || err.message?.includes('fetch')) {
          setError('Network error. Please check your connection and try again.')
        } else if (err.message?.includes('403') || err.message?.includes('Forbidden')) {
          setError('Access denied. You may not have permission to view this data.')
        } else {
          setError('Failed to load dashboard data. Please try again.')
        }
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()

    // Set up polling for real-time updates (every 5 minutes)
    const interval = setInterval(fetchDashboardData, 5 * 60 * 1000)

    return () => clearInterval(interval)
  }, [isAuthenticated, authLoading])

  return { data, loading, error }
}
