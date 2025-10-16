"use client";

import React from 'react';
import * as Tooltip from '@radix-ui/react-tooltip';
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getSortedRowModel,
  SortingState,
  getPaginationRowModel,
  PaginationState,
  Updater,
} from '@tanstack/react-table';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/button';
import TableToolbar, { AdditionalFilterConfig, AdditionalFilterValue } from '@/components/TableToolbar';
import TablePagination from '@/components/TablePagination';
import { useAnalytics } from '@/hooks/useAnalytics';
import { ArrowDown, ArrowUp, ArrowUpDown, Building, ExternalLink, FileDown } from 'lucide-react';

export interface PermitRow {
  id: string;
  title?: string;
  description?: string;
  permitNumber?: string;
  requestNumber?: string;
  addresses?: string;
  stage?: string;
  documentType?: string;
  requestType?: string;
  source?: string;
  approvalDate?: string | null;
  issueDate?: string | null;
  expiryDate?: string | null;
  handasaLink?: string;
  externalUrl?: string;
  searchValues?: string[];
  raw?: any;
}

interface PermitsTableProps {
  data: PermitRow[];
  loading?: boolean;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  filters?: {
    stage?: {
      value: string;
      onChange: (value: string) => void;
      options: Array<{ value: string; label: string }>;
    };
    documentType?: {
      value: string;
      onChange: (value: string) => void;
      options: Array<{ value: string; label: string }>;
    };
    source?: {
      value: string;
      onChange: (value: string) => void;
      options: Array<{ value: string; label: string }>;
    };
  };
  onRefresh?: () => void;
  radius?: number;
  manualPagination?: boolean;
  manualSorting?: boolean;
  pageCount?: number;
  paginationState?: PaginationState;
  onPaginationChange?: (value: PaginationState) => void;
  sortingState?: SortingState;
  onSortingChange?: (value: SortingState) => void;
  totalCount?: number;
  filterOptions?: {
    stage?: string[];
    documentType?: string[];
    source?: string[];
    requestType?: string[];
  };
  advancedFilters?: {
    permitNumber?: { value: string; onChange: (value: string) => void };
    requestNumber?: { value: string; onChange: (value: string) => void };
    requestType?: { value: string; onChange: (value: string) => void };
    description?: { value: string; onChange: (value: string) => void };
    approvalDate?: { from?: string; to?: string; onChange: (value: { from?: string; to?: string }) => void };
    expiryDate?: { from?: string; to?: string; onChange: (value: { from?: string; to?: string }) => void };
  };
}

const stageVariant = (stage?: string) => {
  if (!stage) return 'neutral';
  const normalized = stage.toLowerCase();
  if (normalized.includes('בניה') || normalized.includes('בנייה')) return 'success';
  if (normalized.includes('הריסה')) return 'warning';
  if (normalized.includes('אישור')) return 'secondary';
  return 'neutral';
};

const documentTypeDisplay = (type?: string) => {
  if (!type) return '—';
  const translations: Record<string, string> = {
    permit: 'היתר בנייה',
    'טופס 4': 'טופס 4',
    'היתר בתנאים': 'היתר בתנאים',
    demolition: 'הריסה',
    construction: 'בנייה',
  };
  const normalized = type.toLowerCase();
  return translations[type] || translations[normalized] || type;
};

const sourceDisplay = (source?: string) => {
  if (!source) return '—';
  const translations: Record<string, string> = {
    gis: 'עירייה',
    user_upload: 'העלאה ידנית',
    handasa: 'תיק בניין',
  };
  return source && translations[source.toLowerCase()] || source;
};

const sourceVariant = (source?: string) => {
  if (!source) return 'neutral';
  if (source === 'gis_permit') return 'secondary';
  if (source === 'user_upload') return 'outline';
  return 'neutral';
};

const RequestTypeCell = ({ value }: { value?: string }) => {
  if (!value) {
    return <span className="text-muted-foreground text-sm">—</span>;
  }

  const preview = value.replace(/\s+/g, ' ').trim();

  return (
    <Tooltip.Provider delayDuration={0}>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>
          <div
            tabIndex={0}
            dir="rtl"
            className="max-w-[220px] cursor-help overflow-hidden rounded-md border border-border/40 bg-muted/40 px-2 py-0.5 text-xs font-medium leading-4 text-right text-foreground outline-none transition focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background max-h-10"
          >
            <span className="block truncate">{preview}</span>
          </div>
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            side="bottom"
            align="end"
            sideOffset={4}
            dir="rtl"
            className="max-w-[360px] whitespace-pre-wrap rounded bg-gray-900 px-3 py-2 text-xs leading-5 text-white shadow-md"
          >
            {value}
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
};

const DescriptionCell = ({ value }: { value?: string }) => {
  if (!value) {
    return <span className="text-muted-foreground text-sm">—</span>;
  }

  const preview = value.replace(/\s+/g, ' ').trim();

  return (
    <Tooltip.Provider delayDuration={0}>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>
          <div
            tabIndex={0}
            dir="rtl"
            className="max-w-[400px] cursor-help overflow-hidden rounded-lg bg-muted/30 px-3 py-1 text-sm text-right leading-[1.35rem] text-muted-foreground outline-none transition focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background max-h-16"
          >
            <span className="block leading-[1.35rem] line-clamp-2">{preview}</span>
          </div>
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            side="bottom"
            align="end"
            sideOffset={4}
            dir="rtl"
            className="max-w-[420px] whitespace-pre-wrap rounded bg-gray-900 px-3 py-2 text-sm leading-6 text-white shadow-md"
          >
            {value}
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
};

function createColumns(): ColumnDef<PermitRow>[] {
  return [
    {
      accessorKey: 'title',
      header: 'בקשה',
      cell: ({ row }) => {
        const permit = row.original;
        return (
          <div className="space-y-1 text-right">
            <div className="font-medium text-sm">
              {permit.title || permit.description || 'היתר בנייה'}
            </div>
            {permit.addresses && (
              <div className="text-xs text-muted-foreground">
                {permit.addresses}
              </div>
            )}
          </div>
        );
      },
    },
    {
      accessorKey: 'permitNumber',
      header: 'מספר היתר',
      cell: ({ row }) => (
        <div className="text-sm font-medium text-right">
          {row.original.permitNumber || '—'}
        </div>
      ),
    },
    {
      accessorKey: 'requestNumber',
      header: 'מספר בקשה',
      cell: ({ row }) => (
        <div className="text-sm text-right">
          {row.original.requestNumber || '—'}
        </div>
      ),
    },
    {
      accessorKey: 'stage',
      header: 'שלב',
      cell: ({ row }) => {
        const stage = row.original.stage;
        return stage ? (
          <Badge variant={stageVariant(stage) as any}>
            {stage}
          </Badge>
        ) : (
          <span className="text-muted-foreground text-sm">—</span>
        );
      },
    },
    {
      accessorKey: 'requestType',
      header: 'סוג בקשה',
      cell: ({ row }) => (
        <RequestTypeCell value={row.original.requestType} />
      ),
    },
    {
      accessorKey: 'description',
      header: 'תוכן הבקשה',
      cell: ({ row }) => (
        <DescriptionCell value={row.original.description} />
      ),
    },
    {
      accessorKey: 'source',
      header: 'מקור',
      cell: ({ row }) => {
        const source = row.original.source;
        if (!source) {
          return <span className="text-muted-foreground text-sm">—</span>;
        }
        const display = sourceDisplay(source);
        const variant = sourceVariant(source);
        return (
          <Badge variant={variant as any}>
            {display}
          </Badge>
        );
      },
    },
    {
      accessorKey: 'documentType',
      header: 'סוג מסמך',
      cell: ({ row }) => (
        <div className="text-sm text-muted-foreground text-right">
          {documentTypeDisplay(row.original.documentType)}
        </div>
      ),
    },
    {
      accessorKey: 'approvalDate',
      header: 'תאריך אישור',
      cell: ({ row }) => (
        <div className="text-sm text-right">
          {row.original.approvalDate || row.original.issueDate || '—'}
        </div>
      ),
    },
    {
      accessorKey: 'expiryDate',
      header: 'תוקף',
      cell: ({ row }) => (
        <div className="text-sm text-right">
          {row.original.expiryDate || '—'}
        </div>
      ),
    },
    {
      id: 'actions',
      header: 'פעולות',
      enableHiding: false,
      enableSorting: false,
      cell: ({ row }) => {
        const permit = row.original;
        return (
          <div className="flex justify-end gap-2">
            {permit.handasaLink && (
              <Button
                variant="outline"
                size="sm"
                asChild
                className="text-xs"
              >
                <a
                  href={permit.handasaLink}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="h-3 w-3 ml-1 inline-block" />
                  אתר העירייה
                </a>
              </Button>
            )}
            {permit.externalUrl && (
              <Button
                size="sm"
                variant="secondary"
                onClick={() => window.open(permit.externalUrl as string, '_blank')}
                className="text-xs"
              >
                <FileDown className="h-3 w-3 ml-1 inline-block" />
                הורדה
              </Button>
            )}
          </div>
        );
      },
    },
  ];
}

export default function PermitsTable({
  data,
  loading = false,
  searchValue = '',
  onSearchChange,
  filters,
  onRefresh,
  radius,
  manualPagination = false,
  manualSorting = false,
  pageCount,
  paginationState,
  onPaginationChange,
  sortingState,
  onSortingChange,
  totalCount,
  filterOptions,
  advancedFilters,
}: PermitsTableProps) {
  const { trackFeatureUsage } = useAnalytics();
  const [rowSelection, setRowSelection] = React.useState({});
  const [columnVisibility, setColumnVisibility] = React.useState<Record<string, boolean>>({});
  const [internalSorting, setInternalSorting] = React.useState<SortingState>(sortingState ?? []);
  const [internalPagination, setInternalPagination] = React.useState<PaginationState>(
    paginationState ?? { pageIndex: 0, pageSize: 10 }
  );

  React.useEffect(() => {
    if (sortingState) {
      setInternalSorting(sortingState);
    }
  }, [sortingState]);

  React.useEffect(() => {
    if (paginationState) {
      setInternalPagination(paginationState);
    }
  }, [paginationState]);

  const columns = React.useMemo(() => createColumns(), []);

  const useClientFiltering = !(manualPagination || manualSorting);

  const permitNumberFilterValue = advancedFilters?.permitNumber?.value ?? '';
  const requestNumberFilterValue = advancedFilters?.requestNumber?.value ?? '';
  const requestTypeFilterValue = advancedFilters?.requestType?.value ?? 'all';
  const descriptionFilterValue = advancedFilters?.description?.value ?? '';
  const approvalDateFrom = advancedFilters?.approvalDate?.from ?? '';
  const approvalDateTo = advancedFilters?.approvalDate?.to ?? '';
  const expiryDateFrom = advancedFilters?.expiryDate?.from ?? '';
  const expiryDateTo = advancedFilters?.expiryDate?.to ?? '';

  const filteredData = React.useMemo(() => {
    if (!useClientFiltering) {
      return data;
    }

    let filtered = data;

    if (searchValue) {
      const searchLower = searchValue.toLowerCase();
      filtered = filtered.filter((permit) => {
        const values = permit.searchValues || [
          permit.title,
          permit.description,
          permit.addresses,
          permit.permitNumber,
          permit.requestNumber,
          permit.stage,
          permit.documentType,
        ];
        return values.some((value) => {
          if (!value) return false;
          return value.toLowerCase().includes(searchLower);
        });
      });
    }

    if (filters?.stage?.value && filters.stage.value !== 'all') {
      filtered = filtered.filter((permit) => permit.stage === filters.stage?.value);
    }

    if (filters?.documentType?.value && filters.documentType.value !== 'all') {
      filtered = filtered.filter((permit) => permit.documentType === filters.documentType?.value);
    }

    if (filters?.source?.value && filters.source.value !== 'all') {
      filtered = filtered.filter((permit) => permit.source === filters.source?.value);
    }

    if (advancedFilters?.permitNumber?.value) {
      const search = advancedFilters.permitNumber.value.trim().toLowerCase();
      if (search) {
        filtered = filtered.filter((permit) => {
          const permitNumber = permit.permitNumber?.toLowerCase() ?? '';
          return permitNumber.includes(search);
        });
      }
    }

    if (advancedFilters?.requestNumber?.value) {
      const search = advancedFilters.requestNumber.value.trim().toLowerCase();
      if (search) {
        filtered = filtered.filter((permit) => {
          const requestNumber = permit.requestNumber?.toLowerCase() ?? '';
          return requestNumber.includes(search);
        });
      }
    }

    if (advancedFilters?.requestType?.value && advancedFilters.requestType.value !== 'all') {
      filtered = filtered.filter((permit) => permit.requestType === advancedFilters.requestType?.value);
    }

    if (advancedFilters?.description?.value) {
      const search = advancedFilters.description.value.trim().toLowerCase();
      if (search) {
        filtered = filtered.filter((permit) => {
          const description = permit.description?.toLowerCase() ?? '';
          const title = permit.title?.toLowerCase() ?? '';
          return description.includes(search) || title.includes(search);
        });
      }
    }

    if (advancedFilters?.approvalDate) {
      const from = advancedFilters.approvalDate.from ? new Date(advancedFilters.approvalDate.from) : undefined;
      const to = advancedFilters.approvalDate.to ? new Date(advancedFilters.approvalDate.to) : undefined;
      if (from || to) {
        filtered = filtered.filter((permit) => {
          const dateString = permit.approvalDate || permit.issueDate;
          if (!dateString) return false;
          const approvalDate = new Date(dateString);
          if (Number.isNaN(approvalDate.getTime())) return false;
          if (from && approvalDate < from) return false;
          if (to) {
            const toDate = new Date(to);
            toDate.setHours(23, 59, 59, 999);
            if (approvalDate > toDate) return false;
          }
          return true;
        });
      }
    }

    if (advancedFilters?.expiryDate) {
      const from = advancedFilters.expiryDate.from ? new Date(advancedFilters.expiryDate.from) : undefined;
      const to = advancedFilters.expiryDate.to ? new Date(advancedFilters.expiryDate.to) : undefined;
      if (from || to) {
        filtered = filtered.filter((permit) => {
          const dateString = permit.expiryDate;
          if (!dateString) return false;
          const expiryDate = new Date(dateString);
          if (Number.isNaN(expiryDate.getTime())) return false;
          if (from && expiryDate < from) return false;
          if (to) {
            const toDate = new Date(to);
            toDate.setHours(23, 59, 59, 999);
            if (expiryDate > toDate) return false;
          }
          return true;
        });
      }
    }

    return filtered;
  }, [advancedFilters, data, filters, searchValue, useClientFiltering]);

  const tableData = useClientFiltering ? filteredData : data;

  const resolvedSorting = sortingState ?? internalSorting;
  const resolvedPagination = paginationState ?? internalPagination;

  const handleSortingChange = (updater: Updater<SortingState>) => {
    const next = typeof updater === 'function' ? updater(resolvedSorting) : updater;
    if (onSortingChange) {
      onSortingChange(next);
    } else {
      setInternalSorting(next);
    }
  };

  const handlePaginationChange = (updater: Updater<PaginationState>) => {
    const next = typeof updater === 'function' ? updater(resolvedPagination) : updater;
    if (onPaginationChange) {
      onPaginationChange(next);
    } else {
      setInternalPagination(next);
    }
  };

  const table = useReactTable({
    data: tableData,
    columns,
    state: {
      rowSelection,
      columnVisibility,
      sorting: resolvedSorting,
      pagination: resolvedPagination,
    },
    manualPagination,
    manualSorting,
    pageCount: manualPagination ? pageCount : undefined,
    onRowSelectionChange: setRowSelection,
    onColumnVisibilityChange: setColumnVisibility,
    onSortingChange: handleSortingChange,
    onPaginationChange: handlePaginationChange,
    getCoreRowModel: getCoreRowModel(),
    ...(!manualSorting ? { getSortedRowModel: getSortedRowModel() } : {}),
    ...(!manualPagination ? { getPaginationRowModel: getPaginationRowModel() } : {}),
  });

  React.useEffect(() => {
    if (!manualPagination && useClientFiltering) {
      setInternalPagination((prev) => ({ ...prev, pageIndex: 0 }));
    }
  }, [filteredData.length, manualPagination, useClientFiltering]);

  const toolbarColumns = table.getAllColumns()
    .filter(column => column.getCanHide())
    .map(column => ({
      id: column.id,
      header: column.columnDef.header as string,
      visible: column.getIsVisible(),
      toggle: (value: boolean) => column.toggleVisibility(value),
    }));

  const additionalFilters = React.useMemo(() => {
    const filtersList: AdditionalFilterConfig[] = [];

    const stages = filterOptions?.stage && filterOptions.stage.length > 0
      ? filterOptions.stage
      : Array.from(new Set(data.map((permit) => permit.stage).filter(Boolean))) as string[];

    if (stages.length > 0) {
      filtersList.push({
        key: 'stage',
        label: 'שלב',
        type: 'select',
        value: filters?.stage?.value ?? 'all',
        showAllOption: false,
        options: [
          { value: 'all', label: 'כל השלבים' },
          ...stages.map((stage) => ({ value: stage, label: stage })),
        ],
      });
    }

    const docTypes = filterOptions?.documentType && filterOptions.documentType.length > 0
      ? filterOptions.documentType
      : Array.from(new Set(data.map((permit) => permit.documentType).filter(Boolean))) as string[];

    if (docTypes.length > 0) {
      filtersList.push({
        key: 'documentType',
        label: 'סוג מסמך',
        type: 'select',
        value: filters?.documentType?.value ?? 'all',
        showAllOption: false,
        options: [
          { value: 'all', label: 'כל הסוגים' },
          ...docTypes.map((type) => ({
            value: type,
            label: documentTypeDisplay(type),
          })),
        ],
      });
    }

    const sources = filterOptions?.source && filterOptions.source.length > 0
      ? filterOptions.source
      : Array.from(new Set(data.map((permit) => permit.source).filter(Boolean))) as string[];

    if (sources.length > 0) {
      filtersList.push({
        key: 'source',
        label: 'מקור',
        type: 'select',
        value: filters?.source?.value ?? 'all',
        showAllOption: false,
        options: [
          { value: 'all', label: 'כל המקורות' },
          ...sources.map((source) => ({
            value: source,
            label: sourceDisplay(source),
          })),
        ],
      });
    }

    const requestTypes = filterOptions?.requestType && filterOptions.requestType.length > 0
      ? filterOptions.requestType
      : Array.from(new Set(data.map((permit) => permit.requestType).filter(Boolean))) as string[];

    if (advancedFilters?.requestType && requestTypes.length > 0) {
      filtersList.push({
        key: 'requestType',
        label: 'סוג בקשה',
        type: 'select',
        value: advancedFilters.requestType.value ?? 'all',
        showAllOption: false,
        options: [
          { value: 'all', label: 'כל סוגי הבקשה' },
          ...requestTypes.map((requestType) => ({
            value: requestType,
            label: requestType,
          })),
        ],
      });
    }

    if (advancedFilters?.permitNumber) {
      filtersList.push({
        key: 'permitNumber',
        label: 'מספר היתר',
        type: 'text',
        value: advancedFilters.permitNumber.value,
        placeholder: 'לדוגמה 12345',
      });
    }

    if (advancedFilters?.requestNumber) {
      filtersList.push({
        key: 'requestNumber',
        label: 'מספר בקשה',
        type: 'text',
        value: advancedFilters.requestNumber.value,
        placeholder: 'לדוגמה 456/2024',
      });
    }

    if (advancedFilters?.description) {
      filtersList.push({
        key: 'description',
        label: 'תוכן הבקשה',
        type: 'text',
        value: advancedFilters.description.value,
        placeholder: 'חפש לפי תיאור',
      });
    }

    if (advancedFilters?.approvalDate) {
      filtersList.push({
        key: 'approvalDate',
        label: 'תאריך אישור',
        type: 'date-range',
        value: {
          from: advancedFilters.approvalDate.from,
          to: advancedFilters.approvalDate.to,
        },
      });
    }

    if (advancedFilters?.expiryDate) {
      filtersList.push({
        key: 'expiryDate',
        label: 'תוקף',
        type: 'date-range',
        value: {
          from: advancedFilters.expiryDate.from,
          to: advancedFilters.expiryDate.to,
        },
      });
    }

    return filtersList;
  }, [advancedFilters, data, filterOptions, filters]);

  const handleAdditionalFilterChange = (key: string, value: AdditionalFilterValue) => {
    if (typeof value === 'string') {
      if (key === 'stage' && filters?.stage?.onChange) {
        filters.stage.onChange(value);
      }
      if (key === 'documentType' && filters?.documentType?.onChange) {
        filters.documentType.onChange(value);
      }
      if (key === 'source' && filters?.source?.onChange) {
        filters.source.onChange(value);
      }
      if (key === 'requestType' && advancedFilters?.requestType) {
        advancedFilters.requestType.onChange(value);
      }
      if (key === 'permitNumber' && advancedFilters?.permitNumber) {
        advancedFilters.permitNumber.onChange(value);
      }
      if (key === 'requestNumber' && advancedFilters?.requestNumber) {
        advancedFilters.requestNumber.onChange(value);
      }
      if (key === 'description' && advancedFilters?.description) {
        advancedFilters.description.onChange(value);
      }
      return;
    }

    if ('from' in value || 'to' in value) {
      if (key === 'approvalDate' && advancedFilters?.approvalDate) {
        advancedFilters.approvalDate.onChange({ from: value.from, to: value.to });
      }
      if (key === 'expiryDate' && advancedFilters?.expiryDate) {
        advancedFilters.expiryDate.onChange({ from: value.from, to: value.to });
      }
      return;
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-border bg-card">
        <div className="p-8 text-center">
          <div className="text-muted-foreground">טוען היתרים...</div>
        </div>
      </div>
    );
  }

  const recordCount = manualPagination ? totalCount ?? data.length : filteredData.length;

  return (
    <div className="rounded-xl border border-border bg-card overflow-x-auto rtl" dir="rtl">
      <TableToolbar
        searchValue={searchValue}
        onSearchChange={(value) => {
          if (onSearchChange) {
            onSearchChange(value);
          }
          if (value.trim()) {
            trackFeatureUsage('search', undefined, { query: value.trim() });
          }
        }}
        searchPlaceholder="חיפוש בהיתרים..."
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

      <div className="relative">
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
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
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
                  <div className="flex flex-col items-center justify-center py-8 space-y-2">
                    <Building className="h-8 w-8 text-muted-foreground" />
                    <div className="text-muted-foreground">
                      {radius
                        ? `לא נמצאו היתרים ברדיוס ${radius} מטר`
                        : 'לא נמצאו היתרים'}
                    </div>
                  </div>
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
      </div>
      <TablePagination table={table} />
    </div>
  );
}
