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
import TableToolbar from '@/components/TableToolbar';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/button';
import { ArrowDown, ArrowUp, ArrowUpDown, Download, ExternalLink } from 'lucide-react';
import { useAnalytics } from '@/hooks/useAnalytics';
import TablePagination from '@/components/TablePagination';

export interface DocumentRow {
  id: string;
  title: string;
  description?: string;
  category?: string;
  type?: string;
  status?: string;
  source?: string;
  documentDate?: string;
  uploadedAt?: string;
  uploadedBy?: string;
  fileUrl?: string;
  externalUrl?: string;
  isDownloadable?: boolean;
  externalId?: string;
  searchValues?: string[];
}

interface DocumentsTableProps {
  data: DocumentRow[];
  loading?: boolean;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  filters?: {
    category?: {
      value: string;
      onChange: (value: string) => void;
    };
    type?: {
      value: string;
      onChange: (value: string) => void;
    };
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
  totalCount?: number;
  paginationState?: PaginationState;
  onPaginationChange?: React.Dispatch<React.SetStateAction<PaginationState>>;
  sortingState?: SortingState;
  onSortingChange?: React.Dispatch<React.SetStateAction<SortingState>>;
  disableInternalFiltering?: boolean;
  availableFilters?: {
    category?: string[];
    type?: string[];
    source?: string[];
    status?: string[];
  };
}

const translateType = (type?: string) => {
  if (!type) return '—';
  const map: Record<string, string> = {
    tabu: 'נסח טאבו',
    condo_plan: 'תשריט בית משותף',
    appraisal_decisive: 'שומה מכרעת',
    appraisal_rmi: 'שומת רמ״י',
    appraisal: 'שומה',
    permit: 'היתר בנייה',
    rights: 'זכויות',
    plan: 'תכנית',
    other: 'אחר',
  };
  return map[type] || type;
};

const statusVariant = (status?: string) => {
  switch (status) {
    case 'approved':
      return 'success';
    case 'pending':
      return 'warning';
    case 'rejected':
      return 'error';
    case 'expired':
      return 'neutral';
    default:
      return 'outline';
  }
};

const statusLabel = (status?: string) => {
  const map: Record<string, string> = {
    approved: 'אושר',
    pending: 'ממתין',
    rejected: 'נדחה',
    expired: 'פג תוקף',
  };
  if (!status) return 'לא זמין';
  return map[status] || status;
};

const sourceLabel = (source?: string) => {
  if (!source) return '—';
  const translations: Record<string, string> = {
    user_upload: 'העלאה ידנית',
    gis: 'מערכת מידע גיאוגרפית',
    gis_permit: 'מערכת מידע גיאוגרפית',
    gis_rights: 'מערכת מידע גיאוגרפית',
    rami: 'רמ״י',
    rami_plan: 'רמ״י',
    mavat: 'מנהל התיכנון',
    gov: 'ממשלתי',
    tabu: 'טאבו',
    tabu_upload: 'טאבו',
    meta_migration: 'העברה מנתונים קיימים',
    yad2: 'יד2',
    nadlan: 'מידע נדלן',
    pipeline: 'צינור נתונים',
    external: 'מקור חיצוני',
  };
  return source && translations[source.toLowerCase()] || source;
};

const formatDate = (value?: string) => {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('he-IL');
};

function createColumns(): ColumnDef<DocumentRow>[] {
  return [
    {
      accessorKey: 'title',
      header: 'מסמך',
      cell: ({ row }) => (
        <div className="space-y-1 text-right">
          <div className="font-medium text-sm truncate">
            {row.original.title}
          </div>
          {row.original.description && (
            <div className="text-xs text-muted-foreground line-clamp-2">
              {row.original.description}
            </div>
          )}
          {row.original.externalId && (
            <div className="text-xs text-muted-foreground">
              מזהה: {row.original.externalId}
            </div>
          )}
        </div>
      ),
    },
    {
      accessorKey: 'category',
      header: 'קטגוריה',
      cell: ({ row }) => (
        <div className="text-sm text-right">
          {row.original.category || '—'}
        </div>
      ),
    },
    {
      accessorKey: 'type',
      header: 'סוג',
      cell: ({ row }) => (
        <div className="text-sm text-muted-foreground text-right">
          {translateType(row.original.type)}
        </div>
      ),
    },
    {
      accessorKey: 'status',
      header: 'סטטוס',
      cell: ({ row }) => (
        <div className="flex justify-end">
          <Badge variant={statusVariant(row.original.status) as any}>
            {statusLabel(row.original.status)}
          </Badge>
        </div>
      ),
    },
    {
      accessorKey: 'source',
      header: 'מקור',
      cell: ({ row }) => (
        <div className="flex justify-end">
          <Badge variant="outline">{sourceLabel(row.original.source)}</Badge>
        </div>
      ),
    },
    {
      accessorKey: 'documentDate',
      header: 'תאריך מסמך',
      cell: ({ row }) => (
        <div className="text-sm text-muted-foreground text-right">
          {formatDate(row.original.documentDate)}
        </div>
      ),
    },
    {
      accessorKey: 'uploadedAt',
      header: 'הועלה',
      cell: ({ row }) => (
        <div className="text-sm text-muted-foreground text-right">
          {formatDate(row.original.uploadedAt)}
        </div>
      ),
    },
    {
      accessorKey: 'uploadedBy',
      header: 'הועלה ע״י',
      cell: ({ row }) => (
        <div className="text-sm text-right">
          {row.original.uploadedBy || '—'}
        </div>
      ),
    },
    {
      id: 'actions',
      header: 'פעולות',
      enableHiding: false,
      enableSorting: false,
      cell: ({ row }) => (
        <div className="flex justify-end gap-2">
          {row.original.isDownloadable && row.original.fileUrl && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => window.open(row.original.fileUrl, '_blank')}
              className="text-xs"
            >
              <Download className="h-3 w-3 ml-1 inline-block" />
              הורדה
            </Button>
          )}
          {row.original.externalUrl && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => window.open(row.original.externalUrl, '_blank')}
              className="text-xs"
            >
              <ExternalLink className="h-3 w-3 ml-1 inline-block" />
              קישור
            </Button>
          )}
        </div>
      ),
    },
  ];
}

export default function DocumentsTable({
  data,
  loading = false,
  searchValue = '',
  onSearchChange,
  filters,
  onRefresh,
  totalCount,
  paginationState,
  onPaginationChange,
  sortingState,
  onSortingChange,
  disableInternalFiltering = false,
  availableFilters,
}: DocumentsTableProps) {
  const { trackFeatureUsage } = useAnalytics();
  const [rowSelection, setRowSelection] = React.useState({});
  const [columnVisibility, setColumnVisibility] = React.useState<Record<string, boolean>>({});
  const [internalSorting, setInternalSorting] = React.useState<SortingState>([]);
  const [internalPagination, setInternalPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  });

  const manualSorting = Boolean(sortingState && onSortingChange);
  const manualPagination = Boolean(paginationState && onPaginationChange);

  const sorting = manualSorting ? sortingState! : internalSorting;
  const setSorting = manualSorting ? onSortingChange! : setInternalSorting;

  const pagination = manualPagination ? paginationState! : internalPagination;
  const setPagination = manualPagination ? onPaginationChange! : setInternalPagination;

  const columns = React.useMemo(() => createColumns(), []);

  const filteredData = React.useMemo(() => {
    if (disableInternalFiltering) {
      return data;
    }

    return data.filter((row) => {
      if (searchValue) {
        const searchLower = searchValue.toLowerCase();
        const values = row.searchValues || [
          row.title,
          row.description,
          row.category,
          row.type,
          row.status,
          row.source,
          row.uploadedBy,
          row.externalId,
        ];
        const matches = values.some((value) => value?.toLowerCase().includes(searchLower));
        if (!matches) return false;
      }

      if (filters?.category?.value && filters.category.value !== 'all') {
        if ((row.category || 'all') !== filters.category.value) return false;
      }

      if (filters?.type?.value && filters.type.value !== 'all') {
        if ((row.type || 'all') !== filters.type.value) return false;
      }

      if (filters?.source?.value && filters.source.value !== 'all') {
        if ((row.source || 'all') !== filters.source.value) return false;
      }

      if (filters?.status?.value && filters.status.value !== 'all') {
        if ((row.status || 'all') !== filters.status.value) return false;
      }

      return true;
    });
  }, [data, searchValue, filters, disableInternalFiltering]);

  React.useEffect(() => {
    if (!manualPagination) {
      setPagination((prev) => ({ ...prev, pageIndex: 0 }));
    }
  }, [filteredData.length, manualPagination, setPagination]);

  const effectiveData = disableInternalFiltering ? data : filteredData;

  const table = useReactTable({
    data: effectiveData,
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
    ...(manualSorting ? {} : { getSortedRowModel: getSortedRowModel() }),
    ...(manualPagination
      ? {
          manualPagination: true,
          pageCount: Math.max(
            1,
            Math.ceil((totalCount ?? effectiveData.length) / pagination.pageSize)
          ),
        }
      : {
          getPaginationRowModel: getPaginationRowModel(),
        }),
  });

  const toolbarColumns = table.getAllColumns()
    .filter((column) => column.getCanHide())
    .map((column) => ({
      id: column.id,
      header: column.columnDef.header as string,
      visible: column.getIsVisible(),
      toggle: (value: boolean) => column.toggleVisibility(value),
    }));

  const additionalFilters = React.useMemo(() => {
    const filtersList: Array<{
      key: string;
      label: string;
      value: string;
      options: Array<{ value: string; label: string }>;
    }> = [];

    const categories =
      availableFilters?.category ??
      (Array.from(new Set(data.map((row) => row.category).filter(Boolean))) as string[]);
    if (categories.length > 0) {
      filtersList.push({
        key: 'category',
        label: 'קטגוריה',
        value: filters?.category?.value ?? 'all',
        options: [
          { value: 'all', label: 'כל הקטגוריות' },
          ...categories.map((category) => ({ value: category, label: category })),
        ],
      });
    }

    const types =
      availableFilters?.type ??
      (Array.from(new Set(data.map((row) => row.type).filter(Boolean))) as string[]);
    if (types.length > 0) {
      filtersList.push({
        key: 'type',
        label: 'סוג מסמך',
        value: filters?.type?.value ?? 'all',
        options: [
          { value: 'all', label: 'כל הסוגים' },
          ...types.map((type) => ({ value: type, label: translateType(type) })),
        ],
      });
    }

    const sources =
      availableFilters?.source ??
      (Array.from(new Set(data.map((row) => row.source).filter(Boolean))) as string[]);
    if (sources.length > 0) {
      filtersList.push({
        key: 'source',
        label: 'מקור',
        value: filters?.source?.value ?? 'all',
        options: [
          { value: 'all', label: 'כל המקורות' },
          ...sources.map((source) => ({ value: source, label: sourceLabel(source) })),
        ],
      });
    }

    const statuses =
      availableFilters?.status ??
      (Array.from(new Set(data.map((row) => row.status).filter(Boolean))) as string[]);
    if (statuses.length > 0) {
      filtersList.push({
        key: 'status',
        label: 'סטטוס',
        value: filters?.status?.value ?? 'all',
        options: [
          { value: 'all', label: 'כל הסטטוסים' },
          ...statuses.map((status) => ({ value: status, label: statusLabel(status) })),
        ],
      });
    }

    return filtersList;
  }, [
    data,
    filters,
    availableFilters?.category,
    availableFilters?.type,
    availableFilters?.source,
    availableFilters?.status,
  ]);

  const handleAdditionalFilterChange = (key: string, value: string) => {
    if (key === 'category' && filters?.category?.onChange) {
      filters.category.onChange(value);
    }
    if (key === 'type' && filters?.type?.onChange) {
      filters.type.onChange(value);
    }
    if (key === 'source' && filters?.source?.onChange) {
      filters.source.onChange(value);
    }
    if (key === 'status' && filters?.status?.onChange) {
      filters.status.onChange(value);
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-border bg-card">
        <div className="p-8 text-center text-muted-foreground">טוען מסמכים...</div>
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
            trackFeatureUsage('search', undefined, { query: value.trim(), context: 'documents' });
          }
        }}
        searchPlaceholder="חיפוש במסמכים..."
        filters={{
          city: { value: 'all', onChange: () => {}, options: [] },
          type: { value: 'all', onChange: () => {}, options: [] },
          priceMin: { value: undefined, onChange: () => {} },
          priceMax: { value: undefined, onChange: () => {} },
        }}
        additionalFilters={additionalFilters}
        onAdditionalFilterChange={handleAdditionalFilterChange}
        columns={toolbarColumns}
        selectedCount={table.getSelectedRowModel().rows.length}
        totalCount={totalCount ?? effectiveData.length}
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
                <div className="text-muted-foreground py-8">לא נמצאו מסמכים</div>
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
