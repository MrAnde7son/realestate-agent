import * as React from 'react';
import * as Tooltip from '@radix-ui/react-tooltip';
import { Database } from 'lucide-react';

interface DataBadgeProps {
  source?: string;
  fetchedAt?: string;
  defaultOpen?: boolean;
}

export default function DataBadge({ source, fetchedAt, defaultOpen = false }: DataBadgeProps) {
  if (!source || !fetchedAt) return null;
  const date = new Date(fetchedAt).toISOString().split('T')[0];
  return (
    <Tooltip.Provider delayDuration={0}>
      <Tooltip.Root defaultOpen={defaultOpen}>
        <Tooltip.Trigger asChild>
          <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground border rounded px-1" data-testid="data-badge">
            <Database className="w-3 h-3" />
            <span>{source}</span>
            <span>{date}</span>
          </span>
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content sideOffset={4} className="rounded bg-gray-900 text-white px-2 py-1 text-xs" data-testid="data-badge-tooltip">
            מקור: {source} • עודכן: {date}
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}
