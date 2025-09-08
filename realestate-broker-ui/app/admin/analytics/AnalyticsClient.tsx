"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  AreaChart,
  Area,
} from "recharts";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";

interface Props {
  daily: any[];
  topFailures: any[];
}

export default function AnalyticsClient({ daily, topFailures }: Props) {
  // Add safety checks for data
  if (!daily || !Array.isArray(daily)) {
    return <div className="p-4">No analytics data available</div>;
  }
  
  if (!topFailures || !Array.isArray(topFailures)) {
    return <div className="p-4">No failure data available</div>;
  }

  return (
    <div className="p-4 space-y-8">
      <LineChart width={600} height={300} data={daily}>
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

      <AreaChart width={600} height={200} data={daily}>
        <defs>
          <linearGradient id="colorErr" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#ff0000" stopOpacity={0.8} />
            <stop offset="95%" stopColor="#ff0000" stopOpacity={0} />
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
          {topFailures.map((row: any, idx: number) => (
            <TableRow key={idx}>
              <TableCell>{row.source}</TableCell>
              <TableCell>{row.error_code}</TableCell>
              <TableCell>{row.count}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
