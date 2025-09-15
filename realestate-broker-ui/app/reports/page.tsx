'use client'

import React, { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/Badge'
import { FileText, Download, Eye, Calendar, MapPin, Trash2, ExternalLink, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { apiClient } from '@/lib/api-client'

type Report = {
  id: number
  assetId: number
  address: string
  filename: string
  createdAt: string
  type?: string
  status?: string
  url: string
}

// Status mapping function
const getStatusHebrew = (status: string): string => {
  const statusMap: Record<string, string> = {
    'generating': 'מתבצע',
    'completed': 'הושלם',
    'failed': 'נכשל',
  }
  return statusMap[status] || status
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState<number | null>(null)
  const [clickedRow, setClickedRow] = useState<number | null>(null)

  useEffect(() => {
    apiClient.get('/api/reports')
      .then(res => {
        if (res.ok) {
          // Handle both array and object responses
          const reportsData = Array.isArray(res.data) ? res.data : (res.data.reports || [])
          setReports(reportsData)
        } else {
          console.error('Failed to load reports:', res.error)
          setReports([])
        }
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load reports', err)
        setLoading(false)
        // Set empty array on error
        setReports([])
      })
  }, [])

  // Use only real data from API
  const displayReports = reports
  const isSampleData = false

  const handleRowClick = (report: Report) => {
    setClickedRow(report.id)
    // Open the report in a new tab
    window.open(report.url, '_blank')
    // Reset the clicked state after a short delay
    setTimeout(() => setClickedRow(null), 300)
  }

  const handleDeleteReport = async (reportId: number) => {
    if (!confirm('האם אתה בטוח שברצונך למחוק דוח זה?')) {
      return
    }

    setDeleting(reportId)
    try {
      const response = await apiClient.request('/api/reports', {
        method: 'DELETE',
        body: JSON.stringify({ reportId })
      })

      if (response.ok) {
        // Remove the report from the local state
        setReports(prev => prev.filter(r => r.id !== reportId))
        // Show success message (you could add a toast notification here)
        alert('הדוח נמחק בהצלחה')
      } else {
        alert(`שגיאה במחיקת הדוח: ${response.error}`)
      }
    } catch (error) {
      console.error('Error deleting report:', error)
      alert('שגיאה במחיקת הדוח')
    } finally {
      setDeleting(null)
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <DashboardShell>
          <DashboardHeader 
            heading="דוחות" 
            text="דוחות שנוצרו עבור נכסים" 
          />
          <div className="flex items-center justify-center py-12">
            <p className="text-muted-foreground">טוען דוחות...</p>
          </div>
        </DashboardShell>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader 
          heading="דוחות" 
          text={`${reports.length} דוחות שנוצרו עבור נכסים`}
        />
        
        <div className="space-y-4">
          {displayReports.length === 0 ? (
            <Card>
              <CardBody className="flex flex-col items-center gap-2 py-8 text-muted-foreground">
                <FileText className="h-8 w-8 opacity-50" />
                <p>אין דוחות זמינים</p>
                <p className="text-sm">דוחות יופיעו כאן לאחר שייווצרו</p>
              </CardBody>
            </Card>
          ) : (
            displayReports.map(report => (
              <Card
                key={report.id}
                className={`cursor-pointer border-l-4 transition-colors ${
                  clickedRow === report.id
                    ? 'border-l-primary bg-blue-50'
                    : 'border-l-transparent hover:border-l-primary'
                }`}
                onClick={() => handleRowClick(report)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    handleRowClick(report)
                  }
                }}
                tabIndex={0}
                role="button"
                aria-label={`צפה בדוח עבור ${report.address}`}
              >
                <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div>
                    <div className="font-semibold flex items-center gap-2">
                      {report.address}
                    </div>
                    <div className="text-xs text-muted-foreground flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      <span>
                        {clickedRow === report.id ? 'פותח דוח...' : 'לחץ לצפייה בדוח'}
                      </span>
                      {clickedRow === report.id ? (
                        <Loader2 className="h-3 w-3 animate-spin text-primary" />
                      ) : (
                        <ExternalLink className="h-3 w-3 opacity-60" />
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="accent">{report.type || 'דוח כללי'}</Badge>
                    <Badge variant="success">
                      {report.status ? getStatusHebrew(report.status) : 'הושלם'}
                    </Badge>
                  </div>
                </CardHeader>
                <CardBody className="flex flex-col gap-4">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>
                      {new Date(report.createdAt).toLocaleDateString('he-IL', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2 justify-end" onClick={(e) => e.stopPropagation()}>
                    <Button variant="ghost" size="sm" asChild>
                      <Link href={report.url} target="_blank">
                        <Eye className="h-4 w-4" />
                        <span className="hidden sm:inline ml-2">תצוגה</span>
                      </Link>
                    </Button>
                    <Button variant="outline" size="sm" asChild>
                      <a href={report.url} download>
                        <Download className="h-4 w-4" />
                        <span className="hidden sm:inline ml-2">הורדה</span>
                      </a>
                    </Button>
                    {/* Debug: Delete button should be visible */}
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => {
                        console.log('Delete button clicked for report:', report.id);
                        handleDeleteReport(report.id);
                      }}
                      disabled={deleting === report.id}
                      className="min-w-fit bg-red-600 hover:bg-red-700 text-white border-red-600"
                      style={{ minWidth: '80px', height: '32px' }}
                    >
                      <Trash2 className="h-4 w-4" />
                      <span className="ml-2">
                        {deleting === report.id ? 'מוחק...' : 'מחיקה'}
                      </span>
                    </Button>
                  </div>
                </CardBody>
              </Card>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between mt-6">
          <p className="text-sm text-muted-foreground">
            מציג {displayReports.length} דוחות עם נתונים מלאים
          </p>
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}
