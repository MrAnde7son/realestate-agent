"use client";

import React from 'react';
import { Table } from '@tanstack/react-table';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';

interface TablePaginationProps<TData> {
  table: Table<TData>;
  pageSizeOptions?: number[];
  className?: string;
}

const DEFAULT_PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

export default function TablePagination<TData>({
  table,
  pageSizeOptions = DEFAULT_PAGE_SIZE_OPTIONS,
  className,
}: TablePaginationProps<TData>) {
  const pagination = table.getState().pagination;
  const pageCount = table.getPageCount();

  const normalizedPageSizeOptions = React.useMemo(() => {
    const sanitized = pageSizeOptions
      .map(size => Number(size))
      .filter(size => Number.isFinite(size) && size > 0);

    if (!sanitized.includes(pagination.pageSize)) {
      sanitized.push(pagination.pageSize);
    }

    return Array.from(new Set(sanitized)).sort((a, b) => a - b);
  }, [pageSizeOptions, pagination.pageSize]);

  if (pageCount <= 1 && normalizedPageSizeOptions.length <= 1) {
    return null;
  }

  return (
    <div className={cn("flex flex-col sm:flex-row items-center justify-between gap-3 py-3", className)}>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          הקודם
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          הבא
        </Button>
      </div>

      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>
          עמוד {pagination.pageIndex + 1} מתוך {pageCount || 1}
        </span>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">שורות בעמוד</span>
        <Select
          value={String(pagination.pageSize)}
          onValueChange={(value) => table.setPageSize(Number(value))}
        >
          <SelectTrigger className="w-[90px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {normalizedPageSizeOptions.map((size) => (
              <SelectItem key={size} value={String(size)}>
                {size}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
