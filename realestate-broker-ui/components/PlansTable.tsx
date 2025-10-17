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
import { Calendar, Building, ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react';
import TableToolbar, { AdditionalFilterConfig, AdditionalFilterValue } from '@/components/TableToolbar';
import TablePagination from '@/components/TablePagination';
import { useAnalytics } from '@/hooks/useAnalytics';

interface Plan {
  id: string;
  plan_number: string;
  title?: string;
  description: string;
  status: string;
  effective_date?: string;
  file_url?: string;
  source: string;
  raw?: any;
}

interface PlansTableProps {
  data?: Plan[];
  loading?: boolean;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  filters?: {
    source: {
      value: string;
      onChange: (value: string) => void;
      options: Array<{ value: string; label: string }>;
    };
    status: {
      value: string;
      onChange: (value: string) => void;
      options: Array<{ value: string; label: string }>;
    };
  };
  onRefresh?: () => void;
  manualPagination?: boolean;
  manualSorting?: boolean;
  pageCount?: number;
  paginationState?: PaginationState;
  onPaginationChange?: (value: PaginationState) => void;
  sortingState?: SortingState;
  onSortingChange?: (value: SortingState) => void;
  totalCount?: number;
  filterOptions?: {
    source?: string[];
    status?: string[];
  };
  advancedFilters?: {
    planNumber?: { value: string; onChange: (value: string) => void };
    description?: { value: string; onChange: (value: string) => void };
  };
}

function createColumns(): ColumnDef<Plan>[] {
  return [
    {
      accessorKey: 'plan_number',
      header: 'מספר תוכנית',
      cell: ({ row }) => (
        <div className="font-medium text-sm">
          {row.getValue('plan_number')}
        </div>
      ),
    },
    {
      accessorKey: 'title',
      header: 'שם תוכנית',
      cell: ({ row }) => {
        const value = row.getValue('title') as string | undefined;
        const fallback = row.original.description;
        return (
          <div className="max-w-[300px] truncate text-sm">
            {value || fallback || 'ללא שם'}
          </div>
        );
      },
    },
    {
      accessorKey: 'description',
      header: 'תיאור',
      cell: ({ row }) => (
        <div className="max-w-[300px] truncate text-sm">
          {row.getValue('description') || 'ללא תיאור'}
        </div>
      ),
    },
    {
      accessorKey: 'source',
      header: 'מקור',
      cell: ({ row }) => {
        const source = row.getValue('source') as string;
        const getSourceDisplay = (source: string) => {
          switch (source) {
            case 'rami': return 'רמ״י';
            case 'mavat': return 'מנהל התיכנון';
            case 'collected_government': return 'מנהל התיכנון';
            default: return 'מקומי';
          }
        };
        const getSourceVariant = (source: string) => {
          switch (source) {
            case 'rami': return 'default';
            case 'mavat': return 'secondary';
            case 'collected_government': return 'secondary';
            default: return 'outline';
          }
        };
        return (
          <Badge variant={getSourceVariant(source) as any}>
            {getSourceDisplay(source)}
          </Badge>
        );
      },
    },
    {
      accessorKey: 'status',
      header: 'סטטוס',
      cell: ({ row }) => {
        const status = row.getValue('status') as string;
        return (
          <Badge variant={status === 'מאושר' ? 'success' : 'neutral'}>
            {status || 'לא ידוע'}
          </Badge>
        );
      },
    },
    {
      accessorKey: 'effective_date',
      header: 'תאריך תוקף',
      cell: ({ row }) => {
        const date = row.getValue('effective_date') as string;
        return date ? (
          <div className="flex items-center gap-1 text-sm text-muted-foreground rtl:flex-row-reverse">
            <Calendar className="h-3 w-3" />
            {new Date(date).toLocaleDateString('he-IL')}
          </div>
        ) : (
          <span className="text-muted-foreground text-sm">—</span>
        );
      },
    },
  ];
}

export default function PlansTable({
  data = [],
  loading = false,
  searchValue = '',
  onSearchChange,
  filters,
  onRefresh,
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
}: PlansTableProps) {
  const { trackFeatureUsage } = useAnalytics();
  const [rowSelection, setRowSelection] = React.useState({});
  const [columnVisibility, setColumnVisibility] = React.useState<Record<string, boolean>>({});
  const [internalSorting, setInternalSorting] = React.useState<SortingState>(sortingState ?? []);
  const [internalPagination, setInternalPagination] = React.useState<PaginationState>(
    paginationState ?? {
      pageIndex: 0,
      pageSize: 10,
    }
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

  const filteredData = React.useMemo(() => {
    if (!useClientFiltering) {
      return data;
    }

    return data.filter((plan) => {
      if (searchValue) {
        const searchLower = searchValue.toLowerCase();
        const matchesSearch =
          plan.title?.toLowerCase().includes(searchLower) ||
          plan.description?.toLowerCase().includes(searchLower) ||
          plan.plan_number?.toLowerCase().includes(searchLower) ||
          plan.status?.toLowerCase().includes(searchLower) ||
          plan.raw?.title?.toLowerCase().includes(searchLower) ||
          plan.raw?.authority?.toLowerCase().includes(searchLower) ||
          plan.raw?.jurisdiction?.toLowerCase().includes(searchLower);
        if (!matchesSearch) return false;
      }

      if (filters?.source?.value && filters.source.value !== 'all' && plan.source !== filters.source.value) {
        return false;
      }

      if (filters?.status?.value && filters.status.value !== 'all' && plan.status !== filters.status.value) {
        return false;
      }

      if (advancedFilters?.planNumber?.value) {
        const planNumberSearch = advancedFilters.planNumber.value.trim().toLowerCase();
        if (planNumberSearch && !plan.plan_number?.toLowerCase().includes(planNumberSearch)) {
          return false;
        }
      }

      if (advancedFilters?.description?.value) {
        const descriptionSearch = advancedFilters.description.value.trim().toLowerCase();
        if (
          descriptionSearch &&
          !(
            plan.title?.toLowerCase().includes(descriptionSearch) ||
            plan.description?.toLowerCase().includes(descriptionSearch) ||
            plan.raw?.title?.toLowerCase().includes(descriptionSearch)
          )
        ) {
          return false;
        }
      }

      return true;
    });
  }, [
    data,
    searchValue,
    filters,
    useClientFiltering,
    advancedFilters?.planNumber?.value,
    advancedFilters?.description?.value,
  ]);

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
    enableRowSelection: true,
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
      toggle: (value: boolean) => column.toggleVisibility(value)
    }));

  const additionalFilters = React.useMemo((): AdditionalFilterConfig[] => {
    const filtersList: AdditionalFilterConfig[] = [];

    const sources = filterOptions?.source && filterOptions.source.length > 0
      ? filterOptions.source
      : [...new Set(data.map(plan => plan.source).filter(Boolean))];

    if (sources.length > 0) {
      filtersList.push({
        key: 'source',
        label: 'מקור',
        type: 'select',
        value: filters?.source?.value ?? 'all',
        showAllOption: false,
        options: [
          { value: 'all', label: 'הכל' },
          ...sources.map(source => ({
            value: source,
            label: source === 'rami' ? 'רמ״י' : source === 'mavat' ? 'מנהל התיכנון' : 'מקומי'
          }))
        ]
      });
    }

    const statuses = filterOptions?.status && filterOptions.status.length > 0
      ? filterOptions.status
      : [...new Set(data.map(plan => plan.status).filter(Boolean))];

    if (statuses.length > 0) {
      filtersList.push({
        key: 'status',
        label: 'סטטוס',
        type: 'select',
        value: filters?.status?.value ?? 'all',
        showAllOption: false,
        options: [
          { value: 'all', label: 'הכל' },
          ...statuses.map(status => ({ value: status, label: status }))
        ]
      });
    }

    if (advancedFilters?.planNumber) {
      filtersList.push({
        key: 'planNumber',
        label: 'מספר תוכנית',
        type: 'text',
        value: advancedFilters.planNumber.value,
        placeholder: 'לדוגמה 12345',
      });
    }

    if (advancedFilters?.description) {
      filtersList.push({
        key: 'description',
        label: 'תיאור',
        type: 'text',
        value: advancedFilters.description.value,
        placeholder: 'חפש בתיאור...',
      });
    }

    return filtersList;
  }, [advancedFilters, data, filters, filterOptions]);

  const handleAdditionalFilterChange = (key: string, value: AdditionalFilterValue) => {
    if (typeof value === 'string') {
      if (key === 'source' && filters?.source?.onChange) {
        filters.source.onChange(value);
      }
      if (key === 'status' && filters?.status?.onChange) {
        filters.status.onChange(value);
      }
      if (key === 'planNumber' && advancedFilters?.planNumber) {
        advancedFilters.planNumber.onChange(value);
      }
      if (key === 'description' && advancedFilters?.description) {
        advancedFilters.description.onChange(value);
      }
      trackFeatureUsage('filter', undefined, { filter_type: key, value });
      return;
    }
    trackFeatureUsage('filter', undefined, { filter_type: key, value });
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-border bg-card">
        <div className="p-8 text-center">
          <div className="text-muted-foreground">טוען תוכניות...</div>
        </div>
      </div>
    );
  }

  const recordCount = manualPagination ? (totalCount ?? data.length) : filteredData.length;

  return (
    <div className="rounded-xl border border-border bg-card overflow-x-auto rtl">
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
        searchPlaceholder="חיפוש בתוכניות..."
        additionalFilters={additionalFilters}
        onAdditionalFilterChange={handleAdditionalFilterChange}
        columns={toolbarColumns}
        selectedCount={table.getSelectedRowModel().rows.length}
        totalCount={recordCount}
        onExportSelected={() => {}}
        onExportAll={() => {}}
        viewMode="table"
        onViewModeChange={() => {}}
        onRefresh={onRefresh || (() => {})}
        loading={loading}
      />

      <div className="relative rtl">
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
            {table.getRowModel().rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  <div className="flex flex-col items-center justify-center py-8">
                    <Building className="h-8 w-8 text-muted-foreground mb-2" />
                    <div className="text-muted-foreground">לא נמצאו תוכניות</div>
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
