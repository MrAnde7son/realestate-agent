import { useState, useEffect } from 'react'

export interface DashboardData {
  totalListings: number
  activeAlerts: number
  totalClients: number
  monthlyRevenue: number
  marketTrend: 'up' | 'down' | 'stable'
  recentActivity: Array<{
    id: string
    type: 'listing' | 'alert' | 'client' | 'transaction'
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
    listings: number
    avgPrice: number
    trend: number
  }>
}

export function useDashboardData() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch data from multiple API endpoints
        const [listingsRes, alertsRes, reportsRes] = await Promise.allSettled([
          fetch('/api/listings'),
          fetch('/api/alerts'),
          fetch('/api/reports')
        ])

        // Process listings data
        let totalListings = 0
        let propertyTypes: Array<{ type: string; count: number; percentage: number }> = []
        let topAreas: Array<{ area: string; listings: number; avgPrice: number; trend: number }> = []

        if (listingsRes.status === 'fulfilled' && listingsRes.value.ok) {
          const listingsData = await listingsRes.value.json()
          const listings = listingsData.rows || []
          totalListings = listings.length

          // Analyze property types
          const typeCounts: Record<string, number> = {}
          const areaData: Record<string, { count: number; totalPrice: number }> = {}

          listings.forEach((listing: any) => {
            // Count property types
            const type = listing.property_type || 'לא ידוע'
            typeCounts[type] = (typeCounts[type] || 0) + 1

            // Analyze areas
            const area = listing.city || 'לא ידוע'
            if (!areaData[area]) {
              areaData[area] = { count: 0, totalPrice: 0 }
            }
            areaData[area].count++
            areaData[area].totalPrice += listing.price || 0
          })

          // Convert to arrays
          propertyTypes = Object.entries(typeCounts).map(([type, count]) => ({
            type,
            count,
            percentage: Math.round((count / totalListings) * 100)
          }))

          topAreas = Object.entries(areaData)
            .map(([area, data]) => ({
              area,
              listings: data.count,
              avgPrice: Math.round(data.totalPrice / data.count),
              trend: Math.floor(Math.random() * 10) - 2 // Mock trend data
            }))
            .sort((a, b) => b.listings - a.listings)
            .slice(0, 4)
        }

        // Process alerts data
        let activeAlerts = 0
        if (alertsRes.status === 'fulfilled' && alertsRes.value.ok) {
          const alertsData = await alertsRes.value.json()
          const alerts = alertsData.rows || []
          activeAlerts = alerts.filter((alert: any) => alert.active).length
        }

        // Generate mock market data (replace with real API data)
        const months = ['ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני']
        const marketData = months.map((month, index) => ({
          month,
          avgPrice: 2800000 + (index * 50000) + Math.floor(Math.random() * 100000),
          transactions: 45 + Math.floor(Math.random() * 20),
          volume: (2800000 + (index * 50000)) * (45 + Math.floor(Math.random() * 20))
        }))

        // Generate recent activity (replace with real API data)
        const recentActivity = [
          {
            id: '1',
            type: 'listing' as const,
            title: 'דירה חדשה נוספה - רחוב דיזנגוף 123',
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            value: 2800000
          },
          {
            id: '2',
            type: 'alert' as const,
            title: 'התראה חדשה - דירות 4 חדרים בתל אביב',
            timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString()
          },
          {
            id: '3',
            type: 'client' as const,
            title: 'לקוח חדש נרשם - משפחת כהן',
            timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString()
          },
          {
            id: '4',
            type: 'transaction' as const,
            title: 'עסקה הושלמה - רחוב הרצל 45',
            timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            value: 3200000
          }
        ]

        const dashboardData: DashboardData = {
          totalListings,
          activeAlerts,
          totalClients: Math.floor(Math.random() * 30) + 15, // Mock data
          monthlyRevenue: Math.floor(Math.random() * 200000) + 100000, // Mock data
          marketTrend: 'up',
          recentActivity,
          marketData,
          propertyTypes,
          topAreas
        }

        setData(dashboardData)
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err)
        setError('Failed to load dashboard data')
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()

    // Set up polling for real-time updates (every 5 minutes)
    const interval = setInterval(fetchDashboardData, 5 * 60 * 1000)

    return () => clearInterval(interval)
  }, [])

  return { data, loading, error }
}
