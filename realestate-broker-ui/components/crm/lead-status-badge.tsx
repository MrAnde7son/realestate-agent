'use client';

import { Badge } from '@/components/ui/Badge';
import { LeadStatus } from '@/lib/api/crm';

interface LeadStatusBadgeProps {
  status: LeadStatus;
}

const statusConfig = {
  'new': { label: 'חדש', variant: 'default' as const, className: 'bg-blue-100 text-blue-800' },
  'contacted': { label: 'יצרתי קשר', variant: 'secondary' as const, className: 'bg-yellow-100 text-yellow-800' },
  'interested': { label: 'מתעניין', variant: 'secondary' as const, className: 'bg-orange-100 text-orange-800' },
  'negotiating': { label: 'במשא ומתן', variant: 'secondary' as const, className: 'bg-purple-100 text-purple-800' },
  'closed-won': { label: 'נסגר בהצלחה', variant: 'default' as const, className: 'bg-green-100 text-green-800' },
  'closed-lost': { label: 'נסגר ללא הצלחה', variant: 'destructive' as const, className: 'bg-red-100 text-red-800' },
};

export function LeadStatusBadge({ status }: LeadStatusBadgeProps) {
  const config = statusConfig[status];
  
  return (
    <Badge 
      variant={config.variant} 
      className={`${config.className} font-medium`}
    >
      {config.label}
    </Badge>
  );
}
