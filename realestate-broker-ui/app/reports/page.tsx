'use client'

import React, { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableHeader, TableHead, TableRow, TableBody, TableCell } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { FileText, Download, Eye, Calendar, MapPin, Trash2 } from 'lucide-react'
import Link from 'next/link'

type Report = {
  id: number
  assetId: number
  address: string
  filename: string
  createdAt: string
  type?: string
  status?: string
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState<number | null>(null)

  useEffect(() => {
    fetch('/api/reports')
      .then(res => res.json())
      .then(data => {
        // Handle both array and object responses
        const reportsData = Array.isArray(data) ? data : (data.reports || [])
        setReports(reportsData)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load reports', err)
        setLoading(false)
        // Set empty array on error
        setReports([])
      })
  }, [])

  // Sample data for demonstration (remove this in production)
  const sampleReports: Report[] = [
    {
      id: 1,
      assetId: 1,
      address: 'רחוב הרצל 123, תל אביב',
      filename: 'report_1.pdf',
      createdAt: new Date().toISOString(),
      type: 'דוח שמאות',
      status: 'הושלם'
    },
    {
      id: 2,
      assetId: 2,
      address: 'רחוב דיזנגוף 45, תל אביב',
      filename: 'report_2.pdf',
      createdAt: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
      type: 'דוח תכנון',
      status: 'הושלם'
    }
  ]

  // Use sample data if no real data is available (for demo purposes)
  const displayReports = reports.length > 0 ? reports : sampleReports
  const isSampleData = reports.length === 0 && !loading

  const handleDeleteReport = async (reportId: number) => {
    if (!confirm('האם אתה בטוח שברצונך למחוק דוח זה?')) {
      return
    }

    setDeleting(reportId)
    try {
      const response = await fetch('/api/reports', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reportId })
      })

      if (response.ok) {
        // Remove the report from the local state
        setReports(prev => prev.filter(r => r.id !== reportId))
        // Show success message (you could add a toast notification here)
        alert('הדוח נמחק בהצלחה')
      } else {
        const error = await response.json()
        alert(`שגיאה במחיקת הדוח: ${error.error}`)
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
        
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              דוחות נכסים
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="w-full overflow-x-auto">
              <Table className="min-w-full">
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right whitespace-nowrap">נכס</TableHead>
                    <TableHead className="text-right whitespace-nowrap">סוג דוח</TableHead>
                    <TableHead className="text-right whitespace-nowrap">סטטוס</TableHead>
                    <TableHead className="text-right whitespace-nowrap">נוצר ב</TableHead>
                    <TableHead className="text-right whitespace-nowrap">פעולות</TableHead>
                  </TableRow>
                </TableHeader>
                    <TableBody>
                      {displayReports.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                            <div className="flex flex-col items-center gap-2">
                              <FileText className="h-8 w-8 opacity-50" />
                              <p>אין דוחות זמינים</p>
                              <p className="text-sm">דוחות יופיעו כאן לאחר שייווצרו</p>
                            </div>
                          </TableCell>
                        </TableRow>
                      ) : (
                        displayReports.map(report => (
                          <TableRow key={report.id} className="hover:bg-muted/50">
                            <TableCell>
                              <div>
                                <div className="font-semibold">
                                  <Link
                                    href={`/reports/${report.filename}`}
                                    target="_blank"
                                    className="hover:text-primary transition-colors"
                                  >
                                    {report.address}
                                  </Link>
                                </div>
                                <div className="text-xs text-muted-foreground flex items-center gap-1">
                                  <MapPin className="h-3 w-3" />
                                  <span>צפה בדוח</span>
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline">
                                {report.type || 'דוח כללי'}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant="good">
                                {report.status || 'הושלם'}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Calendar className="h-4 w-4 text-muted-foreground" />
                                <span className="text-sm">
                                  {new Date(report.createdAt).toLocaleDateString('he-IL', {
                                    year: 'numeric',
                                    month: 'short',
                                    day: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </span>
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="flex gap-2 justify-end">
                                <Button variant="ghost" size="sm" asChild>
                                  <Link href={`/reports/${report.filename}`} target="_blank">
                                    <Eye className="h-4 w-4 ml-2" />
                                    תצוגה
                                  </Link>
                                </Button>
                                <Button variant="outline" size="sm" asChild>
                                  <a href={`/reports/${report.filename}`} download>
                                    <Download className="h-4 w-4 ml-2" />
                                    הורדה
                                  </a>
                                </Button>
                                <Button 
                                  variant="destructive" 
                                  size="sm"
                                  onClick={() => handleDeleteReport(report.id)}
                                  disabled={deleting === report.id}
                                >
                                  <Trash2 className="h-4 w-4 ml-2" />
                                  {deleting === report.id ? 'מוחק...' : 'מחיקה'}
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>

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
