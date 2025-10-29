"use client";

import * as React from "react";

import { TableCell, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface TableSkeletonRowsProps {
  columnCount: number;
  rowCount?: number;
  cellClassName?: string;
  className?: string;
}

const WIDTH_CLASSES = ["w-3/4", "w-2/3", "w-1/2"] as const;

export function TableSkeletonRows({
  columnCount,
  rowCount = 3,
  cellClassName,
  className,
}: TableSkeletonRowsProps) {
  const rows = React.useMemo(() => Array.from({ length: Math.max(1, rowCount) }), [rowCount]);
  const cells = React.useMemo(() => Array.from({ length: Math.max(1, columnCount) }), [columnCount]);

  return (
    <>
      {rows.map((_, rowIndex) => (
        <TableRow
          key={`table-skeleton-${rowIndex}`}
          className={cn("animate-pulse", className)}
          aria-hidden="true"
          data-testid="table-skeleton-row"
        >
          {cells.map((_, cellIndex) => (
            <TableCell key={cellIndex} className={cn("py-4", cellClassName)}>
              <Skeleton
                className={cn(
                  "h-4 max-w-[200px]",
                  WIDTH_CLASSES[(rowIndex + cellIndex) % WIDTH_CLASSES.length]
                )}
              />
            </TableCell>
          ))}
        </TableRow>
      ))}
    </>
  );
}
