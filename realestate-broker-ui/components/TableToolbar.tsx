"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/Badge";
import {
  Search,
  Filter,
  Download,
  Settings,
  Grid3X3,
  List,
  Map,
  X,
  Plus,
  RefreshCw,
} from "lucide-react";
import { useAnalytics } from "@/hooks/useAnalytics";

interface FilterOptionOption {
  value: string;
  label: string;
  count?: number;
}

interface FilterOption {
  key: string;
  label: string;
  value: string;
  options?: FilterOptionOption[];
}

interface TableToolbarProps {
  // Search
  searchValue: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder?: string;
  
  // Filters
  filters: {
    city: {
      value: string;
      onChange: (value: string) => void;
      options: string[];
    };
    type: {
      value: string;
      onChange: (value: string) => void;
      options: string[];
    };
    priceMin: {
      value: number | undefined;
      onChange: (value: number | undefined) => void;
    };
    priceMax: {
      value: number | undefined;
      onChange: (value: number | undefined) => void;
    };
    pricePerSqmMin?: {
      value: number | undefined;
      onChange: (value: number | undefined) => void;
    };
    pricePerSqmMax?: {
      value: number | undefined;
      onChange: (value: number | undefined) => void;
    };
    remainingRightsMin?: {
      value: number | undefined;
      onChange: (value: number | undefined) => void;
    };
    remainingRightsMax?: {
      value: number | undefined;
      onChange: (value: number | undefined) => void;
    };
  };
  
  // Column visibility
  columns: Array<{
    id: string;
    header: string;
    visible: boolean;
    toggle: (value: boolean) => void;
  }>;
  
  // Export
  onExportSelected: () => void;
  onExportAll: () => void;
  selectedCount: number;
  totalCount: number;
  
  // View mode
  viewMode: 'table' | 'cards' | 'map';
  onViewModeChange: (mode: 'table' | 'cards' | 'map') => void;
  
  // Actions
  onRefresh: () => void;
  onAddNew?: () => void;
  loading?: boolean;
  
  // Additional filters
  additionalFilters?: FilterOption[];
  onAdditionalFilterChange?: (key: string, value: string) => void;
  
  // Bulk actions
  bulkActions?: Array<{
    label: string;
    action: () => void;
    icon?: React.ReactNode;
    disabled?: boolean;
  }>;
  
  // Status filters
  statusFilters?: {
    value: string;
    onChange: (value: string) => void;
    options: Array<{ value: string; label: string; count?: number }>;
  };
  
  // Date range filters
  dateRange?: {
    from: Date | undefined;
    to: Date | undefined;
    onChange: (from: Date | undefined, to: Date | undefined) => void;
  };
}

export default function TableToolbar({
  searchValue,
  onSearchChange,
  searchPlaceholder = "חיפוש...",
  filters,
  columns,
  onExportSelected,
  onExportAll,
  selectedCount,
  totalCount,
  viewMode,
  onViewModeChange,
  onRefresh,
  onAddNew,
  loading = false,
  additionalFilters = [],
  onAdditionalFilterChange,
  bulkActions = [],
  statusFilters,
  dateRange,
}: TableToolbarProps) {
  const { trackFeatureUsage } = useAnalytics()
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [columnSearch, setColumnSearch] = useState('');
  const [isClient, setIsClient] = useState(false);

  // Handle hydration mismatch
  React.useEffect(() => {
    setIsClient(true);
  }, []);

  // Filter columns based on search
  const filteredColumns = columns.filter(column =>
    column.header.toLowerCase().includes(columnSearch.toLowerCase())
  );

  const hasActiveFilters = 
    filters.city.value !== 'all' ||
    filters.type.value !== 'all' ||
    filters.priceMin.value !== undefined ||
    filters.priceMax.value !== undefined ||
    (filters.pricePerSqmMin && filters.pricePerSqmMin.value !== undefined) ||
    (filters.pricePerSqmMax && filters.pricePerSqmMax.value !== undefined) ||
    (filters.remainingRightsMin && filters.remainingRightsMin.value !== undefined) ||
    (filters.remainingRightsMax && filters.remainingRightsMax.value !== undefined) ||
    additionalFilters.some(filter => filter.value !== 'all') ||
    (statusFilters && statusFilters.value !== 'all') ||
    (dateRange && (dateRange.from || dateRange.to)) ||
    (additionalFilters.find(f => f.key === 'userAssets')?.value === 'mine');

  const clearAllFilters = () => {
    filters.city.onChange('all');
    filters.type.onChange('all');
    filters.priceMin.onChange(undefined);
    filters.priceMax.onChange(undefined);
    filters.pricePerSqmMin?.onChange(undefined);
    filters.pricePerSqmMax?.onChange(undefined);
    filters.remainingRightsMin?.onChange(undefined);
    filters.remainingRightsMax?.onChange(undefined);
    additionalFilters.forEach(filter => {
      onAdditionalFilterChange?.(filter.key, 'all');
    });
    // Track filter usage
    trackFeatureUsage('filter', undefined, { action: 'clear_all' });
    statusFilters?.onChange('all');
    dateRange?.onChange(undefined, undefined);
  };

  return (
    <div className="flex flex-col gap-4 p-3 sm:p-4 border-b border-border bg-muted/30">
      {/* Search - Full width */}
      <div className="relative w-full">
        <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder={searchPlaceholder}
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pr-10 text-right w-full"
          dir="rtl"
        />
      </div>

      {/* Single row - All toolbar actions */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Filter toggle */}
        <Sheet open={filtersOpen} onOpenChange={setFiltersOpen}>
          <SheetTrigger asChild>
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 me-2" />
              <span className="hidden sm:inline">סינון</span>
              {hasActiveFilters && (
                <Badge variant="secondary" className="mr-2 h-5 w-5 p-0 flex items-center justify-center text-xs">
                  !
                </Badge>
              )}
            </Button>
          </SheetTrigger>
            <SheetContent className="w-80" side="right">
              <SheetHeader>
                <SheetTitle>סינון נכסים</SheetTitle>
              </SheetHeader>
              <div className="space-y-3 max-h-[calc(100vh-120px)] overflow-y-auto pr-2">
                <div className="flex items-center justify-between">
                  {hasActiveFilters && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={clearAllFilters}
                      className="h-8 px-2"
                    >
                      <X className="h-3 w-3 me-1" />
                      נקה הכל
                    </Button>
                  )}
                </div>

                {/* My Assets Checkbox - Prominent at top */}
                {additionalFilters.find(f => f.key === 'userAssets') && (
                  <div className="flex items-center space-x-2 p-3 bg-muted/50 rounded-lg border">
                    <input
                      type="checkbox"
                      id="my-assets-checkbox"
                      checked={additionalFilters.find(f => f.key === 'userAssets')?.value === 'mine'}
                      onChange={(e) => {
                        const value = e.target.checked ? 'mine' : 'all';
                        onAdditionalFilterChange?.('userAssets', value);
                        trackFeatureUsage('filter', undefined, { filter_type: 'my_assets', value });
                      }}
                      className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                    />
                    <Label htmlFor="my-assets-checkbox" className="text-sm font-medium cursor-pointer">
                      נכסים שלי בלבד
                    </Label>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-2">
                  {/* City filter */}
                  <div className="space-y-1">
                    <Label htmlFor="city-filter" className="text-sm">עיר</Label>
                    <Select value={filters.city.value} onValueChange={(value) => {
                      filters.city.onChange(value);
                      trackFeatureUsage('filter', undefined, { filter_type: 'city', value });
                    }}>
                      <SelectTrigger>
                        <SelectValue placeholder="כל הערים" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">כל הערים</SelectItem>
                        {filters.city.options.map((city) => (
                          <SelectItem key={city} value={city}>
                            {city}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Type filter */}
                  <div className="space-y-1">
                    <Label htmlFor="type-filter" className="text-sm">סוג נכס</Label>
                    <Select value={filters.type.value} onValueChange={(value) => {
                      filters.type.onChange(value);
                      trackFeatureUsage('filter', undefined, { filter_type: 'type', value });
                    }}>
                      <SelectTrigger>
                        <SelectValue placeholder="כל הסוגים" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">כל הסוגים</SelectItem>
                        {filters.type.options.map((type) => (
                          <SelectItem key={type} value={type}>
                            {type}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Price range */}
                  <div className="space-y-1">
                    <Label htmlFor="price-min" className="text-sm">מחיר מינימלי</Label>
                    <Input
                      id="price-min"
                      type="number"
                      placeholder="₪"
                      value={filters.priceMin.value || ""}
                      onChange={(e) => {
                        const value = e.target.value ? Number(e.target.value) : undefined;
                        filters.priceMin.onChange(value);
                        trackFeatureUsage('filter', undefined, { filter_type: 'price_min', value });
                      }}
                    />
                  </div>

                  <div className="space-y-1">
                    <Label htmlFor="price-max" className="text-sm">מחיר מקסימלי</Label>
                    <Input
                      id="price-max"
                      type="number"
                      placeholder="₪"
                      value={filters.priceMax.value || ""}
                      onChange={(e) => {
                        const value = e.target.value ? Number(e.target.value) : undefined;
                        filters.priceMax.onChange(value);
                        trackFeatureUsage('filter', undefined, { filter_type: 'price_max', value });
                      }}
                    />
                  </div>

                  {/* Price per sqm range */}
                  {filters.pricePerSqmMin && (
                    <div className="space-y-1">
                      <Label htmlFor="price-per-sqm-min" className="text-sm">מחיר למ&quot;ר מינימלי</Label>
                      <Input
                        id="price-per-sqm-min"
                        type="number"
                        placeholder="₪/מ²"
                        value={filters.pricePerSqmMin.value || ""}
                        onChange={(e) => {
                          const value = e.target.value ? Number(e.target.value) : undefined;
                          filters.pricePerSqmMin?.onChange(value);
                          trackFeatureUsage('filter', undefined, { filter_type: 'price_per_sqm_min', value });
                        }}
                      />
                    </div>
                  )}

                  {filters.pricePerSqmMax && (
                    <div className="space-y-1">
                      <Label htmlFor="price-per-sqm-max" className="text-sm">מחיר למ&quot;ר מקסימלי</Label>
                      <Input
                        id="price-per-sqm-max"
                        type="number"
                        placeholder="₪/מ²"
                        value={filters.pricePerSqmMax.value || ""}
                        onChange={(e) => {
                          const value = e.target.value ? Number(e.target.value) : undefined;
                          filters.pricePerSqmMax?.onChange(value);
                          trackFeatureUsage('filter', undefined, { filter_type: 'price_per_sqm_max', value });
                        }}
                      />
                    </div>
                  )}

                  {/* Remaining rights range */}
                  {filters.remainingRightsMin && (
                    <div className="space-y-1">
                      <Label htmlFor="remaining-rights-min" className="text-sm">יתרת זכויות מינימלית</Label>
                      <Input
                        id="remaining-rights-min"
                        type="number"
                        placeholder="מ²"
                        value={filters.remainingRightsMin.value || ""}
                        onChange={(e) => {
                          const value = e.target.value ? Number(e.target.value) : undefined;
                          filters.remainingRightsMin?.onChange(value);
                          trackFeatureUsage('filter', undefined, { filter_type: 'remaining_rights_min', value });
                        }}
                      />
                    </div>
                  )}

                  {filters.remainingRightsMax && (
                    <div className="space-y-1">
                      <Label htmlFor="remaining-rights-max" className="text-sm">יתרת זכויות מקסימלית</Label>
                      <Input
                        id="remaining-rights-max"
                        type="number"
                        placeholder="מ²"
                        value={filters.remainingRightsMax.value || ""}
                        onChange={(e) => {
                          const value = e.target.value ? Number(e.target.value) : undefined;
                          filters.remainingRightsMax?.onChange(value);
                          trackFeatureUsage('filter', undefined, { filter_type: 'remaining_rights_max', value });
                        }}
                      />
                    </div>
                  )}

                  {/* Additional filters */}
                  {additionalFilters.filter(filter => filter.key !== 'userAssets').map((filter) => (
                    <div key={filter.key} className="space-y-1">
                      <Label className="text-sm">{filter.label}</Label>
                      <Select
                        value={filter.value}
                        onValueChange={(value) => onAdditionalFilterChange?.(filter.key, value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder={`בחר ${filter.label.toLowerCase()}`} />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">הכל</SelectItem>
                          {filter.options?.map(option => (
                            <SelectItem key={option.value} value={option.value}>
                              <span className="flex justify-between gap-2">
                                <span>{option.label}</span>
                                {option.count !== undefined && (
                                  <span className="text-xs text-muted-foreground">{option.count}</span>
                                )}
                              </span>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  ))}
                </div>

                {/* Status filters */}
                {statusFilters && (
                  <div className="space-y-1">
                    <Label className="text-sm">סטטוס</Label>
                    <Select value={statusFilters.value} onValueChange={statusFilters.onChange}>
                      <SelectTrigger>
                        <SelectValue placeholder="כל הסטטוסים" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">כל הסטטוסים</SelectItem>
                        {statusFilters.options.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                            {option.count !== undefined && (
                              <span className="mr-2 text-muted-foreground">({option.count})</span>
                            )}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {/* Date range filter */}
                {dateRange && (
                  <div className="space-y-1">
                    <Label className="text-sm">טווח תאריכים</Label>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <Label className="text-xs text-muted-foreground">מ-</Label>
                        <Input
                          type="date"
                          value={dateRange.from ? dateRange.from.toISOString().split('T')[0] : ''}
                          onChange={(e) => {
                            const date = e.target.value ? new Date(e.target.value) : undefined;
                            dateRange.onChange(date, dateRange.to);
                          }}
                        />
                      </div>
                      <div>
                        <Label className="text-xs text-muted-foreground">עד</Label>
                        <Input
                          type="date"
                          value={dateRange.to ? dateRange.to.toISOString().split('T')[0] : ''}
                          onChange={(e) => {
                            const date = e.target.value ? new Date(e.target.value) : undefined;
                            dateRange.onChange(dateRange.from, date);
                          }}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </SheetContent>
          </Sheet>

        {/* View mode toggle */}
        <div className="flex items-center border rounded-md">
          <Button
            variant={viewMode === 'table' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => onViewModeChange('table')}
            className="rounded-r-none"
            title="תצוגת טבלה"
          >
            <List className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'cards' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => onViewModeChange('cards')}
            className="rounded-none border-x"
            title="תצוגת כרטיסים"
          >
            <Grid3X3 className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'map' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => onViewModeChange('map')}
            className="rounded-l-none"
            title="תצוגת מפה"
          >
            <Map className="h-4 w-4" />
          </Button>
        </div>

        {/* Column selection */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 me-2" />
              <span className="hidden sm:inline">עמודות</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-64 bg-white max-h-80">
            <DropdownMenuLabel className="bg-white text-foreground sticky top-0 z-10 bg-background border-b">
              בחר עמודות
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <div className="p-2 border-b">
              <div className="relative">
                <Search className="absolute right-2 top-1/2 transform -translate-y-1/2 h-3 w-3 text-muted-foreground" />
                <Input
                  placeholder="חיפוש עמודות..."
                  value={columnSearch}
                  onChange={(e) => setColumnSearch(e.target.value)}
                  className="pr-8 text-right text-sm h-8"
                  dir="rtl"
                />
              </div>
            </div>
            <div className="max-h-60 overflow-y-auto">
              {/* Quick actions */}
              <div className="p-2 border-b bg-muted/30">
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      filteredColumns.forEach(column => {
                        if (!column.visible) column.toggle(true);
                      });
                    }}
                    className="h-6 px-2 text-xs"
                  >
                    בחר הכל
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      filteredColumns.forEach(column => {
                        if (column.visible) column.toggle(false);
                      });
                    }}
                    className="h-6 px-2 text-xs"
                  >
                    בטל הכל
                  </Button>
                </div>
              </div>
              {filteredColumns.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  לא נמצאו עמודות
                </div>
              ) : (
                filteredColumns.map((column) => (
                  <DropdownMenuCheckboxItem
                    key={column.id}
                    checked={column.visible}
                    onCheckedChange={column.toggle}
                    onSelect={(e) => e.preventDefault()}
                    className="bg-white text-foreground hover:bg-muted"
                  >
                    {column.header}
                  </DropdownMenuCheckboxItem>
                ))
              )}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Bulk actions dropdown */}
        {bulkActions.length > 0 && selectedCount > 0 && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                <span className="hidden sm:inline">פעולות ({selectedCount})</span>
                <span className="sm:hidden">({selectedCount})</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="bg-white">
              <DropdownMenuLabel className="bg-white text-foreground">פעולות על נבחרים</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {bulkActions.map((action, index) => (
                <DropdownMenuCheckboxItem 
                  key={index}
                  onClick={action.action}
                  disabled={action.disabled}
                  className="bg-white text-foreground hover:bg-muted"
                >
                  {action.icon && <span className="mr-2">{action.icon}</span>}
                  {action.label}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {/* Export dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 me-2" />
              <span className="hidden sm:inline">ייצוא</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="bg-white">
            <DropdownMenuLabel className="bg-white text-foreground">ייצוא נתונים</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuCheckboxItem 
              onClick={onExportAll}
              className="bg-white text-foreground hover:bg-muted"
            >
              ייצוא הכל ({totalCount})
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem 
              onClick={onExportSelected}
              disabled={selectedCount === 0}
              className="bg-white text-foreground hover:bg-muted"
            >
              ייצוא נבחרים ({selectedCount})
            </DropdownMenuCheckboxItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Refresh */}
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 me-2 ${loading ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">רענן</span>
        </Button>

        {/* Add new */}
        {onAddNew && (
          <Button onClick={onAddNew} size="sm">
            <Plus className="h-4 w-4 me-2" />
            <span className="hidden sm:inline">הוסף חדש</span>
          </Button>
        )}
      </div>

      {/* Bottom row - Status and info */}
      <div className="flex flex-col sm:flex-row gap-2 sm:items-center sm:justify-between text-sm text-muted-foreground">
        <div className="flex items-center gap-4">
          <span>
            {isClient && selectedCount > 0 ? `${selectedCount} נבחרים מתוך ` : ''}
            {totalCount} נכסים
          </span>
          {hasActiveFilters && (
            <Badge variant="outline" className="text-xs">
              מסונן
            </Badge>
          )}
        </div>
        <div className="text-xs">
          {isClient ? `${columns.filter(c => c.visible).length} מתוך ${columns.length} עמודות` : `${columns.length} עמודות`}
        </div>
      </div>
    </div>
  );
}
