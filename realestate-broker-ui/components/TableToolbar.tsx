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
  SheetDescription,
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
  MoreHorizontal,
  SlidersHorizontal,
} from "lucide-react";
import { useAnalytics } from "@/hooks/useAnalytics";
import { useMediaQuery } from "@/hooks/use-media-query";

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

const TOOLBAR_PILL_BUTTON_CLASSES =
  "h-8 sm:min-h-[44px] rounded-full px-2 sm:px-4 flex items-center gap-1 sm:gap-2 flex-shrink-0 text-xs sm:text-sm";

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

interface FilterSectionProps {
  id: string;
  title: string;
  description?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

const FilterSection = ({
  id,
  title,
  description,
  defaultOpen = false,
  children,
}: FilterSectionProps) => {
  const childArray = React.useMemo(
    () => React.Children.toArray(children).filter(Boolean),
    [children],
  );

  const [open, setOpen] = React.useState(defaultOpen);

  React.useEffect(() => {
    if (defaultOpen) {
      setOpen(true);
    }
  }, [defaultOpen]);

  if (childArray.length === 0) {
    return null;
  }

  return (
    <div className="surface-panel-muted rounded-lg overflow-hidden shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full items-center justify-between gap-2 px-3 sm:px-4 py-2.5 sm:py-3 text-sm sm:text-base font-medium hover:bg-muted/50 transition-colors"
        aria-expanded={open}
        aria-controls={`${id}-content`}
      >
        <span className="text-right">{title}</span>
        <ChevronDown
          className={`h-4 w-4 sm:h-5 sm:w-5 flex-shrink-0 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          aria-hidden="true"
        />
      </button>
      {open && (
        <div id={`${id}-content`} className="space-y-3 sm:space-y-4 px-3 sm:px-4 pb-3 sm:pb-4 pt-2">
          {description && (
            <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">{description}</p>
          )}
          {childArray.map((child, index) => (
            <React.Fragment key={index}>{child}</React.Fragment>
          ))}
        </div>
      )}
    </div>
  );
};

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
  sellerType?: {
    value: string;
    onChange: (value: string) => void;
    options: Array<{ value: string; label: string }>;
  };
  commercial?: {
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

  // Hide actions container (when actions are rendered elsewhere)
  hideActionsContainer?: boolean;

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
  disableExportAll?: boolean;
  selectedCount: number;
  totalCount: number;

  // View mode
  viewMode: 'table' | 'cards' | 'map';
  onViewModeChange: (mode: 'table' | 'cards' | 'map') => void;

  // Actions
  onRefresh: () => void;
  onAddNew?: () => void;
  loading?: boolean;
  extraActions?: React.ReactNode;
  importAction?: {
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
  };

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
  hideActionsContainer = false,
  filters,
  columns,
  onResetColumns,
  onExportSelected,
  onExportAll,
  disableExportAll = false,
  selectedCount,
  totalCount,
  viewMode,
  onViewModeChange,
  onRefresh,
  onAddNew,
  loading = false,
  extraActions,
  importAction,
  additionalFilters = [],
  onAdditionalFilterChange,
  bulkActions = [],
  statusFilters,
  dateRange,
}: TableToolbarProps) {
  const { trackFeatureUsage } = useAnalytics()
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [columnSearch, setColumnSearch] = useState('');
  const [filterSearch, setFilterSearch] = useState('');
  const [isClient, setIsClient] = useState(false);
  const columnSearchInputRef = React.useRef<HTMLInputElement>(null);
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
  const sellerTypeFilter = filters?.sellerType;
  const commercialFilter = filters?.commercial;
  const userAssetsQuickFilter = filters?.userAssets;
  const [pricePopoverOpen, setPricePopoverOpen] = useState(false);
  const [areaPopoverOpen, setAreaPopoverOpen] = useState(false);
  const [typeMenuOpen, setTypeMenuOpen] = useState(false);
  const [rentalSaleMenuOpen, setRentalSaleMenuOpen] = useState(false);
  const [sellerTypeMenuOpen, setSellerTypeMenuOpen] = useState(false);
  const [commercialMenuOpen, setCommercialMenuOpen] = useState(false);
  const [userAssetsMenuOpen, setUserAssetsMenuOpen] = useState(false);
  const { matches: isSmAndUp } = useMediaQuery("(min-width: 640px)", {
    defaultValue: true,
  });
  const [quickFiltersExpanded, setQuickFiltersExpanded] = useState(true);
  const quickFiltersBreakpointInitialized = React.useRef(false);

  React.useEffect(() => {
    if (!quickFiltersBreakpointInitialized.current) {
      quickFiltersBreakpointInitialized.current = true;
    }

    if (isSmAndUp) {
      setQuickFiltersExpanded(true);
    } else if (quickFiltersBreakpointInitialized.current) {
      setQuickFiltersExpanded(false);
    }
  }, [isSmAndUp]);

  // Handle hydration mismatch
  React.useEffect(() => {
    setIsClient(true);
  }, []);

  // Filter columns based on search - memoized to prevent re-renders that cause focus loss
  const filteredColumns = React.useMemo(() => 
    columns.filter(column =>
      column.header.toLowerCase().includes(columnSearch.toLowerCase())
    ),
    [columns, columnSearch]
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

  const sellerTypeDefaultLabel = 'סוג מפרסם';

  const sellerTypeSelectedLabel = (() => {
    if (!sellerTypeFilter || sellerTypeFilter.value === 'all') return sellerTypeDefaultLabel;
    return (
      sellerTypeFilter.options.find(option => option.value === sellerTypeFilter.value)?.label ||
      sellerTypeDefaultLabel
    );
  })();

  const commercialDefaultLabel = 'ייעוד נכס';

  const commercialSelectedLabel = (() => {
    if (!commercialFilter || commercialFilter.value === 'all') return commercialDefaultLabel;
    return (
      commercialFilter.options.find(option => option.value === commercialFilter.value)?.label ||
      commercialDefaultLabel
    );
  })();

  const userAssetsDefaultLabel = 'הנכסים שלי';

  const userAssetsSelectedLabel = (() => {
    if (!userAssetsQuickFilter) return userAssetsDefaultLabel;
    const value = userAssetsQuickFilter.value ?? 'all';
    if (!value || value === 'all') return userAssetsDefaultLabel;
    return (
      userAssetsQuickFilter.options?.find(option => option.value === value)?.label ||
      userAssetsDefaultLabel
    );
  })();

  const userAssetsValue = userAssetsQuickFilter?.value ?? userAssetsAdditionalFilter?.value;
  const userAssetsActive = Boolean(userAssetsValue && userAssetsValue !== 'all');

  const isAdditionalFilterActive = React.useCallback((filter: AdditionalFilterConfig) => {
    if (filter.type === 'number-range') {
      return filter.value.min !== undefined || filter.value.max !== undefined;
    }
    if (filter.type === 'date-range') {
      return Boolean(filter.value.from) || Boolean(filter.value.to);
    }
    if (filter.type === 'text') {
      return (filter.value ?? '').trim() !== (filter.defaultValue ?? '');
    }
    const defaultValue =
      filter.type === 'select' || filter.type === undefined
        ? filter.defaultValue ?? 'all'
        : undefined;
    return filter.value !== defaultValue;
  }, []);

  const additionalFiltersActive = additionalFilters?.some(isAdditionalFilterActive) ?? false;

  const cityValue = cityFilter?.value ?? 'all';
  const typeValue = typeFilter?.value ?? 'all';
  const priceMinValue = priceMinFilter?.value;
  const priceMaxValue = priceMaxFilter?.value;
  const pricePerSqmMinValue = pricePerSqmMinFilter?.value;
  const pricePerSqmMaxValue = pricePerSqmMaxFilter?.value;
  const areaMinValue = areaMinFilter?.value;
  const areaMaxValue = areaMaxFilter?.value;
  const remainingRightsMinValue = remainingRightsMinFilter?.value;
  const remainingRightsMaxValue = remainingRightsMaxFilter?.value;
  const rentalSaleValue = rentalSaleFilter?.value ?? 'all';
  const sellerTypeValue = sellerTypeFilter?.value ?? 'all';
  const commercialValue = commercialFilter?.value ?? 'all';
  const statusValue = statusFilters?.value ?? 'all';
  const dateRangeFrom = dateRange?.from;
  const dateRangeTo = dateRange?.to;

  // Count active filters
  const activeFilterCount = React.useMemo(() => {
    let count = 0;
    if (cityValue !== 'all') count++;
    if (typeValue !== 'all') count++;
    if (priceMinValue !== undefined) count++;
    if (priceMaxValue !== undefined) count++;
    if (pricePerSqmMinValue !== undefined) count++;
    if (pricePerSqmMaxValue !== undefined) count++;
    if (areaMinValue !== undefined) count++;
    if (areaMaxValue !== undefined) count++;
    if (remainingRightsMinValue !== undefined) count++;
    if (remainingRightsMaxValue !== undefined) count++;
    if (rentalSaleValue !== 'all') count++;
    if (sellerTypeValue !== 'all') count++;
    if (commercialValue !== 'all') count++;
    if (statusValue !== 'all') count++;
    if (dateRangeFrom || dateRangeTo) count++;
    if (userAssetsActive) count++;
    // Count active additional filters
    additionalFilters?.forEach(filter => {
      if (isAdditionalFilterActive(filter)) count++;
    });
    return count;
  }, [
    cityValue,
    typeValue,
    priceMinValue,
    priceMaxValue,
    pricePerSqmMinValue,
    pricePerSqmMaxValue,
    areaMinValue,
    areaMaxValue,
    remainingRightsMinValue,
    remainingRightsMaxValue,
    rentalSaleValue,
    sellerTypeValue,
    commercialValue,
    statusValue,
    dateRangeFrom,
    dateRangeTo,
    userAssetsActive,
    additionalFilters,
    isAdditionalFilterActive,
  ]);

  const hasActiveFilters = activeFilterCount > 0;

  const sanitizedAdditionalFilters = React.useMemo(
    () => additionalFilters.filter((filter) => filter.key !== 'userAssets'),
    [additionalFilters],
  );

  const categorizeAdditionalFilter = React.useCallback((key: string) => {
    const normalizedKey = key.toLowerCase();

    if (
      ['city', 'neighborhood', 'region', 'district', 'area_code', 'zone', 'street', 'location', 'locality'].some(
        (keyword) => normalizedKey.includes(keyword),
      )
    ) {
      return 'primary' as const;
    }

    if (['price', 'budget', 'rent', 'sqm', 'cost'].some((keyword) => normalizedKey.includes(keyword))) {
      return 'primary' as const;
    }

    if (
      [
        'room',
        'property',
        'floor',
        'size',
        'area',
        'rights',
        'feature',
        'amenity',
        'parking',
        'garden',
        'balcony',
        'antenna',
        'condition',
        'age',
        'renovated',
        'renovation',
        'furnished',
        'furniture',
        'elevator',
      ].some((keyword) => normalizedKey.includes(keyword))
    ) {
      return 'property' as const;
    }

    if (
      ['listing', 'deal', 'transaction', 'source', 'status', 'availability', 'user', 'ad', 'channel'].some(
        (keyword) => normalizedKey.includes(keyword),
      )
    ) {
      return 'transaction' as const;
    }

    return 'advanced' as const;
  }, []);

  const groupedAdditionalFilters = React.useMemo(
    () =>
      sanitizedAdditionalFilters.reduce<{
        primary: AdditionalFilterConfig[];
        property: AdditionalFilterConfig[];
        transaction: AdditionalFilterConfig[];
        advanced: AdditionalFilterConfig[];
      }>(
        (acc, filter) => {
          const group = categorizeAdditionalFilter(filter.key);
          acc[group].push(filter);
          return acc;
        },
        {
          primary: [],
          property: [],
          transaction: [],
          advanced: [],
        },
      ),
    [categorizeAdditionalFilter, sanitizedAdditionalFilters],
  );

  const primaryAdditionalFilters = groupedAdditionalFilters.primary;
  const propertyAdditionalFilters = groupedAdditionalFilters.property;
  const transactionAdditionalFilters = groupedAdditionalFilters.transaction;
  const advancedAdditionalFilters = groupedAdditionalFilters.advanced;

  // Filter individual filters within sections based on search
  const filterAdditionalFilters = React.useCallback((filters: AdditionalFilterConfig[]) => {
    if (!filterSearch.trim()) {
      return filters;
    }
    const searchLower = filterSearch.toLowerCase().trim();
    return filters.filter(filter => 
      filter.label.toLowerCase().includes(searchLower)
    );
  }, [filterSearch]);

  const filteredPrimaryAdditionalFilters = React.useMemo(
    () => filterAdditionalFilters(primaryAdditionalFilters),
    [primaryAdditionalFilters, filterAdditionalFilters]
  );

  const filteredPropertyAdditionalFilters = React.useMemo(
    () => filterAdditionalFilters(propertyAdditionalFilters),
    [propertyAdditionalFilters, filterAdditionalFilters]
  );

  const filteredTransactionAdditionalFilters = React.useMemo(
    () => filterAdditionalFilters(transactionAdditionalFilters),
    [transactionAdditionalFilters, filterAdditionalFilters]
  );

  const filteredAdvancedAdditionalFilters = React.useMemo(
    () => filterAdditionalFilters(advancedAdditionalFilters),
    [advancedAdditionalFilters, filterAdditionalFilters]
  );

  // Determine which filters to use based on search
  const activePrimaryAdditionalFilters = filterSearch.trim() ? filteredPrimaryAdditionalFilters : primaryAdditionalFilters;
  const activePropertyAdditionalFilters = filterSearch.trim() ? filteredPropertyAdditionalFilters : propertyAdditionalFilters;
  const activeTransactionAdditionalFilters = filterSearch.trim() ? filteredTransactionAdditionalFilters : transactionAdditionalFilters;
  const activeAdvancedAdditionalFilters = filterSearch.trim() ? filteredAdvancedAdditionalFilters : advancedAdditionalFilters;

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
      sellerTypeFilter?.onChange('all');
      commercialFilter?.onChange('all');
      userAssetsQuickFilter?.onChange('all');
    }
  };

  const renderAdditionalFilterControl = React.useCallback((filter: AdditionalFilterConfig) => {
    const track = (metadata: Record<string, any>) =>
      trackFeatureUsage('filter', undefined, {
        filter_type: filter.analyticsKey ?? filter.key,
        ...metadata,
      });

    if (filter.type === 'number-range') {
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs sm:text-sm text-muted-foreground">מינימום</Label>
            <Input
              type="number"
              value={filter.value.min ?? ''}
              placeholder={filter.minPlaceholder ?? ''}
              step={filter.step}
              inputMode="numeric"
              className="text-left h-9 sm:h-10 text-sm sm:text-base"
              onChange={(e) => {
                const parsed = e.target.value ? Number(e.target.value) : undefined;
                onAdditionalFilterChange?.(filter.key, { ...filter.value, min: parsed });
                track({ value: parsed ?? 'clear', suffix: 'min' });
              }}
              aria-label={`${filter.label} - מינימום`}
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs sm:text-sm text-muted-foreground">מקסימום</Label>
            <Input
              type="number"
              value={filter.value.max ?? ''}
              placeholder={filter.maxPlaceholder ?? ''}
              step={filter.step}
              inputMode="numeric"
              className="text-left h-9 sm:h-10 text-sm sm:text-base"
              onChange={(e) => {
                const parsed = e.target.value ? Number(e.target.value) : undefined;
                onAdditionalFilterChange?.(filter.key, { ...filter.value, max: parsed });
                track({ value: parsed ?? 'clear', suffix: 'max' });
              }}
              aria-label={`${filter.label} - מקסימום`}
            />
          </div>
        </div>
      );
    }

    if (filter.type === 'date-range') {
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs sm:text-sm text-muted-foreground">מתאריך</Label>
            <Input
              type="date"
              value={filter.value.from ?? ''}
              placeholder={filter.fromPlaceholder}
              className="h-9 sm:h-10 text-sm sm:text-base"
              onChange={(e) => {
                const value = e.target.value || undefined;
                onAdditionalFilterChange?.(filter.key, { ...filter.value, from: value });
                track({ value: value ?? 'clear', suffix: 'from' });
              }}
              aria-label={`${filter.label} - מתאריך`}
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs sm:text-sm text-muted-foreground">עד תאריך</Label>
            <Input
              type="date"
              value={filter.value.to ?? ''}
              placeholder={filter.toPlaceholder}
              className="h-9 sm:h-10 text-sm sm:text-base"
              onChange={(e) => {
                const value = e.target.value || undefined;
                onAdditionalFilterChange?.(filter.key, { ...filter.value, to: value });
                track({ value: value ?? 'clear', suffix: 'to' });
              }}
              aria-label={`${filter.label} - עד תאריך`}
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
          className="h-9 sm:h-10 text-sm sm:text-base"
          onChange={(e) => {
            const value = e.target.value;
            onAdditionalFilterChange?.(filter.key, value);
            track({ value });
          }}
          aria-label={filter.label}
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
        <SelectTrigger className="h-9 sm:h-10 text-sm sm:text-base">
          <SelectValue placeholder={filter.placeholder ?? `בחר ${filter.label.toLowerCase()}`} />
        </SelectTrigger>
        <SelectContent className="z-[110]">
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
    );
  }, [trackFeatureUsage, onAdditionalFilterChange]);

  const primarySectionItems = React.useMemo<Array<{ key: string; node: React.ReactNode; searchText?: string }>>(() => {
    const items: Array<{ key: string; node: React.ReactNode; searchText?: string }> = [];
    const primaryLocationNodes: React.ReactNode[] = [];

    if (cityFilter && (cityFilter.alwaysVisible || cityFilter.options.length > 0)) {
      primaryLocationNodes.push(
        <div key="city-filter" className="space-y-1.5 sm:space-y-2">
          <Label htmlFor="city-filter" className="text-sm sm:text-base font-medium">
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
            <SelectTrigger className="h-9 sm:h-10 text-sm sm:text-base">
              <SelectValue placeholder={cityFilter.placeholder ?? 'כל הערים'} />
            </SelectTrigger>
            <SelectContent className="z-[110]">
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
        </div>,
      );
    }

    activePrimaryAdditionalFilters.forEach((filter) => {
      primaryLocationNodes.push(
        <div key={`primary-${filter.key}`} className="space-y-1.5 sm:space-y-2">
          <Label className="text-sm sm:text-base font-medium">{filter.label}</Label>
          {renderAdditionalFilterControl(filter)}
        </div>,
      );
    });

    if (primaryLocationNodes.length > 0) {
      const locationSearchText = [
        cityFilter?.label ?? 'עיר',
        ...activePrimaryAdditionalFilters.map(f => f.label)
      ].join(' ');
      
      items.push({
        key: 'primary-location',
        node: <div className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-2">{primaryLocationNodes}</div>,
        searchText: locationSearchText,
      });
    }

    if (priceMinFilter || priceMaxFilter) {
      const budgetSearchText = [
        'תקציב', // legend text
        priceMinFilter?.label,
        priceMaxFilter?.label
      ].filter(Boolean).join(' ');
      
      items.push({
        key: 'primary-budget',
        searchText: budgetSearchText,
        node: (
          <fieldset className="space-y-2 sm:space-y-3">
            <legend className="text-sm sm:text-base font-medium text-foreground">תקציב</legend>
            <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
              בחר טווח מחיר כדי לצמצם תוצאות שלא מתאימות למסגרת התקציב שלך.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3">
              {priceMinFilter && (
                <div className="space-y-1.5">
                  <Label htmlFor="price-min" className="text-sm sm:text-base">
                    {priceMinFilter.label ?? 'מחיר מינימלי'}
                  </Label>
                  <Input
                    id="price-min"
                    type="number"
                    placeholder={priceMinFilter.placeholder ?? '₪'}
                    value={priceMinFilter.value ?? ''}
                    dir="ltr"
                    inputMode="numeric"
                    className="text-left h-9 sm:h-10 text-sm sm:text-base"
                    onChange={(e) => {
                      const value = e.target.value ? Number(e.target.value) : undefined;
                      priceMinFilter.onChange(value);
                      trackFeatureUsage('filter', undefined, {
                        filter_type: priceMinFilter.analyticsKey ?? 'price_min',
                        value,
                      });
                    }}
                    aria-label={priceMinFilter.label ?? 'מחיר מינימלי'}
                  />
                </div>
              )}
              {priceMaxFilter && (
                <div className="space-y-1.5">
                  <Label htmlFor="price-max" className="text-sm sm:text-base">
                    {priceMaxFilter.label ?? 'מחיר מקסימלי'}
                  </Label>
                  <Input
                    id="price-max"
                    type="number"
                    placeholder={priceMaxFilter.placeholder ?? '₪'}
                    value={priceMaxFilter.value ?? ''}
                    dir="ltr"
                    inputMode="numeric"
                    className="text-left h-9 sm:h-10 text-sm sm:text-base"
                    onChange={(e) => {
                      const value = e.target.value ? Number(e.target.value) : undefined;
                      priceMaxFilter.onChange(value);
                      trackFeatureUsage('filter', undefined, {
                        filter_type: priceMaxFilter.analyticsKey ?? 'price_max',
                        value,
                      });
                    }}
                    aria-label={priceMaxFilter.label ?? 'מחיר מקסימלי'}
                  />
                </div>
              )}
            </div>
          </fieldset>
        ),
      });
    }

    return items;
  }, [cityFilter, activePrimaryAdditionalFilters, priceMinFilter, priceMaxFilter, trackFeatureUsage, renderAdditionalFilterControl]);

  const propertySectionItems = React.useMemo<Array<{ key: string; node: React.ReactNode; searchText?: string }>>(() => {
    const items: Array<{ key: string; node: React.ReactNode; searchText?: string }> = [];

    if (typeFilter && (typeFilter.alwaysVisible || typeFilter.options.length > 0)) {
      items.push({
        key: 'property-type',
        searchText: typeFilter.label ?? 'סוג נכס',
        node: (
          <div className="space-y-1.5 sm:space-y-2">
            <Label htmlFor="type-filter" className="text-sm sm:text-base font-medium">
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
              <SelectTrigger className="h-9 sm:h-10 text-sm sm:text-base">
                <SelectValue placeholder={typeFilter.placeholder ?? 'כל הסוגים'} />
              </SelectTrigger>
              <SelectContent className="z-[110]">
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
        ),
      });
    }

    if (areaMinFilter || areaMaxFilter) {
      const areaSearchText = [
        'גודל הנכס', // legend text
        areaMinFilter?.label,
        areaMaxFilter?.label
      ].filter(Boolean).join(' ');
      
      items.push({
        key: 'property-area',
        searchText: areaSearchText,
        node: (
          <fieldset className="space-y-2 sm:space-y-3">
            <legend className="text-sm sm:text-base font-medium text-foreground">גודל הנכס</legend>
            <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
              ציין טווח שטח כדי להתמקד בנכסים בגודל המתאים.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3">
              {areaMinFilter && (
                <div className="space-y-1.5">
                  <Label htmlFor="area-min" className="text-sm sm:text-base">
                    שטח מינימלי
                  </Label>
                  <Input
                    id="area-min"
                    type="number"
                    inputMode="numeric"
                    dir="ltr"
                    className="text-left h-9 sm:h-10 text-sm sm:text-base"
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
                    aria-label="שטח מינימלי"
                  />
                </div>
              )}
              {areaMaxFilter && (
                <div className="space-y-1.5">
                  <Label htmlFor="area-max" className="text-sm sm:text-base">
                    שטח מקסימלי
                  </Label>
                  <Input
                    id="area-max"
                    type="number"
                    inputMode="numeric"
                    dir="ltr"
                    className="text-left h-9 sm:h-10 text-sm sm:text-base"
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
                    aria-label="שטח מקסימלי"
                  />
                </div>
              )}
            </div>
          </fieldset>
        ),
      });
    }

    if (activePropertyAdditionalFilters.length > 0) {
      const propertyAdditionalSearchText = activePropertyAdditionalFilters.map(f => f.label).join(' ');
      
      items.push({
        key: 'property-additional',
        searchText: propertyAdditionalSearchText,
        node: (
          <div className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-2">
            {activePropertyAdditionalFilters.map((filter) => (
              <div key={`property-${filter.key}`} className="space-y-1.5 sm:space-y-2">
                <Label className="text-sm sm:text-base font-medium">{filter.label}</Label>
                {renderAdditionalFilterControl(filter)}
              </div>
            ))}
          </div>
        ),
      });
    }

    return items;
  }, [typeFilter, areaMinFilter, areaMaxFilter, activePropertyAdditionalFilters, trackFeatureUsage, renderAdditionalFilterControl]);

  const transactionSectionItems = React.useMemo<Array<{ key: string; node: React.ReactNode; searchText?: string }>>(() => {
    const items: Array<{ key: string; node: React.ReactNode; searchText?: string }> = [];

    if (activeTransactionAdditionalFilters.length > 0) {
      const transactionAdditionalSearchText = activeTransactionAdditionalFilters.map(f => f.label).join(' ');
      
      items.push({
        key: 'transaction-additional',
        searchText: transactionAdditionalSearchText,
        node: (
          <div className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-2">
            {activeTransactionAdditionalFilters.map((filter) => (
              <div key={`transaction-${filter.key}`} className="space-y-1.5 sm:space-y-2">
                <Label className="text-sm sm:text-base font-medium">{filter.label}</Label>
                {renderAdditionalFilterControl(filter)}
              </div>
            ))}
          </div>
        ),
      });
    }

    if (statusFilters) {
      items.push({
        key: 'transaction-status',
        searchText: 'סטטוס',
        node: (
          <div className="space-y-1.5 sm:space-y-2">
            <Label className="text-sm sm:text-base font-medium">סטטוס</Label>
            <Select value={statusFilters.value} onValueChange={statusFilters.onChange}>
              <SelectTrigger className="h-9 sm:h-10 text-sm sm:text-base">
                <SelectValue placeholder="כל הסטטוסים" />
              </SelectTrigger>
              <SelectContent className="z-[110]">
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
        ),
      });
    }

    if (dateRange) {
      items.push({
        key: 'transaction-date-range',
        searchText: 'טווח תאריכים תאריך',
        node: (
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
                  aria-label="טווח תאריכים - מתאריך"
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
                  aria-label="טווח תאריכים - עד תאריך"
                />
              </div>
            </div>
          </div>
        ),
      });
    }

    return items;
  }, [activeTransactionAdditionalFilters, statusFilters, dateRange, renderAdditionalFilterControl]);

  const advancedSectionItems = React.useMemo<Array<{ key: string; node: React.ReactNode; searchText?: string }>>(() => {
    const items: Array<{ key: string; node: React.ReactNode; searchText?: string }> = [];

    if (pricePerSqmMinFilter || pricePerSqmMaxFilter) {
      const pricePerSqmSearchText = [
        'מחיר למ״ר', // legend text
        pricePerSqmMinFilter?.label,
        pricePerSqmMaxFilter?.label
      ].filter(Boolean).join(' ');
      
      items.push({
        key: 'advanced-price-per-sqm',
        searchText: pricePerSqmSearchText,
        node: (
          <fieldset className="space-y-2">
            <legend className="text-sm font-medium text-foreground">מחיר למ״ר</legend>
            <div className="grid grid-cols-2 gap-2">
              {pricePerSqmMinFilter && (
                <div className="space-y-1">
                  <Label htmlFor="price-per-sqm-min" className="text-sm">
                    {pricePerSqmMinFilter.label ?? 'מחיר למ״ר מינימלי'}
                  </Label>
                  <Input
                    id="price-per-sqm-min"
                    type="number"
                    placeholder={pricePerSqmMinFilter.placeholder ?? '₪/מ״²'}
                    value={pricePerSqmMinFilter.value ?? ''}
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
                    aria-label={pricePerSqmMinFilter.label ?? 'מחיר למ״ר מינימלי'}
                  />
                </div>
              )}
              {pricePerSqmMaxFilter && (
                <div className="space-y-1">
                  <Label htmlFor="price-per-sqm-max" className="text-sm">
                    {pricePerSqmMaxFilter.label ?? 'מחיר למ״ר מקסימלי'}
                  </Label>
                  <Input
                    id="price-per-sqm-max"
                    type="number"
                    placeholder={pricePerSqmMaxFilter.placeholder ?? '₪/מ״²'}
                    value={pricePerSqmMaxFilter.value ?? ''}
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
                    aria-label={pricePerSqmMaxFilter.label ?? 'מחיר למ״ר מקסימלי'}
                  />
                </div>
              )}
            </div>
          </fieldset>
        ),
      });
    }

    if (remainingRightsMinFilter || remainingRightsMaxFilter) {
      const remainingRightsSearchText = [
        'יתרת זכויות', // legend text
        remainingRightsMinFilter?.label,
        remainingRightsMaxFilter?.label
      ].filter(Boolean).join(' ');
      
      items.push({
        key: 'advanced-remaining-rights',
        searchText: remainingRightsSearchText,
        node: (
          <fieldset className="space-y-2">
            <legend className="text-sm font-medium text-foreground">יתרת זכויות</legend>
            <div className="grid grid-cols-2 gap-2">
              {remainingRightsMinFilter && (
                <div className="space-y-1">
                  <Label htmlFor="remaining-rights-min" className="text-sm">
                    {remainingRightsMinFilter.label ?? 'יתרת זכויות מינימלית'}
                  </Label>
                  <Input
                    id="remaining-rights-min"
                    type="number"
                    placeholder={remainingRightsMinFilter.placeholder ?? 'מ²'}
                    value={remainingRightsMinFilter.value ?? ''}
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
                    aria-label={remainingRightsMinFilter.label ?? 'יתרת זכויות מינימלית'}
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
                    value={remainingRightsMaxFilter.value ?? ''}
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
                    aria-label={remainingRightsMaxFilter.label ?? 'יתרת זכויות מקסימלית'}
                  />
                </div>
              )}
            </div>
          </fieldset>
        ),
      });
    }

    if (activeAdvancedAdditionalFilters.length > 0) {
      const advancedAdditionalSearchText = activeAdvancedAdditionalFilters.map(f => f.label).join(' ');
      
      items.push({
        key: 'advanced-additional',
        searchText: advancedAdditionalSearchText,
        node: (
          <div className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-2">
            {activeAdvancedAdditionalFilters.map((filter) => (
              <div key={`advanced-${filter.key}`} className="space-y-1.5 sm:space-y-2">
                <Label className="text-sm sm:text-base font-medium">{filter.label}</Label>
                {renderAdditionalFilterControl(filter)}
              </div>
            ))}
          </div>
        ),
      });
    }

    return items;
  }, [pricePerSqmMinFilter, pricePerSqmMaxFilter, remainingRightsMinFilter, remainingRightsMaxFilter, activeAdvancedAdditionalFilters, trackFeatureUsage, renderAdditionalFilterControl]);

  // Helper to check if section has matching filters for search
  const sectionHasMatchingFilters = React.useCallback((sectionItems: Array<{ key: string; node: React.ReactNode; searchText?: string }>, sectionTitle: string): boolean => {
    if (!filterSearch.trim()) return false;
    const searchLower = filterSearch.toLowerCase().trim();
    if (sectionTitle.toLowerCase().includes(searchLower)) return true;
    return sectionItems.some(({ searchText }) => 
      searchText && searchText.toLowerCase().includes(searchLower)
    );
  }, [filterSearch]);

  const propertySectionDefaultOpen =
    propertySectionItems.length > 0 &&
    (sectionHasMatchingFilters(propertySectionItems, 'מאפייני נכס') ||
      typeHasValue ||
      areaHasValue ||
      propertyAdditionalFilters.some(isAdditionalFilterActive));

  const transactionSectionDefaultOpen =
    transactionSectionItems.length > 0 &&
    (sectionHasMatchingFilters(transactionSectionItems, 'סטטוס ומקור') ||
      (statusFilters && statusFilters.value !== 'all') ||
      Boolean(dateRange && (dateRange.from || dateRange.to)) ||
      transactionAdditionalFilters.some(isAdditionalFilterActive));

  const advancedSectionDefaultOpen =
    advancedSectionItems.length > 0 &&
    (sectionHasMatchingFilters(advancedSectionItems, 'סינון מתקדם') ||
      (pricePerSqmMinFilter && pricePerSqmMinFilter.value !== undefined) ||
      (pricePerSqmMaxFilter && pricePerSqmMaxFilter.value !== undefined) ||
      (remainingRightsMinFilter && remainingRightsMinFilter.value !== undefined) ||
      (remainingRightsMaxFilter && remainingRightsMaxFilter.value !== undefined) ||
      advancedAdditionalFilters.some(isAdditionalFilterActive));

  // Filter sections based on search query - searches through filter labels
  const filterSectionBySearch = React.useCallback((sectionItems: Array<{ key: string; node: React.ReactNode; searchText?: string }>, sectionTitle: string) => {
    if (!filterSearch.trim()) {
      return sectionItems;
    }

    const searchLower = filterSearch.toLowerCase().trim();
    const sectionTitleMatches = sectionTitle.toLowerCase().includes(searchLower);

    // Check if section title matches
    if (sectionTitleMatches) {
      return sectionItems;
    }

    // Filter items by checking if their searchText (which contains all filter labels) contains the search term
    return sectionItems.filter(({ searchText }) => {
      if (!searchText) return false;
      return searchText.toLowerCase().includes(searchLower);
    });
  }, [filterSearch]);

  const filteredPrimarySectionItems = React.useMemo(
    () => filterSectionBySearch(primarySectionItems, 'מיקום ותקציב'),
    [primarySectionItems, filterSectionBySearch]
  );

  const filteredPropertySectionItems = React.useMemo(
    () => filterSectionBySearch(propertySectionItems, 'מאפייני נכס'),
    [propertySectionItems, filterSectionBySearch]
  );

  const filteredTransactionSectionItems = React.useMemo(
    () => filterSectionBySearch(transactionSectionItems, 'סטטוס ומקור'),
    [transactionSectionItems, filterSectionBySearch]
  );

  const filteredAdvancedSectionItems = React.useMemo(
    () => filterSectionBySearch(advancedSectionItems, 'סינון מתקדם'),
    [advancedSectionItems, filterSectionBySearch]
  );

  // Count total number of individual filters (not section items)
  const totalFilterCount = React.useMemo(() => {
    let count = 0;
    // Count individual filters in primary section
    if (cityFilter && (cityFilter.alwaysVisible || cityFilter.options.length > 0)) count++;
    count += primaryAdditionalFilters.length;
    if (priceMinFilter || priceMaxFilter) count += (priceMinFilter ? 1 : 0) + (priceMaxFilter ? 1 : 0);
    
    // Count individual filters in property section
    if (typeFilter && (typeFilter.alwaysVisible || typeFilter.options.length > 0)) count++;
    if (areaMinFilter || areaMaxFilter) count += (areaMinFilter ? 1 : 0) + (areaMaxFilter ? 1 : 0);
    count += propertyAdditionalFilters.length;
    
    // Count individual filters in transaction section
    count += transactionAdditionalFilters.length;
    if (statusFilters) count++;
    if (dateRange) count++;
    
    // Count individual filters in advanced section
    if (pricePerSqmMinFilter || pricePerSqmMaxFilter) count += (pricePerSqmMinFilter ? 1 : 0) + (pricePerSqmMaxFilter ? 1 : 0);
    if (remainingRightsMinFilter || remainingRightsMaxFilter) count += (remainingRightsMinFilter ? 1 : 0) + (remainingRightsMaxFilter ? 1 : 0);
    count += advancedAdditionalFilters.length;
    
    // Count userAssetsAdditionalFilter if present
    if (userAssetsAdditionalFilter) count++;
    
    return count;
  }, [
    cityFilter, priceMinFilter, priceMaxFilter, primaryAdditionalFilters.length,
    typeFilter, areaMinFilter, areaMaxFilter, propertyAdditionalFilters.length,
    transactionAdditionalFilters.length, statusFilters, dateRange,
    pricePerSqmMinFilter, pricePerSqmMaxFilter, remainingRightsMinFilter, remainingRightsMaxFilter,
    advancedAdditionalFilters.length, userAssetsAdditionalFilter
  ]);

  const shouldShowFilterSearch = totalFilterCount > 10;

  return (
    <div className="flex flex-col gap-2 p-2 sm:gap-3 sm:p-3 md:p-4 bg-muted/30 rtl" dir="rtl">
      <div className="flex flex-wrap items-center gap-2 sm:gap-3" dir="rtl">
        <div className="relative flex min-w-[180px] flex-1">
          <Search className="absolute end-2 sm:end-3 top-1/2 transform -translate-y-1/2 h-3.5 w-3.5 sm:h-4 sm:w-4 text-muted-foreground" aria-hidden="true" />
          <Input
            placeholder={searchPlaceholder}
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pe-8 sm:pe-10 w-full h-9 sm:min-h-[44px] text-sm sm:text-base"
            dir="rtl"
            aria-label="חיפוש נכסים"
            aria-describedby="search-help-text"
          />
          <div id="search-help-text" className="sr-only">
            השתמש בשדה זה כדי לחפש נכסים לפי כתובת, עיר או מספר נכס
          </div>
        </div>

        <div className="ms-auto flex flex-shrink-0 items-center gap-1.5 sm:gap-2">
          {!isSmAndUp && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setQuickFiltersExpanded((previous) => !previous)}
              className="h-8 w-8 rounded-full flex items-center justify-center p-0"
              aria-expanded={quickFiltersExpanded}
              aria-controls="quick-filters-panel"
              title="מסננים"
              aria-label="מסננים"
            >
              <SlidersHorizontal className="h-3.5 w-3.5" />
            </Button>
          )}
          <Button
            variant={viewMode === 'table' ? 'default' : 'outline'}
            size="sm"
            onClick={() => onViewModeChange('table')}
            className="h-8 w-8 sm:h-10 sm:w-10 rounded-full flex items-center justify-center p-0"
            title="תצוגת טבלה"
            aria-label="תצוגת טבלה"
          >
            <List className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
          </Button>
          <Button
            variant={viewMode === 'cards' ? 'default' : 'outline'}
            size="sm"
            onClick={() => onViewModeChange('cards')}
            className="h-8 w-8 sm:h-10 sm:w-10 rounded-full flex items-center justify-center p-0"
            title="תצוגת כרטיסים"
            aria-label="תצוגת כרטיסים"
          >
            <Grid3X3 className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
          </Button>
          <Button
            variant={viewMode === 'map' ? 'default' : 'outline'}
            size="sm"
            onClick={() => onViewModeChange('map')}
            className="h-8 w-8 sm:h-10 sm:w-10 rounded-full flex items-center justify-center p-0"
            title="תצוגת מפה"
            aria-label="תצוגת מפה"
          >
            <Map className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
          </Button>
        </div>
      </div>

      {/* Quick filters and toolbar actions */}
      <div className="flex flex-col gap-2 sm:gap-3 lg:flex-row lg:items-start lg:justify-between" dir="rtl">
        <div className="lg:flex-1">
          {(isSmAndUp || quickFiltersExpanded) && (
            <div
              id="quick-filters-panel"
              data-testid="quick-filters-container"
            className="flex w-full flex-wrap items-center gap-1.5 sm:gap-2 pb-1 lg:pb-0"
          >
            {userAssetsQuickFilter && (
              <DropdownMenu open={userAssetsMenuOpen} onOpenChange={setUserAssetsMenuOpen}>
                <DropdownMenuTrigger asChild>
                  <Button
                    type="button"
                    variant={userAssetsActive ? 'default' : 'outline'}
                    size="sm"
                    className={TOOLBAR_PILL_BUTTON_CLASSES}
                    aria-pressed={userAssetsActive}
                  >
                    <span className="hidden sm:inline">{userAssetsSelectedLabel}</span>
                    <span className="sm:hidden">הנכסים שלי</span>
                    <ChevronDown className="h-3 w-3 sm:h-4 sm:w-4 rtl:rotate-180 shrink-0" aria-hidden="true" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56" style={{ direction: "rtl" }}>
                  <DropdownMenuLabel className="text-xs text-muted-foreground">בחר בעלות</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuRadioGroup
                    value={userAssetsQuickFilter.value ?? 'all'}
                    onValueChange={(value) => {
                      if (onAdditionalFilterChange) {
                        onAdditionalFilterChange('userAssets', value);
                      } else {
                        userAssetsQuickFilter.onChange(value);
                        trackFeatureUsage('filter', undefined, { filter_type: 'userAssets', value });
                      }
                    }}
                  >
                    <DropdownMenuRadioItem value="all">כל הנכסים</DropdownMenuRadioItem>
                    {(userAssetsQuickFilter.options ?? []).map(option => (
                      <DropdownMenuRadioItem key={option.value} value={option.value}>
                        {option.label}
                      </DropdownMenuRadioItem>
                    ))}
                  </DropdownMenuRadioGroup>
                </DropdownMenuContent>
              </DropdownMenu>
            )}

            {rentalSaleFilter && (
              <DropdownMenu open={rentalSaleMenuOpen} onOpenChange={setRentalSaleMenuOpen}>
                <DropdownMenuTrigger asChild>
                  <Button
                    type="button"
                    variant={rentalSaleFilter.value !== 'all' ? 'default' : 'outline'}
                    size="sm"
                    className={TOOLBAR_PILL_BUTTON_CLASSES}
                  >
                    <span className="hidden sm:inline">{rentalSaleSelectedLabel}</span>
                    <span className="sm:hidden">עיסקה</span>
                    <ChevronDown className="h-3 w-3 sm:h-4 sm:w-4 rtl:rotate-180 shrink-0" aria-hidden="true" />
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

            {sellerTypeFilter && (
              <DropdownMenu open={sellerTypeMenuOpen} onOpenChange={setSellerTypeMenuOpen}>
                <DropdownMenuTrigger asChild>
                  <Button
                    type="button"
                    variant={sellerTypeFilter.value !== 'all' ? 'default' : 'outline'}
                    size="sm"
                    className={TOOLBAR_PILL_BUTTON_CLASSES}
                  >
                    <span className="hidden sm:inline">{sellerTypeSelectedLabel}</span>
                    <span className="sm:hidden">מפרסם</span>
                    <ChevronDown className="h-3 w-3 sm:h-4 sm:w-4 rtl:rotate-180 shrink-0" aria-hidden="true" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48" style={{ direction: "rtl" }}>
                  <DropdownMenuLabel className="text-xs text-muted-foreground">בחר סוג מפרסם</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuRadioGroup
                    value={sellerTypeFilter.value}
                    onValueChange={(value) => {
                      if (onAdditionalFilterChange) {
                        onAdditionalFilterChange('sellerType', value);
                      } else {
                        sellerTypeFilter.onChange(value);
                        trackFeatureUsage('filter', undefined, { filter_type: 'sellerType', value });
                      }
                    }}
                  >
                    <DropdownMenuRadioItem value="all">הכל</DropdownMenuRadioItem>
                    {sellerTypeFilter.options.map(option => (
                      <DropdownMenuRadioItem key={option.value} value={option.value}>
                        {option.label}
                      </DropdownMenuRadioItem>
                    ))}
                  </DropdownMenuRadioGroup>
                </DropdownMenuContent>
              </DropdownMenu>
            )}

            {commercialFilter && (
              <DropdownMenu open={commercialMenuOpen} onOpenChange={setCommercialMenuOpen}>
                <DropdownMenuTrigger asChild>
                  <Button
                    type="button"
                    variant={commercialFilter.value !== 'all' ? 'default' : 'outline'}
                    size="sm"
                    className={TOOLBAR_PILL_BUTTON_CLASSES}
                  >
                    <span className="hidden sm:inline">{commercialSelectedLabel}</span>
                    <span className="sm:hidden">ייעוד</span>
                    <ChevronDown className="h-3 w-3 sm:h-4 sm:w-4 rtl:rotate-180 shrink-0" aria-hidden="true" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48" style={{ direction: "rtl" }}>
                  <DropdownMenuLabel className="text-xs text-muted-foreground">בחר ייעוד נכס</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuRadioGroup
                    value={commercialFilter.value}
                    onValueChange={(value) => {
                      if (onAdditionalFilterChange) {
                        onAdditionalFilterChange('commercial', value);
                      } else {
                        commercialFilter.onChange(value);
                        trackFeatureUsage('filter', undefined, { filter_type: 'commercial', value });
                      }
                    }}
                  >
                    <DropdownMenuRadioItem value="all">הכל</DropdownMenuRadioItem>
                    {commercialFilter.options.map(option => (
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
                    className={TOOLBAR_PILL_BUTTON_CLASSES}
                  >
                    <span className="hidden sm:inline">{priceButtonText}</span>
                    <span className="sm:hidden">מחיר</span>
                    <ChevronDown className="h-3 w-3 sm:h-4 sm:w-4 rtl:rotate-180 shrink-0" aria-hidden="true" />
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
                            aria-label="מחיר מינימלי"
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
                            aria-label="מחיר מקסימלי"
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
                    className={TOOLBAR_PILL_BUTTON_CLASSES}
                  >
                    <span className="hidden sm:inline">{areaButtonText}</span>
                    <span className="sm:hidden">שטח</span>
                    <ChevronDown className="h-3 w-3 sm:h-4 sm:w-4 rtl:rotate-180 shrink-0" aria-hidden="true" />
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
                            aria-label="שטח מינימלי"
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
                            aria-label="שטח מקסימלי"
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
                    className={TOOLBAR_PILL_BUTTON_CLASSES}
                  >
                    <span className="hidden sm:inline">{typeButtonText}</span>
                    <span className="sm:hidden">סוג נכס</span>
                    <ChevronDown className="h-3 w-3 sm:h-4 sm:w-4 rtl:rotate-180 shrink-0" aria-hidden="true" />
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

            <Sheet open={filtersOpen} onOpenChange={(open) => {
              setFiltersOpen(open);
              if (!open) {
                setFilterSearch('');
              }
            }}>
              <SheetTrigger asChild>
                <Button variant="outline" size="sm" className={TOOLBAR_PILL_BUTTON_CLASSES}>
                  <Filter className="h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0" aria-hidden="true" />
                  <span className="hidden sm:inline">סינון</span>
                  {hasActiveFilters && (
                    <Badge variant="secondary" className="h-4 min-w-4 sm:h-5 sm:min-w-5 px-1 sm:px-1.5 flex items-center justify-center text-xs shrink-0 font-semibold" aria-hidden="true">
                      {activeFilterCount}
                    </Badge>
                  )}
                </Button>
              </SheetTrigger>
                <SheetContent className="w-full sm:w-96 md:w-[420px] max-w-[95vw] overflow-hidden flex flex-col" side="right">
                  <SheetHeader className="flex-shrink-0 pb-3 sm:pb-4">
                    <SheetTitle className="text-lg sm:text-xl">אפשרויות סינון</SheetTitle>
                    <SheetDescription className="sr-only">
                      תפריט סינון מתקדם עם אפשרויות למיקום, תקציב, מאפייני נכס, סטטוס ומקור
                    </SheetDescription>
                  </SheetHeader>
                  <div className="flex-1 overflow-y-auto pe-2 -me-2 space-y-3 sm:space-y-4 pt-3 sm:pt-4">
                    {/* Filter Search - Only show if more than 10 filters */}
                    {shouldShowFilterSearch && (
                      <div className="flex-shrink-0 sticky top-0 bg-background z-10 pb-2 -mt-3 sm:-mt-4 pt-3 sm:pt-4">
                        <div className="relative">
                          <Search className="absolute end-2 sm:end-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" aria-hidden="true" />
                          <Input
                            placeholder="חיפוש מסננים..."
                            value={filterSearch}
                            onChange={(e) => setFilterSearch(e.target.value)}
                            className="pe-9 sm:pe-10 ps-9 sm:ps-10 text-sm h-9 sm:h-10 w-full"
                            dir="rtl"
                            aria-label="חיפוש מסננים"
                          />
                          {filterSearch && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setFilterSearch('')}
                              className="absolute start-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0 hover:bg-muted"
                              aria-label="נקה חיפוש"
                            >
                              <X className="h-3.5 w-3.5" />
                            </Button>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Active Filters Badge and Clear Button */}
                    {hasActiveFilters && (
                      <div className="flex-shrink-0 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-3 pb-3 mb-3">
                        <Badge variant="secondary" className="text-xs px-2 py-1 shadow-xs">
                          {activeFilterCount} סינונים פעילים
                        </Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={clearAllFilters}
                          className="h-8 rounded-full px-3 text-xs sm:text-sm w-full sm:w-auto"
                          aria-label="נקה את כל המסננים"
                        >
                          <X className="h-3.5 w-3.5 me-1.5" />
                          נקה הכל
                        </Button>
                      </div>
                    )}

                    {userAssetsAdditionalFilter && (
                      <div className="space-y-2 rounded-lg bg-muted/50 p-3 shadow-sm">
                        <Label className="text-sm font-medium">הצג נכסים לפי</Label>
                        <Select
                          value={userAssetsAdditionalFilter.value ?? 'all'}
                          onValueChange={(value) => {
                            if (onAdditionalFilterChange) {
                              onAdditionalFilterChange('userAssets', value);
                            } else {
                              userAssetsQuickFilter?.onChange(value);
                              trackFeatureUsage('filter', undefined, { filter_type: 'userAssets', value });
                            }
                          }}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="כל הנכסים" />
                          </SelectTrigger>
                          <SelectContent className="z-[110]">
                            <SelectItem value="all">כל הנכסים</SelectItem>
                            {userAssetsAdditionalFilter.options.map((option) => (
                              <SelectItem key={option.value} value={option.value}>
                                {option.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    {filteredPrimarySectionItems.length > 0 && (
                      <FilterSection
                        id="primary-filters"
                        title="מיקום ותקציב"
                        description="התחל בבחירת מיקום ותקציב כדי להתמקד בתוצאות במהירות."
                        defaultOpen={filterSearch.trim() ? sectionHasMatchingFilters(primarySectionItems, 'מיקום ותקציב') : true}
                      >
                        <div className="space-y-4">
                          {filteredPrimarySectionItems.map(({ key, node }) => (
                            <React.Fragment key={key}>{node}</React.Fragment>
                          ))}
                        </div>
                      </FilterSection>
                    )}

                    {filteredPropertySectionItems.length > 0 && (
                      <FilterSection
                        id="property-filters"
                        title="מאפייני נכס"
                        description="כוון את מאפייני הנכס כדי למצוא התאמות מדויקות יותר."
                        defaultOpen={propertySectionDefaultOpen}
                      >
                        <div className="space-y-3">
                          {filteredPropertySectionItems.map(({ key, node }) => (
                            <React.Fragment key={key}>{node}</React.Fragment>
                          ))}
                        </div>
                      </FilterSection>
                    )}

                    {filteredTransactionSectionItems.length > 0 && (
                      <FilterSection
                        id="transaction-filters"
                        title="סטטוס ומקור"
                        description="נהל את מצב הפרסום ואת מקור המודעה."
                        defaultOpen={transactionSectionDefaultOpen}
                      >
                        <div className="space-y-3">
                          {filteredTransactionSectionItems.map(({ key, node }) => (
                            <React.Fragment key={key}>{node}</React.Fragment>
                          ))}
                        </div>
                      </FilterSection>
                    )}

                    {filteredAdvancedSectionItems.length > 0 && (
                      <FilterSection
                        id="advanced-filters"
                        title="סינון מתקדם"
                        description="השתמש בקריטריונים נוספים כדי לדייק את התוצאות."
                        defaultOpen={advancedSectionDefaultOpen}
                      >
                        <div className="space-y-3">
                          {filteredAdvancedSectionItems.map(({ key, node }) => (
                            <React.Fragment key={key}>{node}</React.Fragment>
                          ))}
                        </div>
                      </FilterSection>
                    )}

                    {filterSearch.trim() && 
                     filteredPrimarySectionItems.length === 0 &&
                     filteredPropertySectionItems.length === 0 &&
                     filteredTransactionSectionItems.length === 0 &&
                     filteredAdvancedSectionItems.length === 0 && (
                      <div className="text-center py-8 text-muted-foreground">
                        <p className="text-sm">לא נמצאו מסננים התואמים לחיפוש</p>
                        <p className="text-xs mt-1">נסה לבדוק את האיות או להשתמש במילים אחרות</p>
                      </div>
                    )}
                  </div>
                </SheetContent>
              </Sheet>

              {hasActiveFilters && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearAllFilters}
                  className={TOOLBAR_PILL_BUTTON_CLASSES}
                  aria-label="נקה את כל המסננים"
                >
                  <span className="hidden sm:inline">נקה כל המסננים</span>
                  <span className="sm:hidden">נקה הכל</span>
                  <X className="h-3.5 w-3.5 sm:h-4 sm:w-4 ms-2 shrink-0" />
                </Button>
              )}
            </div>
          )}
        </div>

        {!hideActionsContainer && (
          <div
            data-testid="toolbar-actions-container"
            className="inline-flex flex-wrap items-center gap-1.5 sm:gap-2 justify-start lg:justify-end"
          >
        {/* Add new */}
        {onAddNew && (
          <Button
            onClick={onAddNew}
            size="sm"
            className={TOOLBAR_PILL_BUTTON_CLASSES}
          >
            <Plus className="h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0" aria-hidden="true" />
            <span className="hidden sm:inline">הוסף חדש</span>
          </Button>
        )}

        {/* Column selection */}
        <DropdownMenu
          onOpenChange={(open) => {
            if (open && columnSearchInputRef.current) {
              // Focus the input when dropdown opens
              setTimeout(() => {
                columnSearchInputRef.current?.focus();
              }, 0);
            } else {
              // Clear search when dropdown closes
              setColumnSearch('');
            }
          }}
        >
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className={TOOLBAR_PILL_BUTTON_CLASSES}
            >
              <Settings className="h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0" aria-hidden="true" />
              <span className="hidden sm:inline">עמודות</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent 
            align="start" 
            className="w-64 bg-white flex flex-col"
            style={{ maxHeight: 'calc(100vh - 8rem)' }}
            onEscapeKeyDown={(e) => {
              if (columnSearch) {
                // Clear search on escape if there's text
                e.preventDefault();
                setColumnSearch('');
                columnSearchInputRef.current?.focus();
              }
            }}
          >
            <DropdownMenuLabel className="bg-white text-foreground sticky top-0 z-10 bg-background border-b flex-shrink-0">
              בחר עמודות
            </DropdownMenuLabel>
            <DropdownMenuSeparator className="flex-shrink-0" />
            <div className="p-2 border-b flex-shrink-0">
              <div className="relative">
                <Search className="absolute end-2 top-1/2 transform -translate-y-1/2 h-3 w-3 text-muted-foreground" aria-hidden="true" />
                <Input
                  ref={columnSearchInputRef}
                  placeholder="חיפוש עמודות..."
                  value={columnSearch}
                  onChange={(e) => {
                    const value = e.target.value;
                    setColumnSearch(value);
                  }}
                  onKeyDown={(e) => {
                    // Prevent dropdown from closing when typing
                    e.stopPropagation();
                  }}
                  onClick={(e) => {
                    // Prevent dropdown from closing when clicking input
                    e.stopPropagation();
                  }}
                  className="pe-8 text-start text-sm h-8"
                  dir="rtl"
                  aria-label="חיפוש עמודות"
                  autoFocus
                />
              </div>
            </div>
            <div className="flex-1 overflow-y-auto min-h-0 ps-2" style={{ maxHeight: 'calc(100vh - 20rem)' }}>
              {/* Quick actions */}
              <div className="p-2 border-b bg-muted/30 flex-shrink-0">
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

        {/* Actions dropdown - Always visible */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className={TOOLBAR_PILL_BUTTON_CLASSES}
              aria-label="פעולות על נתונים"
            >
              <MoreHorizontal className="h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0" />
              <span className="hidden sm:inline">פעולות</span>
              {selectedCount > 0 && (
                <>
                  <Badge
                    variant="secondary"
                    className="hidden sm:inline-flex items-center gap-1 px-1.5 sm:px-2 py-0.5 text-xs font-medium ms-1 sm:ms-2"
                  >
                    {selectedCount}
                  </Badge>
                  <Badge
                    variant="secondary"
                    className="inline-flex items-center justify-center px-1.5 sm:px-2 py-0.5 text-xs font-medium sm:hidden ms-1 sm:ms-2"
                  >
                    {selectedCount}
                  </Badge>
                </>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="bg-white">
            <DropdownMenuLabel className="bg-white text-foreground">פעולות</DropdownMenuLabel>
            <DropdownMenuSeparator />
            
            {/* Export section */}
            <div className="px-2 py-1.5">
              <span className="text-xs font-medium text-muted-foreground">ייצוא נתונים</span>
            </div>
            <DropdownMenuCheckboxItem 
              onClick={onExportAll}
              disabled={disableExportAll}
              className="bg-white text-foreground hover:bg-muted disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <Download className="h-4 w-4 me-2 rtl:ms-2 rtl:me-0" />
              ייצוא הכל ({totalCount})
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem 
              onClick={onExportSelected}
              disabled={selectedCount === 0}
              className="bg-white text-foreground hover:bg-muted"
            >
              <Download className="h-4 w-4 me-2 rtl:ms-2 rtl:me-0" />
              ייצוא נבחרים ({selectedCount})
            </DropdownMenuCheckboxItem>

            {/* Import section */}
            {importAction && (
              <>
                <DropdownMenuSeparator />
                <div className="px-2 py-1.5">
                  <span className="text-xs font-medium text-muted-foreground">ייבוא נתונים</span>
                </div>
                <DropdownMenuCheckboxItem 
                  onClick={importAction.onClick}
                  className="bg-white text-foreground hover:bg-muted"
                >
                  {importAction.icon && <span className="me-2 rtl:ms-2 rtl:me-0">{importAction.icon}</span>}
                  {importAction.label}
                </DropdownMenuCheckboxItem>
              </>
            )}

            {/* Bulk actions section - only show if items are selected */}
            {bulkActions.length > 0 && selectedCount > 0 && (
              <>
                <DropdownMenuSeparator />
                <div className="px-2 py-1.5">
                  <span className="text-xs font-medium text-muted-foreground">פעולות על נבחרים ({selectedCount})</span>
                </div>
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
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Refresh */}
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={loading}
          className={TOOLBAR_PILL_BUTTON_CLASSES}
        >
          <RefreshCw className={`h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0 ${loading ? 'animate-spin' : ''}`} aria-hidden="true" />
          <span className="hidden sm:inline">רענן</span>
        </Button>

      </div>
        )}
      </div>

      {/* Bottom row - Status and info */}
      <div className="flex flex-col sm:flex-row gap-1.5 sm:gap-2 sm:items-center sm:justify-between text-xs sm:text-sm text-muted-foreground rtl:sm:flex-row-reverse">
        <div className="flex items-center gap-2 sm:gap-4 rtl:flex-row-reverse">
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
        <div className="text-xs hidden sm:block">
          {isClient ? `${columns.filter(c => c.visible).length} מתוך ${columns.length} עמודות` : `${columns.length} עמודות`}
        </div>
      </div>
    </div>
  );
}
