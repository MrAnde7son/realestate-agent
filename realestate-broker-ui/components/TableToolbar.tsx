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
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
} from "@/components/ui/dropdown-menu";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/Badge";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
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
  ChevronDown,
} from "lucide-react";
import { useAnalytics } from "@/hooks/useAnalytics";

export type AdditionalFilterValue =
  | string
  | { min?: number; max?: number }
  | { from?: string; to?: string };

const QUICK_FILTER_POPOVER_PROPS = {
  align: "end" as const,
  side: "bottom" as const,
  sideOffset: 12,
  collisionPadding: 16,
};

const QUICK_FILTER_POPOVER_CLASSNAME =
  "w-[calc(100vw-2rem)] max-w-sm sm:w-80 rtl:text-right bg-background text-foreground";

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

interface BaseAdditionalFilter {
  key: string;
  label: string;
  analyticsKey?: string;
}

interface SelectAdditionalFilter extends BaseAdditionalFilter {
  type?: 'select';
  value: string;
  options: FilterOptionOption[];
  defaultValue?: string;
  placeholder?: string;
  showAllOption?: boolean;
}

interface TextAdditionalFilter extends BaseAdditionalFilter {
  type: 'text';
  value: string;
  placeholder?: string;
  defaultValue?: string;
}

interface NumberRangeAdditionalFilter extends BaseAdditionalFilter {
  type: 'number-range';
  value: { min?: number; max?: number };
  defaultValue?: { min?: number; max?: number };
  minPlaceholder?: string;
  maxPlaceholder?: string;
  step?: number;
}

interface DateRangeAdditionalFilter extends BaseAdditionalFilter {
  type: 'date-range';
  value: { from?: string; to?: string };
  defaultValue?: { from?: string; to?: string };
  fromPlaceholder?: string;
  toPlaceholder?: string;
}

export type AdditionalFilterConfig =
  | SelectAdditionalFilter
  | TextAdditionalFilter
  | NumberRangeAdditionalFilter
  | DateRangeAdditionalFilter;

interface SelectFilterConfig {
  value: string;
  onChange: (value: string) => void;
  options: string[];
  label?: string;
  placeholder?: string;
  allLabel?: string;
  showAllOption?: boolean;
  alwaysVisible?: boolean;
  analyticsKey?: string;
}

interface NumericFilterConfig {
  value: number | undefined;
  onChange: (value: number | undefined) => void;
  label?: string;
  placeholder?: string;
  analyticsKey?: string;
}

interface TableToolbarFilters {
  city?: SelectFilterConfig;
  type?: SelectFilterConfig;
  priceMin?: NumericFilterConfig;
  priceMax?: NumericFilterConfig;
  areaMin?: NumericFilterConfig;
  areaMax?: NumericFilterConfig;
  pricePerSqmMin?: NumericFilterConfig;
  pricePerSqmMax?: NumericFilterConfig;
  remainingRightsMin?: NumericFilterConfig;
  remainingRightsMax?: NumericFilterConfig;
  rentalSale?: {
    value: string;
    onChange: (value: string) => void;
    options: Array<{ value: string; label: string }>;
  };
  userAssets?: {
    value: string;
    onChange: (value: string) => void;
    options?: Array<{ value: string; label: string }>;
  };
}

interface TableToolbarProps {
  // Search
  searchValue: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder?: string;

  // Filters
  filters?: TableToolbarFilters;

  // Column visibility
  columns: Array<{
    id: string;
    header: string;
    visible: boolean;
    toggle: (value: boolean) => void;
  }>;
  onResetColumns?: () => void;

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
  additionalFilters?: AdditionalFilterConfig[];
  onAdditionalFilterChange?: (key: string, value: AdditionalFilterValue) => void;

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
  onResetColumns,
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
  const cityFilter = filters?.city;
  const typeFilter = filters?.type;
  const priceMinFilter = filters?.priceMin;
  const priceMaxFilter = filters?.priceMax;
  const areaMinFilter = filters?.areaMin;
  const areaMaxFilter = filters?.areaMax;
  const pricePerSqmMinFilter = filters?.pricePerSqmMin;
  const pricePerSqmMaxFilter = filters?.pricePerSqmMax;
  const remainingRightsMinFilter = filters?.remainingRightsMin;
  const remainingRightsMaxFilter = filters?.remainingRightsMax;
  const rentalSaleFilter = filters?.rentalSale;
  const userAssetsQuickFilter = filters?.userAssets;
  const [pricePopoverOpen, setPricePopoverOpen] = useState(false);
  const [areaPopoverOpen, setAreaPopoverOpen] = useState(false);
  const [typeMenuOpen, setTypeMenuOpen] = useState(false);
  const [rentalSaleMenuOpen, setRentalSaleMenuOpen] = useState(false);

  // Handle hydration mismatch
  React.useEffect(() => {
    setIsClient(true);
  }, []);

  // Filter columns based on search
  const filteredColumns = columns.filter(column =>
    column.header.toLowerCase().includes(columnSearch.toLowerCase())
  );
  const userAssetsAdditionalFilter = additionalFilters.find(
    (filter): filter is SelectAdditionalFilter =>
      filter.key === 'userAssets' && (!filter.type || filter.type === 'select')
  );

  const currencyFormatter = React.useMemo(
    () =>
      new Intl.NumberFormat('he-IL', {
        style: 'currency',
        currency: 'ILS',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }),
    []
  );

  const numberFormatter = React.useMemo(
    () => new Intl.NumberFormat('he-IL'),
    []
  );

  const formatCurrencyValue = React.useCallback(
    (value?: number) => {
      if (typeof value !== 'number' || isNaN(value)) return undefined;
      return currencyFormatter.format(value);
    },
    [currencyFormatter]
  );

  const formatNumberValue = React.useCallback(
    (value?: number) => {
      if (typeof value !== 'number' || isNaN(value)) return undefined;
      return numberFormatter.format(value);
    },
    [numberFormatter]
  );

  const priceHasValue =
    (priceMinFilter && priceMinFilter.value !== undefined) ||
    (priceMaxFilter && priceMaxFilter.value !== undefined);

  const priceButtonText = (() => {
    if (!priceHasValue) return 'מחיר';
    const minLabel = formatCurrencyValue(priceMinFilter?.value ?? undefined);
    const maxLabel = formatCurrencyValue(priceMaxFilter?.value ?? undefined);
    if (minLabel && maxLabel) {
      return `מחיר: ${minLabel} - ${maxLabel}`;
    }
    if (minLabel) {
      return `מחיר: מ-${minLabel}`;
    }
    if (maxLabel) {
      return `מחיר: עד ${maxLabel}`;
    }
    return 'מחיר';
  })();

  const areaHasValue =
    (areaMinFilter && areaMinFilter.value !== undefined) ||
    (areaMaxFilter && areaMaxFilter.value !== undefined);

  const areaButtonText = (() => {
    if (!areaHasValue) return 'שטח';
    const minLabel = formatNumberValue(areaMinFilter?.value ?? undefined);
    const maxLabel = formatNumberValue(areaMaxFilter?.value ?? undefined);
    if (minLabel && maxLabel) {
      return `שטח: ${minLabel}-${maxLabel} מ"ר`;
    }
    if (minLabel) {
      return `שטח: מ-${minLabel} מ"ר`;
    }
    if (maxLabel) {
      return `שטח: עד ${maxLabel} מ"ר`;
    }
    return 'שטח';
  })();

  const typeHasValue = typeFilter && typeFilter.value !== 'all';
  const typeButtonText = typeHasValue ? `סוג נכס: ${typeFilter?.value}` : 'סוג נכס';

  const rentalSaleDefaultLabel = 'סוג עיסקה';

  const rentalSaleSelectedLabel = (() => {
    if (!rentalSaleFilter || rentalSaleFilter.value === 'all') return rentalSaleDefaultLabel;
    return (
      rentalSaleFilter.options.find(option => option.value === rentalSaleFilter.value)?.label ||
      rentalSaleDefaultLabel
    );
  })();

  const userAssetsValue = userAssetsQuickFilter?.value ?? userAssetsAdditionalFilter?.value;
  const userAssetsActive = Boolean(userAssetsValue && userAssetsValue !== 'all');

  const additionalFiltersActive = additionalFilters?.some((filter) => {
    if (filter.type === 'number-range') {
      return filter.value.min !== undefined || filter.value.max !== undefined;
    }
    if (filter.type === 'date-range') {
      return Boolean(filter.value.from) || Boolean(filter.value.to);
    }
    if (filter.type === 'text') {
      return (filter.value ?? '').trim() !== (filter.defaultValue ?? '');
    }
    const defaultValue = filter.type === 'select' || filter.type === undefined
      ? filter.defaultValue ?? 'all'
      : undefined;
    return filter.value !== defaultValue;
  }) ?? false;

  const hasActiveFilters = 
    (cityFilter && cityFilter.value !== 'all') ||
    (typeFilter && typeFilter.value !== 'all') ||
    (priceMinFilter && priceMinFilter.value !== undefined) ||
    (priceMaxFilter && priceMaxFilter.value !== undefined) ||
    (pricePerSqmMinFilter && pricePerSqmMinFilter.value !== undefined) ||
    (pricePerSqmMaxFilter && pricePerSqmMaxFilter.value !== undefined) ||
    (areaMinFilter && areaMinFilter.value !== undefined) ||
    (areaMaxFilter && areaMaxFilter.value !== undefined) ||
    (remainingRightsMinFilter && remainingRightsMinFilter.value !== undefined) ||
    (remainingRightsMaxFilter && remainingRightsMaxFilter.value !== undefined) ||
    (rentalSaleFilter && rentalSaleFilter.value !== 'all') ||
    additionalFiltersActive ||
    (statusFilters && statusFilters.value !== 'all') ||
    (dateRange && (dateRange.from || dateRange.to)) ||
    userAssetsActive;

  const clearAllFilters = () => {
    if (cityFilter) {
      const nextValue = cityFilter.showAllOption === false ? (cityFilter.options[0] ?? '') : 'all';
      cityFilter.onChange(nextValue);
    }
    if (typeFilter) {
      const nextValue = typeFilter.showAllOption === false ? (typeFilter.options[0] ?? '') : 'all';
      typeFilter.onChange(nextValue);
    }
    priceMinFilter?.onChange(undefined);
    priceMaxFilter?.onChange(undefined);
    areaMinFilter?.onChange(undefined);
    areaMaxFilter?.onChange(undefined);
    pricePerSqmMinFilter?.onChange(undefined);
    pricePerSqmMaxFilter?.onChange(undefined);
    remainingRightsMinFilter?.onChange(undefined);
    remainingRightsMaxFilter?.onChange(undefined);
    additionalFilters?.forEach(filter => {
      if (filter.type === 'number-range') {
        onAdditionalFilterChange?.(filter.key, filter.defaultValue ?? { min: undefined, max: undefined });
      } else if (filter.type === 'date-range') {
        onAdditionalFilterChange?.(filter.key, filter.defaultValue ?? { from: undefined, to: undefined });
      } else if (filter.type === 'text') {
        onAdditionalFilterChange?.(filter.key, filter.defaultValue ?? '');
      } else {
        const defaultValue = filter.defaultValue ?? 'all';
        onAdditionalFilterChange?.(filter.key, defaultValue);
      }
    });
    // Track filter usage
    trackFeatureUsage('filter', undefined, { action: 'clear_all' });
    statusFilters?.onChange('all');
    dateRange?.onChange(undefined, undefined);
    if (!onAdditionalFilterChange) {
      rentalSaleFilter?.onChange('all');
      userAssetsQuickFilter?.onChange('all');
    }
  };

  const renderAdditionalFilterControl = (filter: AdditionalFilterConfig) => {
    const track = (metadata: Record<string, any>) =>
      trackFeatureUsage('filter', undefined, {
        filter_type: filter.analyticsKey ?? filter.key,
        ...metadata,
      });

    if (filter.type === 'number-range') {
      return (
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">מינימום</Label>
            <Input
              type="number"
              value={filter.value.min ?? ''}
              placeholder={filter.minPlaceholder ?? ''}
              step={filter.step}
              dir="ltr"
              inputMode="numeric"
              className="text-left"
              onChange={(e) => {
                const parsed = e.target.value ? Number(e.target.value) : undefined;
                onAdditionalFilterChange?.(filter.key, { ...filter.value, min: parsed });
                track({ value: parsed ?? 'clear', suffix: 'min' });
              }}
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">מקסימום</Label>
            <Input
              type="number"
              value={filter.value.max ?? ''}
              placeholder={filter.maxPlaceholder ?? ''}
              step={filter.step}
              dir="ltr"
              inputMode="numeric"
              className="text-left"
              onChange={(e) => {
                const parsed = e.target.value ? Number(e.target.value) : undefined;
                onAdditionalFilterChange?.(filter.key, { ...filter.value, max: parsed });
                track({ value: parsed ?? 'clear', suffix: 'max' });
              }}
            />
          </div>
        </div>
      );
    }

    if (filter.type === 'date-range') {
      return (
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">מתאריך</Label>
            <Input
              type="date"
              value={filter.value.from ?? ''}
              placeholder={filter.fromPlaceholder}
              onChange={(e) => {
                const value = e.target.value || undefined;
                onAdditionalFilterChange?.(filter.key, { ...filter.value, from: value });
                track({ value: value ?? 'clear', suffix: 'from' });
              }}
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">עד תאריך</Label>
            <Input
              type="date"
              value={filter.value.to ?? ''}
              placeholder={filter.toPlaceholder}
              onChange={(e) => {
                const value = e.target.value || undefined;
                onAdditionalFilterChange?.(filter.key, { ...filter.value, to: value });
                track({ value: value ?? 'clear', suffix: 'to' });
              }}
            />
          </div>
        </div>
      );
    }

    if (filter.type === 'text') {
      return (
        <Input
          value={filter.value}
          placeholder={filter.placeholder}
          onChange={(e) => {
            const value = e.target.value;
            onAdditionalFilterChange?.(filter.key, value);
            track({ value });
          }}
        />
      );
    }

    return (
      <Select
        value={filter.value}
        onValueChange={(value) => {
          onAdditionalFilterChange?.(filter.key, value);
          track({ value });
        }}
      >
        <SelectTrigger>
          <SelectValue placeholder={filter.placeholder ?? `בחר ${filter.label.toLowerCase()}`} />
        </SelectTrigger>
        <SelectContent>
          {(() => {
            const defaultValue = filter.defaultValue ?? 'all';
            const hasDefaultOption = filter.options?.some((option) => option.value === defaultValue);
            const shouldRenderDefault = filter.showAllOption ?? !hasDefaultOption;
            return shouldRenderDefault ? (
              <SelectItem value={defaultValue}>הכל</SelectItem>
            ) : null;
          })()}
          {filter.options?.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              <span className="flex justify-between gap-2 rtl:flex-row-reverse">
                <span>{option.label}</span>
                {option.count !== undefined && (
                  <span className="text-xs text-muted-foreground">{option.count}</span>
                )}
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    );
  };

  return (
    <div className="flex flex-col gap-3 p-3 sm:p-4 border-b border-border bg-muted/30 rtl" dir="rtl">
      {/* Search - Full width */}
      <div className="relative w-full">
        <Search className="absolute end-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder={searchPlaceholder}
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pe-10 text-start w-full min-h-[44px]"
          dir="rtl"
        />
      </div>

      {/* Quick filters and toolbar actions */}
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between" dir="rtl">
        <div className="lg:flex-1">
          <div
            data-testid="quick-filters-container"
            className="flex min-w-0 items-center gap-2 overflow-x-auto pb-1 rtl:flex-row-reverse lg:flex-wrap lg:overflow-visible lg:pb-0"
          >
            {userAssetsQuickFilter && (
              <Button
                type="button"
                variant={userAssetsActive ? 'default' : 'outline'}
                size="sm"
                className="h-10 rounded-full px-4 flex-shrink-0"
                aria-pressed={userAssetsActive}
                onClick={() => {
                  const nextValue = userAssetsActive ? 'all' : 'mine';
                  if (onAdditionalFilterChange) {
                    onAdditionalFilterChange('userAssets', nextValue);
                  } else {
                    userAssetsQuickFilter.onChange(nextValue);
                    trackFeatureUsage('filter', undefined, { filter_type: 'userAssets', value: nextValue });
                  }
                }}
              >
                הנכסים שלי
              </Button>
            )}

            {rentalSaleFilter && (
              <DropdownMenu open={rentalSaleMenuOpen} onOpenChange={setRentalSaleMenuOpen}>
                <DropdownMenuTrigger asChild>
                  <Button
                    type="button"
                    variant={rentalSaleFilter.value !== 'all' ? 'default' : 'outline'}
                    size="sm"
                    className="h-10 rounded-full px-4 flex items-center gap-2 flex-shrink-0"
                  >
                    <span>{rentalSaleSelectedLabel}</span>
                    <ChevronDown className="h-4 w-4 rtl:rotate-180" aria-hidden="true" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48" style={{ direction: "rtl" }}>
                  <DropdownMenuLabel className="text-xs text-muted-foreground">בחר סוג עיסקה</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuRadioGroup
                    value={rentalSaleFilter.value}
                    onValueChange={(value) => {
                      if (onAdditionalFilterChange) {
                        onAdditionalFilterChange('rentalSale', value);
                      } else {
                        rentalSaleFilter.onChange(value);
                        trackFeatureUsage('filter', undefined, { filter_type: 'rentalSale', value });
                      }
                    }}
                  >
                    <DropdownMenuRadioItem value="all">הכל</DropdownMenuRadioItem>
                    {rentalSaleFilter.options.map(option => (
                      <DropdownMenuRadioItem key={option.value} value={option.value}>
                        {option.label}
                      </DropdownMenuRadioItem>
                    ))}
                  </DropdownMenuRadioGroup>
                </DropdownMenuContent>
              </DropdownMenu>
            )}

            {(priceMinFilter || priceMaxFilter) && (
              <Popover open={pricePopoverOpen} onOpenChange={setPricePopoverOpen}>
                <PopoverTrigger asChild>
                  <Button
                    type="button"
                    variant={priceHasValue ? 'default' : 'outline'}
                    size="sm"
                    className="h-10 rounded-full px-4 flex items-center gap-2 flex-shrink-0"
                  >
                    <span>{priceButtonText}</span>
                    <ChevronDown className="h-4 w-4 rtl:rotate-180" aria-hidden="true" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent
                  {...QUICK_FILTER_POPOVER_PROPS}
                  className={QUICK_FILTER_POPOVER_CLASSNAME}
                  style={{ direction: "rtl" }}
                >
                  <div className="flex flex-col gap-3">
                    <div className="grid grid-cols-2 gap-2">
                      {priceMinFilter && (
                        <div className="space-y-1">
                          <Label htmlFor="quick-price-min" className="text-xs text-muted-foreground">
                            מחיר מינימלי
                          </Label>
                          <Input
                            id="quick-price-min"
                            type="number"
                            inputMode="numeric"
                            dir="ltr"
                            className="text-left"
                            value={priceMinFilter.value ?? ''}
                            placeholder={priceMinFilter.placeholder ?? '₪'}
                            onChange={(event) => {
                              const parsed = event.target.value ? Number(event.target.value) : undefined;
                              priceMinFilter.onChange(parsed);
                              trackFeatureUsage('filter', undefined, {
                                filter_type: priceMinFilter.analyticsKey ?? 'price_min',
                                value: parsed ?? 'clear',
                              });
                            }}
                          />
                        </div>
                      )}
                      {priceMaxFilter && (
                        <div className="space-y-1">
                          <Label htmlFor="quick-price-max" className="text-xs text-muted-foreground">
                            מחיר מקסימלי
                          </Label>
                          <Input
                            id="quick-price-max"
                            type="number"
                            inputMode="numeric"
                            dir="ltr"
                            className="text-left"
                            value={priceMaxFilter.value ?? ''}
                            placeholder={priceMaxFilter.placeholder ?? '₪'}
                            onChange={(event) => {
                              const parsed = event.target.value ? Number(event.target.value) : undefined;
                              priceMaxFilter.onChange(parsed);
                              trackFeatureUsage('filter', undefined, {
                                filter_type: priceMaxFilter.analyticsKey ?? 'price_max',
                                value: parsed ?? 'clear',
                              });
                            }}
                          />
                        </div>
                      )}
                    </div>
                    <div className="flex justify-between gap-2">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          if (priceMinFilter) {
                            priceMinFilter.onChange(undefined);
                            trackFeatureUsage('filter', undefined, {
                              filter_type: priceMinFilter.analyticsKey ?? 'price_min',
                              value: 'clear',
                            });
                          }
                          if (priceMaxFilter) {
                            priceMaxFilter.onChange(undefined);
                            trackFeatureUsage('filter', undefined, {
                              filter_type: priceMaxFilter.analyticsKey ?? 'price_max',
                              value: 'clear',
                            });
                          }
                        }}
                      >
                        נקה
                      </Button>
                      <Button type="button" variant="secondary" size="sm" onClick={() => setPricePopoverOpen(false)}>
                        סגור
                      </Button>
                    </div>
                  </div>
                </PopoverContent>
              </Popover>
            )}

            {(areaMinFilter || areaMaxFilter) && (
              <Popover open={areaPopoverOpen} onOpenChange={setAreaPopoverOpen}>
                <PopoverTrigger asChild>
                  <Button
                    type="button"
                    variant={areaHasValue ? 'default' : 'outline'}
                    size="sm"
                    className="h-10 rounded-full px-4 flex items-center gap-2 flex-shrink-0"
                  >
                    <span>{areaButtonText}</span>
                    <ChevronDown className="h-4 w-4 rtl:rotate-180" aria-hidden="true" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent
                  {...QUICK_FILTER_POPOVER_PROPS}
                  className={QUICK_FILTER_POPOVER_CLASSNAME}
                  style={{ direction: "rtl" }}
                >
                  <div className="flex flex-col gap-3">
                    <div className="grid grid-cols-2 gap-2">
                      {areaMinFilter && (
                        <div className="space-y-1">
                          <Label htmlFor="quick-area-min" className="text-xs text-muted-foreground">
                            שטח מינימלי
                          </Label>
                          <Input
                            id="quick-area-min"
                            type="number"
                            inputMode="numeric"
                            dir="ltr"
                            className="text-left"
                            value={areaMinFilter.value ?? ''}
                            placeholder={areaMinFilter.placeholder ?? 'מ"ר'}
                            onChange={(event) => {
                              const parsed = event.target.value ? Number(event.target.value) : undefined;
                              areaMinFilter.onChange(parsed);
                              trackFeatureUsage('filter', undefined, {
                                filter_type: areaMinFilter.analyticsKey ?? 'area_min',
                                value: parsed ?? 'clear',
                              });
                            }}
                          />
                        </div>
                      )}
                      {areaMaxFilter && (
                        <div className="space-y-1">
                          <Label htmlFor="quick-area-max" className="text-xs text-muted-foreground">
                            שטח מקסימלי
                          </Label>
                          <Input
                            id="quick-area-max"
                            type="number"
                            inputMode="numeric"
                            dir="ltr"
                            className="text-left"
                            value={areaMaxFilter.value ?? ''}
                            placeholder={areaMaxFilter.placeholder ?? 'מ"ר'}
                            onChange={(event) => {
                              const parsed = event.target.value ? Number(event.target.value) : undefined;
                              areaMaxFilter.onChange(parsed);
                              trackFeatureUsage('filter', undefined, {
                                filter_type: areaMaxFilter.analyticsKey ?? 'area_max',
                                value: parsed ?? 'clear',
                              });
                            }}
                          />
                        </div>
                      )}
                    </div>
                    <div className="flex justify-between gap-2">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          if (areaMinFilter) {
                            areaMinFilter.onChange(undefined);
                            trackFeatureUsage('filter', undefined, {
                              filter_type: areaMinFilter.analyticsKey ?? 'area_min',
                              value: 'clear',
                            });
                          }
                          if (areaMaxFilter) {
                            areaMaxFilter.onChange(undefined);
                            trackFeatureUsage('filter', undefined, {
                              filter_type: areaMaxFilter.analyticsKey ?? 'area_max',
                              value: 'clear',
                            });
                          }
                        }}
                      >
                        נקה
                      </Button>
                      <Button type="button" variant="secondary" size="sm" onClick={() => setAreaPopoverOpen(false)}>
                        סגור
                      </Button>
                    </div>
                  </div>
                </PopoverContent>
              </Popover>
            )}

            {typeFilter && typeFilter.options.length > 0 && (
              <DropdownMenu open={typeMenuOpen} onOpenChange={setTypeMenuOpen}>
                <DropdownMenuTrigger asChild>
                  <Button
                    type="button"
                    variant={typeHasValue ? 'default' : 'outline'}
                    size="sm"
                    className="h-10 rounded-full px-4 flex items-center gap-2 flex-shrink-0"
                  >
                    <span>{typeButtonText}</span>
                    <ChevronDown className="h-4 w-4 rtl:rotate-180" aria-hidden="true" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48" style={{ direction: "rtl" }}>
                  <DropdownMenuLabel className="text-xs text-muted-foreground">בחר סוג נכס</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuRadioGroup
                    value={typeFilter.value}
                    onValueChange={(value) => {
                      typeFilter.onChange(value);
                      trackFeatureUsage('filter', undefined, {
                        filter_type: typeFilter.analyticsKey ?? 'type',
                        value,
                      });
                    }}
                  >
                    <DropdownMenuRadioItem value="all">הכל</DropdownMenuRadioItem>
                    {typeFilter.options.map(option => (
                      <DropdownMenuRadioItem key={option} value={option}>
                        {option}
                      </DropdownMenuRadioItem>
                    ))}
                  </DropdownMenuRadioGroup>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
            <Sheet open={filtersOpen} onOpenChange={setFiltersOpen}>
              <SheetTrigger asChild>
                <Button variant="outline" size="sm" className="h-10 rounded-full px-4 flex items-center gap-2 flex-shrink-0">
                  <Filter className="h-4 w-4" />
                  <span className="hidden sm:inline">סינון</span>
                  {hasActiveFilters && (
                    <Badge variant="secondary" className="h-5 w-5 p-0 flex items-center justify-center text-xs">
                      !
                    </Badge>
                  )}
                </Button>
              </SheetTrigger>
                <SheetContent className="w-80" side="right">
                  <SheetHeader>
                    <SheetTitle>אפשרויות סינון</SheetTitle>
                  </SheetHeader>
                  <div className="space-y-3 max-h-[calc(100vh-120px)] overflow-y-auto pe-2">
                    <div className="flex items-center justify-between rtl:flex-row-reverse">
                      {hasActiveFilters && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={clearAllFilters}
                          className="h-8 rounded-full px-3"
                        >
                          <X className="h-3 w-3 me-1" />
                          נקה הכל
                        </Button>
                      )}
                    </div>

                    {/* My Assets Checkbox - Prominent at top */}
                    {userAssetsAdditionalFilter && (
                      <div className="flex items-center space-x-2 p-3 bg-muted/50 rounded-lg border rtl:flex-row-reverse rtl:space-x-reverse">
                        <input
                          type="checkbox"
                          id="my-assets-checkbox"
                          checked={userAssetsAdditionalFilter?.value === 'mine'}
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
                      {cityFilter && (cityFilter.alwaysVisible || cityFilter.options.length > 0) && (
                        <div className="space-y-1">
                          <Label htmlFor="city-filter" className="text-sm">
                            {cityFilter.label ?? 'עיר'}
                          </Label>
                          <Select
                            value={cityFilter.value}
                            onValueChange={(value) => {
                              cityFilter.onChange(value);
                              trackFeatureUsage('filter', undefined, {
                                filter_type: cityFilter.analyticsKey ?? 'city',
                                value,
                              });
                            }}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder={cityFilter.placeholder ?? 'כל הערים'} />
                            </SelectTrigger>
                            <SelectContent>
                              {cityFilter.showAllOption !== false && (
                                <SelectItem value="all">{cityFilter.allLabel ?? 'כל הערים'}</SelectItem>
                              )}
                              {cityFilter.options.map((option) => (
                                <SelectItem key={option} value={option}>
                                  {option}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      )}

                      {typeFilter && (typeFilter.alwaysVisible || typeFilter.options.length > 0) && (
                        <div className="space-y-1">
                          <Label htmlFor="type-filter" className="text-sm">
                            {typeFilter.label ?? 'סוג נכס'}
                          </Label>
                          <Select
                            value={typeFilter.value}
                            onValueChange={(value) => {
                              typeFilter.onChange(value);
                              trackFeatureUsage('filter', undefined, {
                                filter_type: typeFilter.analyticsKey ?? 'type',
                                value,
                              });
                            }}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder={typeFilter.placeholder ?? 'כל הסוגים'} />
                            </SelectTrigger>
                            <SelectContent>
                              {typeFilter.showAllOption !== false && (
                                <SelectItem value="all">{typeFilter.allLabel ?? 'כל הסוגים'}</SelectItem>
                              )}
                              {typeFilter.options.map((option) => (
                                <SelectItem key={option} value={option}>
                                  {option}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      )}

                      {priceMinFilter && (
                        <div className="space-y-1">
                          <Label htmlFor="price-min" className="text-sm">
                            {priceMinFilter.label ?? 'מחיר מינימלי'}
                          </Label>
                          <Input
                            id="price-min"
                            type="number"
                            placeholder={priceMinFilter.placeholder ?? '₪'}
                            value={priceMinFilter.value ?? ""}
                            dir="ltr"
                            inputMode="numeric"
                            className="text-left"
                            onChange={(e) => {
                              const value = e.target.value ? Number(e.target.value) : undefined;
                              priceMinFilter.onChange(value);
                              trackFeatureUsage('filter', undefined, {
                                filter_type: priceMinFilter.analyticsKey ?? 'price_min',
                                value,
                              });
                            }}
                          />
                        </div>
                      )}

                      {priceMaxFilter && (
                        <div className="space-y-1">
                          <Label htmlFor="price-max" className="text-sm">
                            {priceMaxFilter.label ?? 'מחיר מקסימלי'}
                          </Label>
                          <Input
                            id="price-max"
                            type="number"
                            placeholder={priceMaxFilter.placeholder ?? '₪'}
                            value={priceMaxFilter.value ?? ""}
                            dir="ltr"
                            inputMode="numeric"
                            className="text-left"
                            onChange={(e) => {
                              const value = e.target.value ? Number(e.target.value) : undefined;
                              priceMaxFilter.onChange(value);
                              trackFeatureUsage('filter', undefined, {
                                filter_type: priceMaxFilter.analyticsKey ?? 'price_max',
                                value,
                              });
                            }}
                          />
                        </div>
                      )}

                      {pricePerSqmMinFilter && (
                        <div className="space-y-1">
                          <Label htmlFor="price-per-sqm-min" className="text-sm">
                            {pricePerSqmMinFilter.label ?? 'מחיר למ"ר מינימלי'}
                          </Label>
                          <Input
                            id="price-per-sqm-min"
                            type="number"
                            placeholder={pricePerSqmMinFilter.placeholder ?? '₪/מ²'}
                            value={pricePerSqmMinFilter.value ?? ""}
                            dir="ltr"
                            inputMode="numeric"
                            className="text-left"
                            onChange={(e) => {
                              const value = e.target.value ? Number(e.target.value) : undefined;
                              pricePerSqmMinFilter.onChange(value);
                              trackFeatureUsage('filter', undefined, {
                                filter_type: pricePerSqmMinFilter.analyticsKey ?? 'price_per_sqm_min',
                                value,
                              });
                            }}
                          />
                        </div>
                      )}

                      {pricePerSqmMaxFilter && (
                        <div className="space-y-1">
                          <Label htmlFor="price-per-sqm-max" className="text-sm">
                            {pricePerSqmMaxFilter.label ?? 'מחיר למ"ר מקסימלי'}
                          </Label>
                          <Input
                            id="price-per-sqm-max"
                            type="number"
                            placeholder={pricePerSqmMaxFilter.placeholder ?? '₪/מ²'}
                            value={pricePerSqmMaxFilter.value ?? ""}
                            dir="ltr"
                            inputMode="numeric"
                            className="text-left"
                            onChange={(e) => {
                              const value = e.target.value ? Number(e.target.value) : undefined;
                              pricePerSqmMaxFilter.onChange(value);
                              trackFeatureUsage('filter', undefined, {
                                filter_type: pricePerSqmMaxFilter.analyticsKey ?? 'price_per_sqm_max',
                                value,
                              });
                            }}
                          />
                        </div>
                      )}

                      {remainingRightsMinFilter && (
                        <div className="space-y-1">
                          <Label htmlFor="remaining-rights-min" className="text-sm">
                            {remainingRightsMinFilter.label ?? 'יתרת זכויות מינימלית'}
                          </Label>
                          <Input
                            id="remaining-rights-min"
                            type="number"
                            placeholder={remainingRightsMinFilter.placeholder ?? 'מ²'}
                            value={remainingRightsMinFilter.value ?? ""}
                            dir="ltr"
                            inputMode="numeric"
                            className="text-left"
                            onChange={(e) => {
                              const value = e.target.value ? Number(e.target.value) : undefined;
                              remainingRightsMinFilter.onChange(value);
                              trackFeatureUsage('filter', undefined, {
                                filter_type: remainingRightsMinFilter.analyticsKey ?? 'remaining_rights_min',
                                value,
                              });
                            }}
                          />
                        </div>
                      )}

                      {remainingRightsMaxFilter && (
                        <div className="space-y-1">
                          <Label htmlFor="remaining-rights-max" className="text-sm">
                            {remainingRightsMaxFilter.label ?? 'יתרת זכויות מקסימלית'}
                          </Label>
                          <Input
                            id="remaining-rights-max"
                            type="number"
                            placeholder={remainingRightsMaxFilter.placeholder ?? 'מ²'}
                            value={remainingRightsMaxFilter.value ?? ""}
                            dir="ltr"
                            inputMode="numeric"
                            className="text-left"
                            onChange={(e) => {
                              const value = e.target.value ? Number(e.target.value) : undefined;
                              remainingRightsMaxFilter.onChange(value);
                              trackFeatureUsage('filter', undefined, {
                                filter_type: remainingRightsMaxFilter.analyticsKey ?? 'remaining_rights_max',
                                value,
                              });
                            }}
                          />
                        </div>
                      )}

                      {/* Additional filters */}
                      {additionalFilters
                        .filter((filter) => filter.key !== 'userAssets')
                        .map((filter) => (
                          <div key={filter.key} className="space-y-1">
                            <Label className="text-sm">{filter.label}</Label>
                            {renderAdditionalFilterControl(filter)}
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
                                  <span className="me-2 rtl:ms-2 rtl:me-0 text-muted-foreground">({option.count})</span>
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


          </div>
        </div>

        <div
          data-testid="toolbar-actions-container"
          className="flex w-full flex-wrap items-center gap-2 justify-start rtl:flex-row-reverse lg:w-auto lg:justify-end"
        >
        {/* View mode toggle */}
        <div className="flex items-center gap-2 rtl:flex-row-reverse" dir="rtl">
          <Button
            variant={viewMode === 'table' ? 'default' : 'outline'}
            size="sm"
            onClick={() => onViewModeChange('table')}
            className="h-10 w-10 rounded-full flex items-center justify-center"
            title="תצוגת טבלה"
            aria-label="תצוגת טבלה"
          >
            <List className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'cards' ? 'default' : 'outline'}
            size="sm"
            onClick={() => onViewModeChange('cards')}
            className="h-10 w-10 rounded-full flex items-center justify-center"
            title="תצוגת כרטיסים"
            aria-label="תצוגת כרטיסים"
          >
            <Grid3X3 className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'map' ? 'default' : 'outline'}
            size="sm"
            onClick={() => onViewModeChange('map')}
            className="h-10 w-10 rounded-full flex items-center justify-center"
            title="תצוגת מפה"
            aria-label="תצוגת מפה"
          >
            <Map className="h-4 w-4" />
          </Button>
        </div>

        {/* Column selection */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className="min-h-[44px] rounded-full px-4 flex items-center gap-2 flex-shrink-0"
            >
              <Settings className="h-4 w-4" />
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
                <Search className="absolute end-2 top-1/2 transform -translate-y-1/2 h-3 w-3 text-muted-foreground" />
                <Input
                  placeholder="חיפוש עמודות..."
                  value={columnSearch}
                  onChange={(e) => setColumnSearch(e.target.value)}
                  className="pe-8 text-start text-sm h-8"
                  dir="rtl"
                />
              </div>
            </div>
            <div className="max-h-60 overflow-y-auto">
              {/* Quick actions */}
              <div className="p-2 border-b bg-muted/30">
                <div className="flex gap-2 rtl:flex-row-reverse">
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
                  {onResetColumns && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setColumnSearch('');
                        onResetColumns();
                      }}
                      className="h-6 px-2 text-xs"
                    >
                      שחזר
                    </Button>
                  )}
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
              <Button
                variant="outline"
                size="sm"
                className="min-h-[44px] rounded-full px-4 flex items-center gap-2 flex-shrink-0"
              >
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
                  {action.icon && <span className="me-2 rtl:ms-2 rtl:me-0">{action.icon}</span>}
                  {action.label}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {/* Export dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className="min-h-[44px] rounded-full px-4 flex items-center gap-2 flex-shrink-0"
            >
              <Download className="h-4 w-4" />
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
          className="min-h-[44px] rounded-full px-4 flex items-center gap-2 flex-shrink-0"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">רענן</span>
        </Button>

        {/* Add new */}
        {onAddNew && (
          <Button
            onClick={onAddNew}
            size="sm"
            className="min-h-[44px] rounded-full px-4 flex items-center gap-2 flex-shrink-0"
          >
            <Plus className="h-4 w-4" />
            <span className="hidden sm:inline">הוסף חדש</span>
          </Button>
        )}
      </div>
      </div>

      {/* Bottom row - Status and info */}
      <div className="flex flex-col sm:flex-row gap-2 sm:items-center sm:justify-between text-sm text-muted-foreground rtl:sm:flex-row-reverse">
        <div className="flex items-center gap-4 rtl:flex-row-reverse">
          <span>
            {isClient && selectedCount > 0 ? `${selectedCount} נבחרים מתוך ` : ''}
            {totalCount} פריטים
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
