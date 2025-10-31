import * as React from 'react';
import * as Tooltip from '@radix-ui/react-tooltip';
import { Database } from 'lucide-react';
import { Badge, type BadgeProps } from '@/components/ui/Badge';

interface DataBadgeProps {
  source?: string;
  fetchedAt?: string;
  url?: string;
  defaultOpen?: boolean;
  tone?: 'status' | 'type' | 'risk';
}

const toneToVariant: Record<NonNullable<DataBadgeProps['tone']>, BadgeProps['variant']> = {
  status: 'info',
  type: 'neutral',
  risk: 'warning',
};

export default function DataBadge({
  source,
  fetchedAt,
  url,
  defaultOpen = false,
  tone = 'type',
}: DataBadgeProps) {
  if (!source || !fetchedAt) return null;
  const date = new Date(fetchedAt).toISOString().split('T')[0];
  const badgeVariant = toneToVariant[tone];
  return (
    <Tooltip.Provider delayDuration={0}>
      <Tooltip.Root defaultOpen={defaultOpen}>
        <Tooltip.Trigger asChild>
          <Badge
            variant={badgeVariant}
            dir="rtl"
            className="gap-1 text-[10px] px-1 rtl:flex-row-reverse font-normal"
            data-testid="data-badge"
            data-semantic={tone}
          >
            <Database className="w-3 h-3" />
            <span className="hidden sm:inline">{source}</span>
            <span className="hidden sm:inline">{date}</span>
          </Badge>
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            sideOffset={4}
            dir="rtl"
            className="rounded bg-gray-900 text-white px-2 py-1 text-xs"
            data-testid="data-badge-tooltip"
          >
            מקור: {source} • עודכן: {date}
            {url && (
              <>
                {' '}• <a href={url} target="_blank" rel="noopener noreferrer">קישור</a>
              </>
            )}
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}
