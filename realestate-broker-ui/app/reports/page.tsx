'use client'

import React, { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { Table, TableHeader, TableHead, TableRow, TableBody, TableCell } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

type Report = {
  id: string
  listingId: string
  address: string
  filename: string
  createdAt: string
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([])

  useEffect(() => {
    fetch('/api/reports')
      .then(res => res.json())
      .then(data => setReports(data.reports))
      .catch(err => console.error('Failed to load reports', err))
  }, [])

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold">דוחות</h1>
          <p className="text-muted-foreground">דוחות שנוצרו עבור נכסים</p>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-right">נכס</TableHead>
              <TableHead className="text-right">נוצר ב</TableHead>
              <TableHead className="text-right">פעולות</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {reports.map(report => (
              <TableRow key={report.id}>
                <TableCell className="text-right">{report.address}</TableCell>
                <TableCell className="text-right">{new Date(report.createdAt).toLocaleString('he-IL')}</TableCell>
                <TableCell className="flex gap-2 justify-end">
                  <Button variant="secondary" asChild>
                    <Link href={`/reports/${report.filename}`} target="_blank">תצוגה</Link>
                  </Button>
                  <Button variant="secondary" asChild>
                    <a href={`/reports/${report.filename}`} download>
                      הורדה
                    </a>
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </DashboardLayout>
  )
}
