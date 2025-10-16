"use client";

import React from 'react';
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getSortedRowModel,
  SortingState,
  getPaginationRowModel,
  PaginationState,
} from '@tanstack/react-table';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import TableToolbar, { AdditionalFilterValue, AdditionalFilterConfig } from '@/components/TableToolbar';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/button';
import { ArrowDown, ArrowUp, ArrowUpDown, ExternalLink } from 'lucide-react';
import { useAnalytics } from '@/hooks/useAnalytics';
import TablePagination from '@/components/TablePagination';

export interface RamiAppraisalRow {
  id: string;
  planNumber?: string;
  date?: string;
  value?: number | string;
  status?: string;
  source?: string;
  url?: string;
  fetchedAt?: string;
  searchValues?: string[];
}

interface RamiAppraisalsTableProps {
  data: RamiAppraisalRow[];
  loading?: boolean;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  filters?: {
    source?: {
      value: string;
      onChange: (value: string) => void;
    };
    status?: {
      value: string;
      onChange: (value: string) => void;
    };
  };
  onRefresh?: () => void;
}

const formatCurrency = (value?: number | string) => {
  if (value === null || value === undefined) return '—';
  const numeric = typeof value === 'string' ? Number(value) : value;
  if (Number.isNaN(numeric)) return value?.toString() ?? '—';
  return new Intl.NumberFormat('he-IL', {
    style: 'currency',
    currency: 'ILS',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(numeric);
};

const formatDate = (value?: string) => {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('he-IL');
};

const statusBadge = (status?: string) => {
  if (!status) return null;
  return <Badge variant="outline">{status}</Badge>;
};

const sourceBadge = (source?: string) => {
  if (!source) return null;
  const normalized = source.toLowerCase();
  if (normalized.includes('rami')) {
    return <Badge variant="secondary">רמ״י</Badge>;
  }
  if (normalized.includes('internal')) {
    return <Badge variant="outline">מאגר פנימי</Badge>;
  }
  return <Badge variant="neutral">{source}</Badge>;
};

function createColumns(): ColumnDef<RamiAppraisalRow>[] {
  return [
    {
      accessorKey: 'planNumber',
      header: 'תכנית',
      cell: ({ row }) => (
        <div className="text-sm font-medium text-right">
          {row.original.planNumber || 'תכנית רמ״י'}
        </div>
      ),
    },
    {
      accessorKey: 'date',
      header: 'תאריך',
      cell: ({ row }) => (
        <div className="text-sm text-muted-foreground text-right">
          {formatDate(row.original.date)}
        </div>
      ),
    },
    {
      accessorKey: 'value',
      header: 'שווי מוערך',
      cell: ({ row }) => (
        <div className="text-sm font-semibold text-right">
          {formatCurrency(row.original.value)}
        </div>
      ),
    },
    {
      accessorKey: 'status',
      header: 'סטטוס',
      cell: ({ row }) => (
        <div className="flex justify-end">
          {statusBadge(row.original.status)}
        </div>
      ),
    },
    {
      accessorKey: 'source',
      header: 'מקור',
      cell: ({ row }) => (
        <div className="flex justify-end">
          {sourceBadge(row.original.source)}
        </div>
      ),
    },
    {
      accessorKey: 'fetchedAt',
      header: 'עודכן',
      cell: ({ row }) => (
        <div className="text-sm text-muted-foreground text-right">
          {formatDate(row.original.fetchedAt)}
        </div>
      ),
    },
    {
      id: 'actions',
      header: 'פעולות',
      enableHiding: false,
      enableSorting: false,
      cell: ({ row }) => (
        <div className="flex justify-end">
          {row.original.url && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => window.open(row.original.url, '_blank')}
              className="text-xs"
            >
              <ExternalLink className="h-3 w-3 ml-1 inline-block" />
              פתיחה
            </Button>
          )}
        </div>
      ),
    },
  ];
}

export default function RamiAppraisalsTable({
  data,
  loading = false,
  searchValue = '',
  onSearchChange,
  filters,
  onRefresh,
}: RamiAppraisalsTableProps) {
  const { trackFeatureUsage } = useAnalytics();
  const [rowSelection, setRowSelection] = React.useState({});
  const [columnVisibility, setColumnVisibility] = React.useState<Record<string, boolean>>({});
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  });

  const columns = React.useMemo(() => createColumns(), []);

  const [planNumberFilter, setPlanNumberFilter] = React.useState('');
  const [valueRange, setValueRange] = React.useState<{ min?: number; max?: number }>({});
  const [dateRange, setDateRange] = React.useState<{ from?: string; to?: string }>({});

  const filteredData = React.useMemo(() => {
    return data.filter((row) => {
      if (searchValue) {
        const searchLower = searchValue.toLowerCase();
        const values = row.searchValues || [
          row.planNumber,
          row.status,
          row.source,
          row.date,
          row.value?.toString(),
        ];
        const matches = values.some((value) => value?.toLowerCase().includes(searchLower));
        if (!matches) return false;
      }

      if (filters?.source?.value && filters.source.value !== 'all') {
        if ((row.source || 'all') !== filters.source.value) return false;
      }

      if (filters?.status?.value && filters.status.value !== 'all') {
        if ((row.status || 'all') !== filters.status.value) return false;
      }

      if (planNumberFilter.trim()) {
        const search = planNumberFilter.trim().toLowerCase();
        if (!row.planNumber?.toLowerCase().includes(search)) return false;
      }

      if (valueRange.min !== undefined || valueRange.max !== undefined) {
        const numericValue = typeof row.value === 'string' ? Number(row.value) : row.value;
        if (numericValue === undefined || Number.isNaN(numericValue)) return false;
        if (valueRange.min !== undefined && numericValue < valueRange.min) return false;
        if (valueRange.max !== undefined && numericValue > valueRange.max) return false;
      }

      if (dateRange.from || dateRange.to) {
        const appraisalDate = row.date ? new Date(row.date) : undefined;
        if (!appraisalDate || Number.isNaN(appraisalDate.getTime())) return false;
        if (dateRange.from) {
          const fromDate = new Date(dateRange.from);
          if (appraisalDate < fromDate) return false;
        }
        if (dateRange.to) {
          const toDate = new Date(dateRange.to);
          toDate.setHours(23, 59, 59, 999);
          if (appraisalDate > toDate) return false;
        }
      }

      return true;
    });
  }, [
    data,
    searchValue,
    filters,
    planNumberFilter,
    valueRange.min,
    valueRange.max,
    dateRange.from,
    dateRange.to,
  ]);

  React.useEffect(() => {
    setPagination((prev) => ({ ...prev, pageIndex: 0 }));
  }, [filteredData.length]);

  const table = useReactTable({
    data: filteredData,
    columns,
    state: {
      rowSelection,
      columnVisibility,
      sorting,
      pagination,
    },
    enableRowSelection: true,
    onRowSelectionChange: setRowSelection,
    onColumnVisibilityChange: setColumnVisibility,
    onSortingChange: setSorting,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  const toolbarColumns = table.getAllColumns()
    .filter((column) => column.getCanHide())
    .map((column) => ({
      id: column.id,
      header: column.columnDef.header as string,
      visible: column.getIsVisible(),
      toggle: (value: boolean) => column.toggleVisibility(value),
    }));

  const additionalFilters = React.useMemo<AdditionalFilterConfig[]>(() => {
    const filtersList: AdditionalFilterConfig[] = [];

    const sources = Array.from(new Set(data.map((row) => row.source).filter(Boolean))) as string[];
    if (sources.length > 0) {
      filtersList.push({
        key: 'source',
        label: 'מקור',
        type: 'select',
        value: filters?.source?.value ?? 'all',
        options: [
          { value: 'all', label: 'כל המקורות' },
          ...sources.map((source) => ({ value: source, label: source })),
        ],
      });
    }

    const statuses = Array.from(new Set(data.map((row) => row.status).filter(Boolean))) as string[];
    if (statuses.length > 0 && filters?.status) {
      filtersList.push({
        key: 'status',
        label: 'סטטוס',
        type: 'select',
        value: filters.status.value ?? 'all',
        options: [
          { value: 'all', label: 'כל הסטטוסים' },
          ...statuses.map((status) => ({ value: status, label: status })),
        ],
      });
    }

    filtersList.push(
      {
        key: 'planNumber',
        label: 'מספר תוכנית',
        type: 'text',
        value: planNumberFilter,
        placeholder: 'לדוגמה 12345',
      },
      {
        key: 'date',
        label: 'תאריך',
        type: 'date-range',
        value: { from: dateRange.from, to: dateRange.to },
      },
      {
        key: 'value',
        label: 'שווי מוערך',
        type: 'number-range',
        value: { min: valueRange.min, max: valueRange.max },
        minPlaceholder: 'מינימום',
        maxPlaceholder: 'מקסימום',
      },
    );

    return filtersList;
  }, [
    data,
    filters?.source,
    filters?.source?.value,
    filters?.status,
    filters?.status?.value,
    planNumberFilter,
    dateRange.from,
    dateRange.to,
    valueRange.min,
    valueRange.max,
  ]);

  const handleAdditionalFilterChange = React.useCallback((key: string, value: AdditionalFilterValue) => {
    if (key === 'source' && typeof value === 'string' && filters?.source?.onChange) {
      filters.source.onChange(value);
      trackFeatureUsage('filter', undefined, { filter_type: 'rami_source', value });
      return;
    }
    if (key === 'status' && typeof value === 'string' && filters?.status?.onChange) {
      filters.status.onChange(value);
      trackFeatureUsage('filter', undefined, { filter_type: 'rami_status', value });
      return;
    }
    if (key === 'planNumber' && typeof value === 'string') {
      setPlanNumberFilter(value);
      trackFeatureUsage('filter', undefined, { filter_type: 'rami_plan_number', value });
      return;
    }
    if (key === 'date' && typeof value === 'object' && value !== null && !Array.isArray(value) && 'from' in value) {
      const nextValue = value as { from?: string; to?: string };
      setDateRange({ from: nextValue.from, to: nextValue.to });
      trackFeatureUsage('filter', undefined, { filter_type: 'rami_date', value });
      return;
    }
    if (key === 'value' && typeof value === 'object' && value !== null && !Array.isArray(value) && 'min' in value) {
      const nextValue = value as { min?: number; max?: number };
      setValueRange({ min: nextValue.min, max: nextValue.max });
      trackFeatureUsage('filter', undefined, { filter_type: 'rami_value', value });
    }
  }, [filters?.source, filters?.status, trackFeatureUsage]);

  if (loading) {
    return (
      <div className="rounded-xl border border-border bg-card">
        <div className="p-8 text-center text-muted-foreground">טוען שומות רמ״י...</div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card overflow-x-auto rtl" dir="rtl">
      <TableToolbar
        searchValue={searchValue}
        onSearchChange={(value) => {
          onSearchChange?.(value);
          if (value.trim()) {
            trackFeatureUsage('search', undefined, { query: value.trim(), context: 'rami_appraisals' });
          }
        }}
        searchPlaceholder="חיפוש בשומות רמ״י..."
        additionalFilters={additionalFilters}
        onAdditionalFilterChange={handleAdditionalFilterChange}
        columns={toolbarColumns}
        selectedCount={table.getSelectedRowModel().rows.length}
        totalCount={filteredData.length}
        onExportSelected={() => {}}
        onExportAll={() => {}}
        viewMode="table"
        onViewModeChange={() => {}}
        onRefresh={onRefresh || (() => {})}
        loading={loading}
      />

      <Table className="rtl">
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => {
                const sorted = header.column.getIsSorted();
                return (
                  <TableHead key={header.id} className="text-right rtl:text-right">
                    {header.isPlaceholder ? null : (
                      <button
                        type="button"
                        onClick={header.column.getToggleSortingHandler()}
                        disabled={!header.column.getCanSort()}
                        className="flex w-full items-center justify-end gap-1 text-xs font-medium rtl:flex-row-reverse disabled:cursor-default"
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {header.column.getCanSort() && (
                          <span className="text-muted-foreground">
                            {sorted === 'asc' ? (
                              <ArrowUp className="h-3 w-3" />
                            ) : sorted === 'desc' ? (
                              <ArrowDown className="h-3 w-3" />
                            ) : (
                              <ArrowUpDown className="h-3 w-3" />
                            )}
                          </span>
                        )}
                      </button>
                    )}
                  </TableHead>
                );
              })}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {filteredData.length === 0 ? (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center">
                <div className="text-muted-foreground py-8">לא נמצאו שומות רמ״י</div>
              </TableCell>
            </TableRow>
          ) : (
            table.getRowModel().rows.map((row) => (
              <TableRow key={row.id} className="hover:bg-muted/50">
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id} className="text-right rtl:text-right">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      <TablePagination table={table} />
    </div>
  );
}
