"use client";
import React from 'react';
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
  ColumnResizeMode,
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
import { Calendar, Building } from 'lucide-react';
import TableToolbar from '@/components/TableToolbar';
import { useAnalytics } from '@/hooks/useAnalytics';

interface Plan {
  id: string;
  plan_number: string;
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
            default: return 'מקומי';
          }
        };
        const getSourceVariant = (source: string) => {
          switch (source) {
            case 'rami': return 'default';
            case 'mavat': return 'secondary';
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
}: PlansTableProps) {
  const { trackFeatureUsage } = useAnalytics();
  const [rowSelection, setRowSelection] = React.useState({});
  const [columnVisibility, setColumnVisibility] = React.useState<Record<string, boolean>>({});

  const columns = React.useMemo(() => createColumns(), []);

  const filteredData = React.useMemo(() => {
    return data.filter(plan => {
      // Search filter
      if (searchValue) {
        const searchLower = searchValue.toLowerCase();
        const matchesSearch = 
          plan.description?.toLowerCase().includes(searchLower) ||
          plan.plan_number?.toLowerCase().includes(searchLower) ||
          plan.status?.toLowerCase().includes(searchLower) ||
          plan.raw?.title?.toLowerCase().includes(searchLower) ||
          plan.raw?.authority?.toLowerCase().includes(searchLower) ||
          plan.raw?.jurisdiction?.toLowerCase().includes(searchLower);
        if (!matchesSearch) return false;
      }

      // Source filter
      if (filters?.source?.value && filters.source.value !== 'all' && plan.source !== filters.source.value) {
        return false;
      }

      // Status filter
      if (filters?.status?.value && filters.status.value !== 'all' && plan.status !== filters.status.value) {
        return false;
      }

      return true;
    });
  }, [data, searchValue, filters]);

  const table = useReactTable({
    data: filteredData,
    columns,
    state: {
      rowSelection,
      columnVisibility,
    },
    enableRowSelection: true,
    onRowSelectionChange: setRowSelection,
    onColumnVisibilityChange: setColumnVisibility,
    getCoreRowModel: getCoreRowModel(),
  });

  // Prepare columns for toolbar
  const toolbarColumns = table.getAllColumns()
    .filter(column => column.getCanHide())
    .map(column => ({
      id: column.id,
      header: column.columnDef.header as string,
      visible: column.getIsVisible(),
      toggle: (value: boolean) => column.toggleVisibility(value)
    }));

  const additionalFilters = React.useMemo(() => {
    const filters = [];
    
    if (data.length > 0) {
      // Source filter
      const sources = [...new Set(data.map(plan => plan.source))];
      if (sources.length > 1) {
        filters.push({
          key: 'source',
          label: 'מקור',
          type: 'select',
          value: 'all',
          options: [
            { value: 'all', label: 'הכל' },
            ...sources.map(source => ({
              value: source,
              label: source === 'rami' ? 'רמ״י' : source === 'mavat' ? 'מנהל התיכנון' : 'מקומי'
            }))
          ]
        });
      }

      // Status filter
      const statuses = [...new Set(data.map(plan => plan.status).filter(Boolean))];
      if (statuses.length > 1) {
        filters.push({
          key: 'status',
          label: 'סטטוס',
          type: 'select',
          value: 'all',
          options: [
            { value: 'all', label: 'הכל' },
            ...statuses.map(status => ({ value: status, label: status }))
          ]
        });
      }
    }

    return filters;
  }, [data]);

  const handleAdditionalFilterChange = (key: string, value: string) => {
    // Handle filter changes here if needed
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

  return (
    <div className="rounded-xl border border-border bg-card overflow-x-auto rtl">
      {/* Integrated Toolbar */}
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
        filters={{
          city: { value: 'all', onChange: () => {}, options: [] },
          type: { value: 'all', onChange: () => {}, options: [] },
          priceMin: { value: undefined, onChange: () => {} },
          priceMax: { value: undefined, onChange: () => {} },
          ...(filters || {})
        }}
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

      {/* Table */}
      <div className="relative rtl">
        <Table className="rtl">
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id} className="text-right rtl:text-right">
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {filteredData.length === 0 ? (
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
    </div>
  );
}
