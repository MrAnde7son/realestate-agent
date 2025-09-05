'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/lib/auth-context'
import { authAPI } from '@/lib/auth'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  AreaChart,
  Area
} from 'recharts'
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table'

export default function AnalyticsPage() {
  const { user } = useAuth()
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    if (user?.role === 'admin') {
      const token = authAPI.getAccessToken()
      fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'}/api/analytics/`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
        .then(res => res.json())
        .then(setData)
        .catch(console.error)
    }
  }, [user])

  if (!user) return null
  if (user.role !== 'admin') return <div>Access denied</div>
  if (!data) return <div>Loading...</div>

  return (
    <div className="p-4 space-y-8">
      <LineChart width={600} height={300} data={data.daily}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="users" stroke="#8884d8" />
        <Line type="monotone" dataKey="assets" stroke="#82ca9d" />
        <Line type="monotone" dataKey="reports" stroke="#ffc658" />
        <Line type="monotone" dataKey="alerts" stroke="#ff8042" />
      </LineChart>

      <AreaChart width={600} height={200} data={data.daily}>
        <defs>
          <linearGradient id="colorErr" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#ff0000" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#ff0000" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <XAxis dataKey="date" />
        <YAxis />
        <CartesianGrid strokeDasharray="3 3" />
        <Tooltip />
        <Area type="monotone" dataKey="errors" stroke="#ff0000" fillOpacity={1} fill="url(#colorErr)" />
      </AreaChart>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Source</TableHead>
            <TableHead>Error Code</TableHead>
            <TableHead>Count</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.top_failures.map((row: any, idx: number) => (
            <TableRow key={idx}>
              <TableCell>{row.source}</TableCell>
              <TableCell>{row.error_code}</TableCell>
              <TableCell>{row.count}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
