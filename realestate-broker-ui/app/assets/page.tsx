"use client";
import React, { useState, useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
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
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  RefreshCw,
  Trash2,
  Download,
  FileText,
  DownloadCloud,
  Star,
  StarOff,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { selectOnboardingState, isOnboardingComplete } from "@/onboarding/selectors";
import type { Asset } from "@/lib/normalizers/asset";
import AssetsTable from "@/components/AssetsTable";
import ImportDialogNadlanOne from "@/components/import/ImportDialogNadlanOne";

import dynamic from "next/dynamic";
import DashboardLayout from "@/components/layout/dashboard-layout";

const MapView = dynamic(() => import("@/components/MapView"), {
  ssr: false,
  loading: () => (
    <div className="flex flex-col items-center justify-center py-12 space-y-4">
      <RefreshCw className="h-8 w-8 animate-spin text-brand-teal" />
      <div className="text-center">
        <p className="text-sm sm:text-base text-muted-foreground">טוען מפה...</p>
      </div>
    </div>
  ),
});
import { ResponsiveContainer } from "@/components/layout/responsive-container";
import { SectionHeader, type SectionHeaderAction } from "@/components/layout/section-header";
import { useSavedFilters } from "@/hooks/use-saved-filters";
import { SavedFilterPreset } from "@/components/layout/saved-filters-menu";
import { TableActionsToolbar, type TableActionColumn, type TableAction } from "@/components/layout/table-actions-toolbar";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useToast } from "@/hooks/use-toast";
import { useConfirm } from "@/hooks/use-confirm";
import PlanLimitDialog from "@/components/PlanLimitDialog";
import { apiClient } from "@/lib/api-client";
import { useDedupedEffect } from "@/hooks/use-deduped-effect";
import { useMediaQuery } from "@/hooks/use-media-query";
import type { PaginationState, SortingState } from "@tanstack/react-table";
import { getUserFriendlyError } from "@/lib/error-utils";
import { trackEvent } from "@/lib/analytics";

const DEFAULT_RADIUS_METERS = 100;
const DEFAULT_PAGE_SIZE = 25;
const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

const RISK_FILTER_OPTIONS = [
  { value: "flagged", label: "עם דגלי סיכון" },
  { value: "clean", label: "ללא דגלי סיכון" },
] as const;

const DOCUMENTS_FILTER_OPTIONS = [
  { value: "with", label: "עם מסמכים" },
  { value: "without", label: "ללא מסמכים" },
] as const;

type AssetFilterMetadata = {
  cities: string[];
  types: string[];
  neighborhoods: string[];
  zonings: string[];
  blocks: string[];
  parcels: string[];
  sources: string[];
  buildingTypes: string[];
  rooms: number[];
  statusCounts: Record<string, number>;
  bedroomCounts: number[];
  bathroomCounts: number[];
  totalFloorCounts: number[];
  parkingSpaceCounts: number[];
  balconyAreas: number[];
  totalAreaRange: { min: number | null; max: number | null };
  yearBuiltRange: { min: number | null; max: number | null };
  rentPriceRange: { min: number | null; max: number | null };
  rentEstimateRange: { min: number | null; max: number | null };
  priceGapPctRange: { min: number | null; max: number | null };
  capRatePctRange: { min: number | null; max: number | null };
  bedroomRange: { min: number | null; max: number | null };
  bathroomRange: { min: number | null; max: number | null };
  totalFloorRange: { min: number | null; max: number | null };
  parkingSpaceRange: { min: number | null; max: number | null };
  balconyAreaRange: { min: number | null; max: number | null };
};

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [nadlanImportOpen, setNadlanImportOpen] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: DEFAULT_PAGE_SIZE });
  const [sorting, setSorting] = useState<SortingState>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [watchingAssetIds, setWatchingAssetIds] = useState<Set<number>>(() => new Set());
  const [filterMetadata, setFilterMetadata] = useState<AssetFilterMetadata>({
    cities: [],
    types: [],
    neighborhoods: [],
    zonings: [],
    blocks: [],
    parcels: [],
    sources: [],
    buildingTypes: [],
    rooms: [],
    statusCounts: {},
    bedroomCounts: [],
    bathroomCounts: [],
    totalFloorCounts: [],
    parkingSpaceCounts: [],
    balconyAreas: [],
    totalAreaRange: { min: null, max: null },
    yearBuiltRange: { min: null, max: null },
    rentPriceRange: { min: null, max: null },
    rentEstimateRange: { min: null, max: null },
    priceGapPctRange: { min: null, max: null },
    capRatePctRange: { min: null, max: null },
    bedroomRange: { min: null, max: null },
    bathroomRange: { min: null, max: null },
    totalFloorRange: { min: null, max: null },
    parkingSpaceRange: { min: null, max: null },
    balconyAreaRange: { min: null, max: null },
  });
  const searchParams = useSearchParams();
  const [searchInput, setSearchInput] = useState(() => searchParams.get("search") ?? "");
  const [debouncedSearch, setDebouncedSearch] = useState(() => searchParams.get("search") ?? "");
  const [city, setCity] = useState<string>(() => searchParams.get("city") ?? "all");
  const [typeFilter, setTypeFilter] = useState(
    () => searchParams.get("type") ?? "all"
  );
  const [priceMin, setPriceMin] = useState<number | undefined>(() => {
    const val = searchParams.get("priceMin");
    return val ? Number(val) : undefined;
  });
  const [priceMax, setPriceMax] = useState<number | undefined>(() => {
    const val = searchParams.get("priceMax");
    return val ? Number(val) : undefined;
  });
  const [neighborhood, setNeighborhood] = useState<string>(() => searchParams.get("neighborhood") ?? "all");
  const [zoning, setZoning] = useState<string>(() => searchParams.get("zoning") ?? "all");
  const [riskFilter, setRiskFilter] = useState<string>(() => searchParams.get("risk") ?? "all");
  const [documentsFilter, setDocumentsFilter] = useState<string>(() => searchParams.get("documents") ?? "all");
  const [statusFilter, setStatusFilter] = useState<string>(() => searchParams.get("status") ?? "all");
  const [sourceFilter, setSourceFilter] = useState<string>(() => searchParams.get("source") ?? "all");
  const [rentalSaleFilter, setRentalSaleFilter] = useState<string>(() => searchParams.get("listingType") ?? searchParams.get("rentalSale") ?? "all");
  const [sellerTypeFilter, setSellerTypeFilter] = useState<string>(() => searchParams.get("sellerType") ?? searchParams.get("adType") ?? "all");
  const [commercialFilter, setCommercialFilter] = useState<string>(() => searchParams.get("commercial") ?? "all");
  const [userAssetsFilter, setUserAssetsFilter] = useState<string>(() => searchParams.get("userAssets") ?? "all");
  const [buildingTypeFilter, setBuildingTypeFilter] = useState<string>(() => searchParams.get("buildingType") ?? "all");
  const [floorMin, setFloorMin] = useState<number | undefined>(() => {
    const val = searchParams.get("floorMin");
    return val ? Number(val) : undefined;
  });
  const [floorMax, setFloorMax] = useState<number | undefined>(() => {
    const val = searchParams.get("floorMax");
    return val ? Number(val) : undefined;
  });
  const [areaMin, setAreaMin] = useState<number | undefined>(() => {
    const val = searchParams.get("areaMin");
    return val ? Number(val) : undefined;
  });
  const [areaMax, setAreaMax] = useState<number | undefined>(() => {
    const val = searchParams.get("areaMax");
    return val ? Number(val) : undefined;
  });
  const [bedroomsMin, setBedroomsMin] = useState<number | undefined>(() => {
    const val = searchParams.get("bedroomsMin");
    return val ? Number(val) : undefined;
  });
  const [bedroomsMax, setBedroomsMax] = useState<number | undefined>(() => {
    const val = searchParams.get("bedroomsMax");
    return val ? Number(val) : undefined;
  });
  const [bathroomsMin, setBathroomsMin] = useState<number | undefined>(() => {
    const val = searchParams.get("bathroomsMin");
    return val ? Number(val) : undefined;
  });
  const [bathroomsMax, setBathroomsMax] = useState<number | undefined>(() => {
    const val = searchParams.get("bathroomsMax");
    return val ? Number(val) : undefined;
  });
  const [totalFloorsMin, setTotalFloorsMin] = useState<number | undefined>(() => {
    const val = searchParams.get("totalFloorsMin");
    return val ? Number(val) : undefined;
  });
  const [totalFloorsMax, setTotalFloorsMax] = useState<number | undefined>(() => {
    const val = searchParams.get("totalFloorsMax");
    return val ? Number(val) : undefined;
  });
  const [totalAreaMin, setTotalAreaMin] = useState<number | undefined>(() => {
    const val = searchParams.get("totalAreaMin");
    return val ? Number(val) : undefined;
  });
  const [totalAreaMax, setTotalAreaMax] = useState<number | undefined>(() => {
    const val = searchParams.get("totalAreaMax");
    return val ? Number(val) : undefined;
  });
  const [balconyAreaMin, setBalconyAreaMin] = useState<number | undefined>(() => {
    const val = searchParams.get("balconyAreaMin");
    return val ? Number(val) : undefined;
  });
  const [balconyAreaMax, setBalconyAreaMax] = useState<number | undefined>(() => {
    const val = searchParams.get("balconyAreaMax");
    return val ? Number(val) : undefined;
  });
  const [parkingSpacesMin, setParkingSpacesMin] = useState<number | undefined>(() => {
    const val = searchParams.get("parkingSpacesMin");
    return val ? Number(val) : undefined;
  });
  const [parkingSpacesMax, setParkingSpacesMax] = useState<number | undefined>(() => {
    const val = searchParams.get("parkingSpacesMax");
    return val ? Number(val) : undefined;
  });
  const [yearBuiltMin, setYearBuiltMin] = useState<number | undefined>(() => {
    const val = searchParams.get("yearBuiltMin");
    return val ? Number(val) : undefined;
  });
  const [yearBuiltMax, setYearBuiltMax] = useState<number | undefined>(() => {
    const val = searchParams.get("yearBuiltMax");
    return val ? Number(val) : undefined;
  });
  const [rentPriceMin, setRentPriceMin] = useState<number | undefined>(() => {
    const val = searchParams.get("rentPriceMin");
    return val ? Number(val) : undefined;
  });
  const [rentPriceMax, setRentPriceMax] = useState<number | undefined>(() => {
    const val = searchParams.get("rentPriceMax");
    return val ? Number(val) : undefined;
  });
  const [rentEstimateMin, setRentEstimateMin] = useState<number | undefined>(() => {
    const val = searchParams.get("rentEstimateMin");
    return val ? Number(val) : undefined;
  });
  const [rentEstimateMax, setRentEstimateMax] = useState<number | undefined>(() => {
    const val = searchParams.get("rentEstimateMax");
    return val ? Number(val) : undefined;
  });
  const [priceGapPctMin, setPriceGapPctMin] = useState<number | undefined>(() => {
    const val = searchParams.get("priceGapPctMin");
    return val ? Number(val) : undefined;
  });
  const [priceGapPctMax, setPriceGapPctMax] = useState<number | undefined>(() => {
    const val = searchParams.get("priceGapPctMax");
    return val ? Number(val) : undefined;
  });
  const [capRatePctMin, setCapRatePctMin] = useState<number | undefined>(() => {
    const val = searchParams.get("capRatePctMin");
    return val ? Number(val) : undefined;
  });
  const [capRatePctMax, setCapRatePctMax] = useState<number | undefined>(() => {
    const val = searchParams.get("capRatePctMax");
    return val ? Number(val) : undefined;
  });
  const [roomsFilter, setRoomsFilter] = useState<string>(() => searchParams.get("rooms") ?? "all");
  const [featuresFilter, setFeaturesFilter] = useState<string>(() => searchParams.get("features") ?? "all");
  const [pricePerSqmMin, setPricePerSqmMin] = useState<number | undefined>(() => {
    const val = searchParams.get("pricePerSqmMin");
    return val ? Number(val) : undefined;
  });
  const [pricePerSqmMax, setPricePerSqmMax] = useState<number | undefined>(() => {
    const val = searchParams.get("pricePerSqmMax");
    return val ? Number(val) : undefined;
  });
  const [remainingRightsMin, setRemainingRightsMin] = useState<number | undefined>(() => {
    const val = searchParams.get("remainingRightsMin");
    return val ? Number(val) : undefined;
  });
  const [remainingRightsMax, setRemainingRightsMax] = useState<number | undefined>(() => {
    const val = searchParams.get("remainingRightsMax");
    return val ? Number(val) : undefined;
  });
  const [blockFilter, setBlockFilter] = useState<string>(() => searchParams.get("block") ?? "all");
  const [parcelFilter, setParcelFilter] = useState<string>(() => searchParams.get("parcel") ?? "all");
  const [renovatedFilter, setRenovatedFilter] = useState<string>(() => {
    const value = searchParams.get("renovated");
    return value ?? "all";
  });
  const [furnishedFilter, setFurnishedFilter] = useState<string>(() => {
    const value = searchParams.get("furnished");
    return value ?? "all";
  });
  const [airConditioningFilter, setAirConditioningFilter] = useState<string>(() => {
    const value = searchParams.get("airConditioning");
    return value ?? "all";
  });
  const [storageRoomFilter, setStorageRoomFilter] = useState<string>(() => {
    const value = searchParams.get("storageRoom");
    return value ?? "all";
  });
  const [hasElevatorFilter, setHasElevatorFilter] = useState<string>(() => {
    const value = searchParams.get("hasElevator");
    return value ?? "all";
  });
  const [recentDealFilter, setRecentDealFilter] = useState<string>(() => {
    const value = searchParams.get("recentDeal");
    return value ?? "all";
  });
  const [modelPriceMin, setModelPriceMin] = useState<number | undefined>(() => {
    const val = searchParams.get("modelPriceMin");
    return val ? Number(val) : undefined;
  });
  const [modelPriceMax, setModelPriceMax] = useState<number | undefined>(() => {
    const val = searchParams.get("modelPriceMax");
    return val ? Number(val) : undefined;
  });
  const [antennaDistanceMin, setAntennaDistanceMin] = useState<number | undefined>(() => {
    const val = searchParams.get("antennaDistanceMin");
    return val ? Number(val) : undefined;
  });
  const [antennaDistanceMax, setAntennaDistanceMax] = useState<number | undefined>(() => {
    const val = searchParams.get("antennaDistanceMax");
    return val ? Number(val) : undefined;
  });
  const [shelterDistanceMin, setShelterDistanceMin] = useState<number | undefined>(() => {
    const val = searchParams.get("shelterDistanceMin");
    return val ? Number(val) : undefined;
  });
  const [shelterDistanceMax, setShelterDistanceMax] = useState<number | undefined>(() => {
    const val = searchParams.get("shelterDistanceMax");
    return val ? Number(val) : undefined;
  });
  const [noiseLevelMin, setNoiseLevelMin] = useState<number | undefined>(() => {
    const val = searchParams.get("noiseLevelMin");
    return val ? Number(val) : undefined;
  });
  const [noiseLevelMax, setNoiseLevelMax] = useState<number | undefined>(() => {
    const val = searchParams.get("noiseLevelMax");
    return val ? Number(val) : undefined;
  });
  const [greenWithin300mFilter, setGreenWithin300mFilter] = useState<string>(() => {
    const value = searchParams.get("greenWithin300m");
    return value ?? "all";
  });
  const [schoolsWithin500mFilter, setSchoolsWithin500mFilter] = useState<string>(() => {
    const value = searchParams.get("schoolsWithin500m");
    return value ?? "all";
  });
  // High Priority Filters
  const [priceDroppedFilter, setPriceDroppedFilter] = useState<string>(() => {
    const value = searchParams.get("priceDropped");
    return value ?? "all";
  });
  const [shelterFilter, setShelterFilter] = useState<string>(() => {
    const value = searchParams.get("shelter");
    return value ?? "all";
  });
  const [accessibilityFilter, setAccessibilityFilter] = useState<string>(() => {
    const value = searchParams.get("accessibility");
    return value ?? "all";
  });
  const [buildingClassFilter, setBuildingClassFilter] = useState<string>(() => {
    const value = searchParams.get("buildingClass");
    return value ?? "all";
  });
  const [generalConditionFilter, setGeneralConditionFilter] = useState<string>(() => {
    const value = searchParams.get("generalCondition");
    return value ?? "all";
  });
  const [investmentYieldMin, setInvestmentYieldMin] = useState<number | undefined>(() => {
    const val = searchParams.get("investmentYieldMin");
    return val ? Number(val) : undefined;
  });
  const [investmentYieldMax, setInvestmentYieldMax] = useState<number | undefined>(() => {
    const val = searchParams.get("investmentYieldMax");
    return val ? Number(val) : undefined;
  });
  const [approximateRentMin, setApproximateRentMin] = useState<number | undefined>(() => {
    const val = searchParams.get("approximateRentMin");
    return val ? Number(val) : undefined;
  });
  const [approximateRentMax, setApproximateRentMax] = useState<number | undefined>(() => {
    const val = searchParams.get("approximateRentMax");
    return val ? Number(val) : undefined;
  });
  const [commuteTimeMin, setCommuteTimeMin] = useState<number | undefined>(() => {
    const val = searchParams.get("commuteTimeMin");
    return val ? Number(val) : undefined;
  });
  const [commuteTimeMax, setCommuteTimeMax] = useState<number | undefined>(() => {
    const val = searchParams.get("commuteTimeMax");
    return val ? Number(val) : undefined;
  });
  const [publishedDaysMax, setPublishedDaysMax] = useState<number | undefined>(() => {
    const val = searchParams.get("publishedDaysMax");
    return val ? Number(val) : undefined;
  });
  // Madlan Tags
  const [tagBestSchoolFilter, setTagBestSchoolFilter] = useState<string>(() => {
    const value = searchParams.get("tagBestSchool");
    return value ?? "all";
  });
  const [tagSafetyFilter, setTagSafetyFilter] = useState<string>(() => {
    const value = searchParams.get("tagSafety");
    return value ?? "all";
  });
  const [tagFamilyFriendlyFilter, setTagFamilyFriendlyFilter] = useState<string>(() => {
    const value = searchParams.get("tagFamilyFriendly");
    return value ?? "all";
  });
  const [tagLightRailFilter, setTagLightRailFilter] = useState<string>(() => {
    const value = searchParams.get("tagLightRail");
    return value ?? "all";
  });
  const [exclusiveFilter, setExclusiveFilter] = useState<string>(() => {
    const value = searchParams.get("exclusive");
    return value ?? "all";
  });
  const [viewMode, setViewMode] = useState<'table' | 'cards' | 'map'>(() => {
    const urlViewMode = searchParams.get("view");
    if (urlViewMode === 'table' || urlViewMode === 'cards' || urlViewMode === 'map') {
      return urlViewMode;
    }
    // Default to cards on mobile if no URL parameter
    if (typeof window !== 'undefined' && window.matchMedia) {
      const isMobile = !window.matchMedia('(min-width: 1024px)').matches;
      return isMobile ? 'cards' : 'table';
    }
    // SSR fallback: default to table (will be adjusted by auto-switch effect)
    return 'table';
  });
  const [viewModeManuallySet, setViewModeManuallySet] = useState(false);
  const { matches: isDesktop, isReady: isViewportReady } = useMediaQuery('(min-width: 1024px)');
  const router = useRouter();
  const pathname = usePathname();

  const handleViewModeChange = React.useCallback(
    (nextMode: 'table' | 'cards' | 'map') => {
      setViewMode(nextMode);
      setViewModeManuallySet(true);
      
      // Update URL with view mode
      const params = new URLSearchParams(searchParams.toString());
      params.set('view', nextMode);
      router.push(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [setViewMode, setViewModeManuallySet, searchParams, router, pathname]
  );

  // Sync URL view mode to state (for browser back/forward and refresh)
  React.useEffect(() => {
    const urlViewMode = searchParams.get("view");
    if (urlViewMode === 'table' || urlViewMode === 'cards' || urlViewMode === 'map') {
      if (viewMode !== urlViewMode) {
        setViewMode(urlViewMode);
        setViewModeManuallySet(true);
      }
    } else if (urlViewMode === null && viewModeManuallySet) {
      // URL was cleared (e.g., browser back), reset manual flag
      setViewModeManuallySet(false);
    }
  }, [searchParams, viewMode, viewModeManuallySet]);

  React.useEffect(() => {
    if (!isViewportReady) {
      return
    }

    // Only auto-switch if view mode wasn't manually set and not in URL
    const urlViewMode = searchParams.get("view");
    if (urlViewMode) {
      // View mode is in URL, don't auto-switch
      return;
    }

    // Auto-switch to cards on mobile, table on desktop
    if (!isDesktop && !viewModeManuallySet && viewMode !== 'cards') {
      setViewMode('cards')
      return
    }

    if (isDesktop && !viewModeManuallySet && viewMode === 'cards') {
      setViewMode('table')
    }
  }, [isDesktop, isViewportReady, setViewMode, viewMode, viewModeManuallySet, searchParams])

  // Track previous pathname and search params to detect navigation clicks
  const prevPathnameRef = React.useRef<string | null>(null);
  const prevSearchParamsRef = React.useRef<string>('');
  const isNavigatingFromAssetsRef = React.useRef(false);

  // Detect when user clicks navigation (including assets nav while on assets)
  React.useEffect(() => {
    const prevPathname = prevPathnameRef.current;
    const currentPathname = pathname;
    const currentSearchParams = searchParams.toString();
    const prevSearchParams = prevSearchParamsRef.current;
    
    // Initialize on mount
    if (prevPathname === null) {
      prevPathnameRef.current = currentPathname;
      prevSearchParamsRef.current = currentSearchParams;
      return;
    }

    // Detect navigation away from /assets
    const isNavigatingAway = prevPathname === '/assets' && currentPathname !== '/assets';
    
    // Detect clicking assets nav while on assets (URL changes from /assets?filters to /assets)
    const hadFilterParams = prevSearchParams && Array.from(new URLSearchParams(prevSearchParams).keys()).some(
      key => key !== 'view'
    );
    const isClickingAssetsNav = prevPathname === '/assets' && 
                                 currentPathname === '/assets' &&
                                 prevSearchParams !== currentSearchParams &&
                                 hadFilterParams &&
                                 !Array.from(searchParams.keys()).some(key => key !== 'view');
    
    if (isNavigatingAway || isClickingAssetsNav) {
      isNavigatingFromAssetsRef.current = true;
      // Reset flag after a short delay
      setTimeout(() => {
        isNavigatingFromAssetsRef.current = false;
      }, 100);
    }
    
    prevPathnameRef.current = currentPathname;
    prevSearchParamsRef.current = currentSearchParams;
  }, [pathname, searchParams]);

  const { user, isAuthenticated, refreshUser } = useAuth();
  const isAdmin = user?.role === 'admin';
  const onboardingState = React.useMemo(() => selectOnboardingState(user), [user]);
  const { toast } = useToast();
  const { confirm } = useConfirm();
  const { savedFilters, saveFilters, deleteFilter, applyFilter, hasActiveFilters } = useSavedFilters('assets');

  // Handle protected action (add new asset)
  const handleProtectedAction = (action: string) => {
    if (!isAuthenticated) {
      router.push("/auth?redirect=" + encodeURIComponent("/assets"));
    }
  };

  const [citySuggestions, setCitySuggestions] = useState<string[]>([]);
  const [streetSuggestions, setStreetSuggestions] = useState<string[]>([]);
  const [planLimitError, setPlanLimitError] = useState<any>(null);
  const [showPlanLimitDialog, setShowPlanLimitDialog] = useState(false);

  const fetchCitySuggestions = async (query: string) => {
    if (!query) {
      setCitySuggestions([]);
      return;
    }
    try {
      const res = await fetch(
        `https://data.gov.il/api/3/action/datastore_search?resource_id=d4901968-dad3-4845-a9b0-a57d027f11ab&q=${encodeURIComponent(
          query
        )}&limit=5`
      );
      const json = await res.json();
      const records = json.result?.records || [];
      setCitySuggestions(
        Array.from(
          new Set(
            records
              .map(
                (item: any) =>
                  (item["שם_ישוב"] || item["שם ישוב"] || item.city || item.name).trim()
              )
              .filter(Boolean)
          )
        ) as string[]
      );
    } catch (e) {
      console.error("Failed to fetch city suggestions", e);
    }
  };

  const fetchStreetSuggestions = async (
    query: string,
    cityName?: string
  ) => {
    if (!query || !cityName) {
      setStreetSuggestions([]);
      return;
    }
    try {
      const res = await fetch(
        `https://data.gov.il/api/3/action/datastore_search?resource_id=9ad3862c-8391-4b2f-84a4-2d4c68625f4b&limit=5&q=${encodeURIComponent(
          query
        )}`
      );
      const json = await res.json();
      const records = json.result?.records || [];
      const roads = Array.from(
        new Set(
          records
            .map(
              (item: any) =>
                (item["שם_רחוב"] ||
                item["שם רחוב"] ||
                item.street ||
                item.road).trim()
            )
            .filter(Boolean)
        )
      );
      setStreetSuggestions(roads as string[]);
    } catch (e) {
      console.error("Failed to fetch street suggestions", e);
    }
  };


  // Debounce search input
  React.useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearch(searchInput.trim());
    }, 300);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    const searchParam = searchParams.get("search") ?? "";
    setSearchInput(searchParam);
    setDebouncedSearch(searchParam);
    setCity(searchParams.get("city") ?? "all");
    setTypeFilter(searchParams.get("type") ?? "all");
    const min = searchParams.get("priceMin");
    setPriceMin(min ? Number(min) : undefined);
    const max = searchParams.get("priceMax");
    setPriceMax(max ? Number(max) : undefined);
    setNeighborhood(searchParams.get("neighborhood") ?? "all");
    setZoning(searchParams.get("zoning") ?? "all");
    setRiskFilter(searchParams.get("risk") ?? "all");
    setDocumentsFilter(searchParams.get("documents") ?? "all");
    setStatusFilter(searchParams.get("status") ?? "all");
    setRentalSaleFilter(searchParams.get("listingType") ?? searchParams.get("rentalSale") ?? "all");
    setSellerTypeFilter(searchParams.get("sellerType") ?? "all");
    setCommercialFilter(searchParams.get("commercial") ?? "all");
    setUserAssetsFilter(searchParams.get("userAssets") ?? "all");
    setBuildingTypeFilter(searchParams.get("buildingType") ?? "all");
    const floorMinVal = searchParams.get("floorMin");
    setFloorMin(floorMinVal ? Number(floorMinVal) : undefined);
    const floorMaxVal = searchParams.get("floorMax");
    setFloorMax(floorMaxVal ? Number(floorMaxVal) : undefined);
    const areaMinVal = searchParams.get("areaMin");
    setAreaMin(areaMinVal ? Number(areaMinVal) : undefined);
    const areaMaxVal = searchParams.get("areaMax");
    setAreaMax(areaMaxVal ? Number(areaMaxVal) : undefined);
    const bedroomsMinVal = searchParams.get("bedroomsMin");
    setBedroomsMin(bedroomsMinVal ? Number(bedroomsMinVal) : undefined);
    const bedroomsMaxVal = searchParams.get("bedroomsMax");
    setBedroomsMax(bedroomsMaxVal ? Number(bedroomsMaxVal) : undefined);
    const bathroomsMinVal = searchParams.get("bathroomsMin");
    setBathroomsMin(bathroomsMinVal ? Number(bathroomsMinVal) : undefined);
    const bathroomsMaxVal = searchParams.get("bathroomsMax");
    setBathroomsMax(bathroomsMaxVal ? Number(bathroomsMaxVal) : undefined);
    const totalFloorsMinVal = searchParams.get("totalFloorsMin");
    setTotalFloorsMin(totalFloorsMinVal ? Number(totalFloorsMinVal) : undefined);
    const totalFloorsMaxVal = searchParams.get("totalFloorsMax");
    setTotalFloorsMax(totalFloorsMaxVal ? Number(totalFloorsMaxVal) : undefined);
    const totalAreaMinVal = searchParams.get("totalAreaMin");
    setTotalAreaMin(totalAreaMinVal ? Number(totalAreaMinVal) : undefined);
    const totalAreaMaxVal = searchParams.get("totalAreaMax");
    setTotalAreaMax(totalAreaMaxVal ? Number(totalAreaMaxVal) : undefined);
    const balconyAreaMinVal = searchParams.get("balconyAreaMin");
    setBalconyAreaMin(balconyAreaMinVal ? Number(balconyAreaMinVal) : undefined);
    const balconyAreaMaxVal = searchParams.get("balconyAreaMax");
    setBalconyAreaMax(balconyAreaMaxVal ? Number(balconyAreaMaxVal) : undefined);
    const parkingSpacesMinVal = searchParams.get("parkingSpacesMin");
    setParkingSpacesMin(parkingSpacesMinVal ? Number(parkingSpacesMinVal) : undefined);
    const parkingSpacesMaxVal = searchParams.get("parkingSpacesMax");
    setParkingSpacesMax(parkingSpacesMaxVal ? Number(parkingSpacesMaxVal) : undefined);
    const yearBuiltMinVal = searchParams.get("yearBuiltMin");
    setYearBuiltMin(yearBuiltMinVal ? Number(yearBuiltMinVal) : undefined);
    const yearBuiltMaxVal = searchParams.get("yearBuiltMax");
    setYearBuiltMax(yearBuiltMaxVal ? Number(yearBuiltMaxVal) : undefined);
    const rentPriceMinVal = searchParams.get("rentPriceMin");
    setRentPriceMin(rentPriceMinVal ? Number(rentPriceMinVal) : undefined);
    const rentPriceMaxVal = searchParams.get("rentPriceMax");
    setRentPriceMax(rentPriceMaxVal ? Number(rentPriceMaxVal) : undefined);
    const rentEstimateMinVal = searchParams.get("rentEstimateMin");
    setRentEstimateMin(rentEstimateMinVal ? Number(rentEstimateMinVal) : undefined);
    const rentEstimateMaxVal = searchParams.get("rentEstimateMax");
    setRentEstimateMax(rentEstimateMaxVal ? Number(rentEstimateMaxVal) : undefined);
    const priceGapPctMinVal = searchParams.get("priceGapPctMin");
    setPriceGapPctMin(priceGapPctMinVal ? Number(priceGapPctMinVal) : undefined);
    const priceGapPctMaxVal = searchParams.get("priceGapPctMax");
    setPriceGapPctMax(priceGapPctMaxVal ? Number(priceGapPctMaxVal) : undefined);
    const capRatePctMinVal = searchParams.get("capRatePctMin");
    setCapRatePctMin(capRatePctMinVal ? Number(capRatePctMinVal) : undefined);
    const capRatePctMaxVal = searchParams.get("capRatePctMax");
    setCapRatePctMax(capRatePctMaxVal ? Number(capRatePctMaxVal) : undefined);
    setRoomsFilter(searchParams.get("rooms") ?? "all");
    setFeaturesFilter(searchParams.get("features") ?? "all");
    const pricePerSqmMinVal = searchParams.get("pricePerSqmMin");
    setPricePerSqmMin(pricePerSqmMinVal ? Number(pricePerSqmMinVal) : undefined);
    const pricePerSqmMaxVal = searchParams.get("pricePerSqmMax");
    setPricePerSqmMax(pricePerSqmMaxVal ? Number(pricePerSqmMaxVal) : undefined);
    const remainingRightsMinVal = searchParams.get("remainingRightsMin");
    setRemainingRightsMin(remainingRightsMinVal ? Number(remainingRightsMinVal) : undefined);
    const remainingRightsMaxVal = searchParams.get("remainingRightsMax");
    setRemainingRightsMax(remainingRightsMaxVal ? Number(remainingRightsMaxVal) : undefined);
    setBlockFilter(searchParams.get("block") ?? "all");
    setParcelFilter(searchParams.get("parcel") ?? "all");
    setRenovatedFilter(searchParams.get("renovated") ?? "all");
    setFurnishedFilter(searchParams.get("furnished") ?? "all");
    setAirConditioningFilter(searchParams.get("airConditioning") ?? "all");
    setStorageRoomFilter(searchParams.get("storageRoom") ?? "all");
    setHasElevatorFilter(searchParams.get("hasElevator") ?? "all");
    setRecentDealFilter(searchParams.get("recentDeal") ?? "all");
    const pageParam = searchParams.get("page");
    const pageSizeParam = searchParams.get("pageSize");
    setPagination(prev => {
      const nextIndex = pageParam ? Math.max(Number(pageParam) - 1, 0) : 0;
      const nextSize = pageSizeParam ? Number(pageSizeParam) : prev.pageSize;
      if (Number.isNaN(nextSize) || nextSize <= 0) {
        return { pageIndex: nextIndex, pageSize: prev.pageSize };
      }
      if (nextIndex === prev.pageIndex && nextSize === prev.pageSize) {
        return prev;
      }
      return { pageIndex: nextIndex, pageSize: nextSize };
    });
  }, [searchParams]);

  useEffect(() => {
    // Skip updating URL if we're navigating from assets (prevents loop)
    if (isNavigatingFromAssetsRef.current) {
      return;
    }
    
    const params = new URLSearchParams(searchParams.toString());
    if (debouncedSearch) {
      params.set("search", debouncedSearch);
    } else {
      params.delete("search");
    }
    if (city && city !== "all") {
      params.set("city", city);
    } else {
      params.delete("city");
    }
    if (typeFilter && typeFilter !== "all") {
      params.set("type", typeFilter);
    } else {
      params.delete("type");
    }
    if (priceMin !== undefined) {
      params.set("priceMin", priceMin.toString());
    } else {
      params.delete("priceMin");
    }
    if (priceMax !== undefined) {
      params.set("priceMax", priceMax.toString());
    } else {
      params.delete("priceMax");
    }
    if (neighborhood && neighborhood !== "all") {
      params.set("neighborhood", neighborhood);
    } else {
      params.delete("neighborhood");
    }
    if (zoning && zoning !== "all") {
      params.set("zoning", zoning);
    } else {
      params.delete("zoning");
    }
    if (riskFilter && riskFilter !== "all") {
      params.set("risk", riskFilter);
    } else {
      params.delete("risk");
    }
    if (documentsFilter && documentsFilter !== "all") {
      params.set("documents", documentsFilter);
    } else {
      params.delete("documents");
    }
    if (statusFilter && statusFilter !== "all") {
      params.set("status", statusFilter);
    } else {
      params.delete("status");
    }
    if (sourceFilter && sourceFilter !== "all") {
      params.set("source", sourceFilter);
    } else {
      params.delete("source");
    }
    if (rentalSaleFilter && rentalSaleFilter !== "all") {
      params.set("listingType", rentalSaleFilter);
      params.delete("rentalSale"); // Remove old param for backward compatibility
    } else {
      params.delete("listingType");
      params.delete("rentalSale");
    }
    if (sellerTypeFilter && sellerTypeFilter !== "all") {
      params.set("sellerType", sellerTypeFilter);
    } else {
      params.delete("sellerType");
      params.delete("adType"); // Remove old param for backward compatibility
    }
    if (commercialFilter && commercialFilter !== "all") {
      params.set("commercial", commercialFilter);
    } else {
      params.delete("commercial");
    }
    if (userAssetsFilter && userAssetsFilter !== "all") {
      params.set("userAssets", userAssetsFilter);
    } else {
      params.delete("userAssets");
    }
    if (buildingTypeFilter && buildingTypeFilter !== "all") {
      params.set("buildingType", buildingTypeFilter);
    } else {
      params.delete("buildingType");
    }
    if (floorMin !== undefined) {
      params.set("floorMin", floorMin.toString());
    } else {
      params.delete("floorMin");
    }
    if (floorMax !== undefined) {
      params.set("floorMax", floorMax.toString());
    } else {
      params.delete("floorMax");
    }
    if (areaMin !== undefined) {
      params.set("areaMin", areaMin.toString());
    } else {
      params.delete("areaMin");
    }
    if (areaMax !== undefined) {
      params.set("areaMax", areaMax.toString());
    } else {
      params.delete("areaMax");
    }
    if (bedroomsMin !== undefined) {
      params.set("bedroomsMin", bedroomsMin.toString());
    } else {
      params.delete("bedroomsMin");
    }
    if (bedroomsMax !== undefined) {
      params.set("bedroomsMax", bedroomsMax.toString());
    } else {
      params.delete("bedroomsMax");
    }
    if (bathroomsMin !== undefined) {
      params.set("bathroomsMin", bathroomsMin.toString());
    } else {
      params.delete("bathroomsMin");
    }
    if (bathroomsMax !== undefined) {
      params.set("bathroomsMax", bathroomsMax.toString());
    } else {
      params.delete("bathroomsMax");
    }
    if (totalFloorsMin !== undefined) {
      params.set("totalFloorsMin", totalFloorsMin.toString());
    } else {
      params.delete("totalFloorsMin");
    }
    if (totalFloorsMax !== undefined) {
      params.set("totalFloorsMax", totalFloorsMax.toString());
    } else {
      params.delete("totalFloorsMax");
    }
    if (totalAreaMin !== undefined) {
      params.set("totalAreaMin", totalAreaMin.toString());
    } else {
      params.delete("totalAreaMin");
    }
    if (totalAreaMax !== undefined) {
      params.set("totalAreaMax", totalAreaMax.toString());
    } else {
      params.delete("totalAreaMax");
    }
    if (balconyAreaMin !== undefined) {
      params.set("balconyAreaMin", balconyAreaMin.toString());
    } else {
      params.delete("balconyAreaMin");
    }
    if (balconyAreaMax !== undefined) {
      params.set("balconyAreaMax", balconyAreaMax.toString());
    } else {
      params.delete("balconyAreaMax");
    }
    if (parkingSpacesMin !== undefined) {
      params.set("parkingSpacesMin", parkingSpacesMin.toString());
    } else {
      params.delete("parkingSpacesMin");
    }
    if (parkingSpacesMax !== undefined) {
      params.set("parkingSpacesMax", parkingSpacesMax.toString());
    } else {
      params.delete("parkingSpacesMax");
    }
    if (yearBuiltMin !== undefined) {
      params.set("yearBuiltMin", yearBuiltMin.toString());
    } else {
      params.delete("yearBuiltMin");
    }
    if (yearBuiltMax !== undefined) {
      params.set("yearBuiltMax", yearBuiltMax.toString());
    } else {
      params.delete("yearBuiltMax");
    }
    if (rentPriceMin !== undefined) {
      params.set("rentPriceMin", rentPriceMin.toString());
    } else {
      params.delete("rentPriceMin");
    }
    if (rentPriceMax !== undefined) {
      params.set("rentPriceMax", rentPriceMax.toString());
    } else {
      params.delete("rentPriceMax");
    }
    if (rentEstimateMin !== undefined) {
      params.set("rentEstimateMin", rentEstimateMin.toString());
    } else {
      params.delete("rentEstimateMin");
    }
    if (rentEstimateMax !== undefined) {
      params.set("rentEstimateMax", rentEstimateMax.toString());
    } else {
      params.delete("rentEstimateMax");
    }
    if (priceGapPctMin !== undefined) {
      params.set("priceGapPctMin", priceGapPctMin.toString());
    } else {
      params.delete("priceGapPctMin");
    }
    if (priceGapPctMax !== undefined) {
      params.set("priceGapPctMax", priceGapPctMax.toString());
    } else {
      params.delete("priceGapPctMax");
    }
    if (capRatePctMin !== undefined) {
      params.set("capRatePctMin", capRatePctMin.toString());
    } else {
      params.delete("capRatePctMin");
    }
    if (capRatePctMax !== undefined) {
      params.set("capRatePctMax", capRatePctMax.toString());
    } else {
      params.delete("capRatePctMax");
    }
    if (roomsFilter && roomsFilter !== "all") {
      params.set("rooms", roomsFilter);
    } else {
      params.delete("rooms");
    }
    if (featuresFilter && featuresFilter !== "all") {
      params.set("features", featuresFilter);
    } else {
      params.delete("features");
    }
    if (pricePerSqmMin !== undefined) {
      params.set("pricePerSqmMin", pricePerSqmMin.toString());
    } else {
      params.delete("pricePerSqmMin");
    }
    if (pricePerSqmMax !== undefined) {
      params.set("pricePerSqmMax", pricePerSqmMax.toString());
    } else {
      params.delete("pricePerSqmMax");
    }
    if (remainingRightsMin !== undefined) {
      params.set("remainingRightsMin", remainingRightsMin.toString());
    } else {
      params.delete("remainingRightsMin");
    }
    if (remainingRightsMax !== undefined) {
      params.set("remainingRightsMax", remainingRightsMax.toString());
    } else {
      params.delete("remainingRightsMax");
    }
    if (blockFilter && blockFilter !== "all") {
      params.set("block", blockFilter);
    } else {
      params.delete("block");
    }
    if (parcelFilter && parcelFilter !== "all") {
      params.set("parcel", parcelFilter);
    } else {
      params.delete("parcel");
    }
    if (renovatedFilter && renovatedFilter !== "all") {
      params.set("renovated", renovatedFilter);
    } else {
      params.delete("renovated");
    }
    if (furnishedFilter && furnishedFilter !== "all") {
      params.set("furnished", furnishedFilter);
    } else {
      params.delete("furnished");
    }
    if (airConditioningFilter && airConditioningFilter !== "all") {
      params.set("airConditioning", airConditioningFilter);
    } else {
      params.delete("airConditioning");
    }
    if (storageRoomFilter && storageRoomFilter !== "all") {
      params.set("storageRoom", storageRoomFilter);
    } else {
      params.delete("storageRoom");
    }
    if (hasElevatorFilter && hasElevatorFilter !== "all") {
      params.set("hasElevator", hasElevatorFilter);
    } else {
      params.delete("hasElevator");
    }
    if (recentDealFilter && recentDealFilter !== "all") {
      params.set("recentDeal", recentDealFilter);
    } else {
      params.delete("recentDeal");
    }
    if (modelPriceMin !== undefined) {
      params.set("modelPriceMin", modelPriceMin.toString());
    } else {
      params.delete("modelPriceMin");
    }
    if (modelPriceMax !== undefined) {
      params.set("modelPriceMax", modelPriceMax.toString());
    } else {
      params.delete("modelPriceMax");
    }
    if (antennaDistanceMin !== undefined) {
      params.set("antennaDistanceMin", antennaDistanceMin.toString());
    } else {
      params.delete("antennaDistanceMin");
    }
    if (antennaDistanceMax !== undefined) {
      params.set("antennaDistanceMax", antennaDistanceMax.toString());
    } else {
      params.delete("antennaDistanceMax");
    }
    if (shelterDistanceMin !== undefined) {
      params.set("shelterDistanceMin", shelterDistanceMin.toString());
    } else {
      params.delete("shelterDistanceMin");
    }
    if (shelterDistanceMax !== undefined) {
      params.set("shelterDistanceMax", shelterDistanceMax.toString());
    } else {
      params.delete("shelterDistanceMax");
    }
    if (noiseLevelMin !== undefined) {
      params.set("noiseLevelMin", noiseLevelMin.toString());
    } else {
      params.delete("noiseLevelMin");
    }
    if (noiseLevelMax !== undefined) {
      params.set("noiseLevelMax", noiseLevelMax.toString());
    } else {
      params.delete("noiseLevelMax");
    }
    if (greenWithin300mFilter && greenWithin300mFilter !== "all") {
      params.set("greenWithin300m", greenWithin300mFilter);
    } else {
      params.delete("greenWithin300m");
    }
    if (schoolsWithin500mFilter && schoolsWithin500mFilter !== "all") {
      params.set("schoolsWithin500m", schoolsWithin500mFilter);
    } else {
      params.delete("schoolsWithin500m");
    }
    // High Priority Filters
    if (priceDroppedFilter && priceDroppedFilter !== "all") {
      params.set("priceDropped", priceDroppedFilter);
    } else {
      params.delete("priceDropped");
    }
    if (shelterFilter && shelterFilter !== "all") {
      params.set("shelter", shelterFilter);
    } else {
      params.delete("shelter");
    }
    if (accessibilityFilter && accessibilityFilter !== "all") {
      params.set("accessibility", accessibilityFilter);
    } else {
      params.delete("accessibility");
    }
    if (buildingClassFilter && buildingClassFilter !== "all") {
      params.set("buildingClass", buildingClassFilter);
    } else {
      params.delete("buildingClass");
    }
    if (generalConditionFilter && generalConditionFilter !== "all") {
      params.set("generalCondition", generalConditionFilter);
    } else {
      params.delete("generalCondition");
    }
    if (investmentYieldMin !== undefined) {
      params.set("investmentYieldMin", investmentYieldMin.toString());
    } else {
      params.delete("investmentYieldMin");
    }
    if (investmentYieldMax !== undefined) {
      params.set("investmentYieldMax", investmentYieldMax.toString());
    } else {
      params.delete("investmentYieldMax");
    }
    if (approximateRentMin !== undefined) {
      params.set("approximateRentMin", approximateRentMin.toString());
    } else {
      params.delete("approximateRentMin");
    }
    if (approximateRentMax !== undefined) {
      params.set("approximateRentMax", approximateRentMax.toString());
    } else {
      params.delete("approximateRentMax");
    }
    if (commuteTimeMin !== undefined) {
      params.set("commuteTimeMin", commuteTimeMin.toString());
    } else {
      params.delete("commuteTimeMin");
    }
    if (commuteTimeMax !== undefined) {
      params.set("commuteTimeMax", commuteTimeMax.toString());
    } else {
      params.delete("commuteTimeMax");
    }
    if (publishedDaysMax !== undefined) {
      params.set("publishedDaysMax", publishedDaysMax.toString());
    } else {
      params.delete("publishedDaysMax");
    }
    if (tagBestSchoolFilter && tagBestSchoolFilter !== "all") {
      params.set("tagBestSchool", tagBestSchoolFilter);
    } else {
      params.delete("tagBestSchool");
    }
    if (tagSafetyFilter && tagSafetyFilter !== "all") {
      params.set("tagSafety", tagSafetyFilter);
    } else {
      params.delete("tagSafety");
    }
    if (tagFamilyFriendlyFilter && tagFamilyFriendlyFilter !== "all") {
      params.set("tagFamilyFriendly", tagFamilyFriendlyFilter);
    } else {
      params.delete("tagFamilyFriendly");
    }
    if (tagLightRailFilter && tagLightRailFilter !== "all") {
      params.set("tagLightRail", tagLightRailFilter);
    } else {
      params.delete("tagLightRail");
    }
    if (exclusiveFilter && exclusiveFilter !== "all") {
      params.set("exclusive", exclusiveFilter);
    } else {
      params.delete("exclusive");
    }
    if (pagination.pageIndex > 0) {
      params.set("page", String(pagination.pageIndex + 1));
    } else {
      params.delete("page");
    }
    if (pagination.pageSize !== DEFAULT_PAGE_SIZE) {
      params.set("pageSize", String(pagination.pageSize));
    } else {
      params.delete("pageSize");
    }
    const query = params.toString();
    const newUrl = query ? `${pathname}?${query}` : pathname;
    const currentQuery = searchParams.toString();
    const currentUrl = currentQuery ? `${pathname}?${currentQuery}` : pathname;
    if (newUrl !== currentUrl) {
      router.replace(newUrl, { scroll: false });
    }
  }, [
    debouncedSearch,
    city,
    typeFilter,
    priceMin,
    priceMax,
    neighborhood,
    zoning,
    riskFilter,
    documentsFilter,
    statusFilter,
    sourceFilter,
    rentalSaleFilter,
    sellerTypeFilter,
    commercialFilter,
    userAssetsFilter,
    buildingTypeFilter,
    floorMin,
    floorMax,
    areaMin,
    areaMax,
    bedroomsMin,
    bedroomsMax,
    bathroomsMin,
    bathroomsMax,
    totalFloorsMin,
    totalFloorsMax,
    totalAreaMin,
    totalAreaMax,
    balconyAreaMin,
    balconyAreaMax,
    parkingSpacesMin,
    parkingSpacesMax,
    yearBuiltMin,
    yearBuiltMax,
    rentPriceMin,
    rentPriceMax,
    rentEstimateMin,
    rentEstimateMax,
    priceGapPctMin,
    priceGapPctMax,
    capRatePctMin,
    capRatePctMax,
    roomsFilter,
    featuresFilter,
    pricePerSqmMin,
    pricePerSqmMax,
    remainingRightsMin,
    remainingRightsMax,
    blockFilter,
    parcelFilter,
    renovatedFilter,
    furnishedFilter,
    airConditioningFilter,
    storageRoomFilter,
    hasElevatorFilter,
    recentDealFilter,
    modelPriceMin,
    modelPriceMax,
    antennaDistanceMin,
    antennaDistanceMax,
    shelterDistanceMin,
    shelterDistanceMax,
    noiseLevelMin,
    noiseLevelMax,
    greenWithin300mFilter,
    schoolsWithin500mFilter,
    priceDroppedFilter,
    shelterFilter,
    accessibilityFilter,
    buildingClassFilter,
    generalConditionFilter,
    investmentYieldMin,
    investmentYieldMax,
    approximateRentMin,
    approximateRentMax,
    commuteTimeMin,
    commuteTimeMax,
    publishedDaysMax,
    tagBestSchoolFilter,
    tagSafetyFilter,
    tagFamilyFriendlyFilter,
    tagLightRailFilter,
    exclusiveFilter,
    pagination.pageIndex,
    pagination.pageSize,
    router,
    pathname,
    searchParams,
  ]);

  React.useEffect(() => {
    setPagination(prev => (prev.pageIndex === 0 ? prev : { ...prev, pageIndex: 0 }));
  }, [
    debouncedSearch,
    city,
    typeFilter,
    priceMin,
    priceMax,
    neighborhood,
    zoning,
    riskFilter,
    documentsFilter,
    statusFilter,
    sourceFilter,
    rentalSaleFilter,
    sellerTypeFilter,
    commercialFilter,
    userAssetsFilter,
    buildingTypeFilter,
    floorMin,
    floorMax,
    areaMin,
    areaMax,
    bedroomsMin,
    bedroomsMax,
    bathroomsMin,
    bathroomsMax,
    totalFloorsMin,
    totalFloorsMax,
    totalAreaMin,
    totalAreaMax,
    balconyAreaMin,
    balconyAreaMax,
    parkingSpacesMin,
    parkingSpacesMax,
    yearBuiltMin,
    yearBuiltMax,
    rentPriceMin,
    rentPriceMax,
    rentEstimateMin,
    rentEstimateMax,
    priceGapPctMin,
    priceGapPctMax,
    capRatePctMin,
    capRatePctMax,
    roomsFilter,
    featuresFilter,
    pricePerSqmMin,
    pricePerSqmMax,
    remainingRightsMin,
    remainingRightsMax,
    blockFilter,
    parcelFilter,
    renovatedFilter,
    furnishedFilter,
    airConditioningFilter,
    storageRoomFilter,
    hasElevatorFilter,
    priceDroppedFilter,
    shelterFilter,
    accessibilityFilter,
    buildingClassFilter,
    generalConditionFilter,
    investmentYieldMin,
    investmentYieldMax,
    approximateRentMin,
    approximateRentMax,
    commuteTimeMin,
    commuteTimeMax,
    publishedDaysMax,
    tagBestSchoolFilter,
    tagSafetyFilter,
    tagFamilyFriendlyFilter,
    tagLightRailFilter,
    exclusiveFilter,
  ]);

  // Function to fetch assets
  const buildFilterParams = React.useCallback(() => {
    const params = new URLSearchParams();

    if (debouncedSearch) params.set("search", debouncedSearch);
    if (city && city !== "all") params.set("city", city);
    if (typeFilter && typeFilter !== "all") params.set("type", typeFilter);
    if (priceMin != null) params.set("priceMin", String(priceMin));
    if (priceMax != null) params.set("priceMax", String(priceMax));
    if (neighborhood && neighborhood !== "all") params.set("neighborhood", neighborhood);
    if (zoning && zoning !== "all") params.set("zoning", zoning);
    if (riskFilter && riskFilter !== "all") params.set("risk", riskFilter);
    if (documentsFilter && documentsFilter !== "all") params.set("documents", documentsFilter);
    if (statusFilter && statusFilter !== "all") params.set("status", statusFilter);
    if (sourceFilter && sourceFilter !== "all") params.set("source", sourceFilter);
    if (rentalSaleFilter && rentalSaleFilter !== "all") {
      params.set("listingType", rentalSaleFilter);
      params.delete("rentalSale"); // Remove old param for backward compatibility
    } else {
      params.delete("listingType");
      params.delete("rentalSale");
    }
    if (sellerTypeFilter && sellerTypeFilter !== "all") params.set("sellerType", sellerTypeFilter);
    if (commercialFilter && commercialFilter !== "all") params.set("commercial", commercialFilter);
    if (userAssetsFilter && userAssetsFilter !== "all") params.set("userAssets", userAssetsFilter);
    if (buildingTypeFilter && buildingTypeFilter !== "all") params.set("buildingType", buildingTypeFilter);
    if (floorMin != null) params.set("floorMin", String(floorMin));
    if (floorMax != null) params.set("floorMax", String(floorMax));
    if (areaMin != null) params.set("areaMin", String(areaMin));
    if (areaMax != null) params.set("areaMax", String(areaMax));
    if (bedroomsMin != null) params.set("bedroomsMin", String(bedroomsMin));
    if (bedroomsMax != null) params.set("bedroomsMax", String(bedroomsMax));
    if (bathroomsMin != null) params.set("bathroomsMin", String(bathroomsMin));
    if (bathroomsMax != null) params.set("bathroomsMax", String(bathroomsMax));
    if (totalFloorsMin != null) params.set("totalFloorsMin", String(totalFloorsMin));
    if (totalFloorsMax != null) params.set("totalFloorsMax", String(totalFloorsMax));
    if (totalAreaMin != null) params.set("totalAreaMin", String(totalAreaMin));
    if (totalAreaMax != null) params.set("totalAreaMax", String(totalAreaMax));
    if (balconyAreaMin != null) params.set("balconyAreaMin", String(balconyAreaMin));
    if (balconyAreaMax != null) params.set("balconyAreaMax", String(balconyAreaMax));
    if (parkingSpacesMin != null) params.set("parkingSpacesMin", String(parkingSpacesMin));
    if (parkingSpacesMax != null) params.set("parkingSpacesMax", String(parkingSpacesMax));
    if (yearBuiltMin != null) params.set("yearBuiltMin", String(yearBuiltMin));
    if (yearBuiltMax != null) params.set("yearBuiltMax", String(yearBuiltMax));
    if (rentPriceMin != null) params.set("rentPriceMin", String(rentPriceMin));
    if (rentPriceMax != null) params.set("rentPriceMax", String(rentPriceMax));
    if (rentEstimateMin != null) params.set("rentEstimateMin", String(rentEstimateMin));
    if (rentEstimateMax != null) params.set("rentEstimateMax", String(rentEstimateMax));
    if (priceGapPctMin != null) params.set("priceGapPctMin", String(priceGapPctMin));
    if (priceGapPctMax != null) params.set("priceGapPctMax", String(priceGapPctMax));
    if (capRatePctMin != null) params.set("capRatePctMin", String(capRatePctMin));
    if (capRatePctMax != null) params.set("capRatePctMax", String(capRatePctMax));
    if (roomsFilter && roomsFilter !== "all") params.set("rooms", roomsFilter);
    if (featuresFilter && featuresFilter !== "all") params.set("features", featuresFilter);
    if (pricePerSqmMin != null) params.set("pricePerSqmMin", String(pricePerSqmMin));
    if (pricePerSqmMax != null) params.set("pricePerSqmMax", String(pricePerSqmMax));
    if (remainingRightsMin != null) params.set("remainingRightsMin", String(remainingRightsMin));
    if (remainingRightsMax != null) params.set("remainingRightsMax", String(remainingRightsMax));
    if (blockFilter && blockFilter !== "all") params.set("block", blockFilter);
    if (parcelFilter && parcelFilter !== "all") params.set("parcel", parcelFilter);
    if (renovatedFilter && renovatedFilter !== "all") params.set("renovated", renovatedFilter);
    if (furnishedFilter && furnishedFilter !== "all") params.set("furnished", furnishedFilter);
    if (airConditioningFilter && airConditioningFilter !== "all") params.set("airConditioning", airConditioningFilter);
    if (storageRoomFilter && storageRoomFilter !== "all") params.set("storageRoom", storageRoomFilter);
    if (hasElevatorFilter && hasElevatorFilter !== "all") params.set("hasElevator", hasElevatorFilter);
    if (recentDealFilter && recentDealFilter !== "all") params.set("recentDeal", recentDealFilter);
    if (modelPriceMin != null) params.set("modelPriceMin", String(modelPriceMin));
    if (modelPriceMax != null) params.set("modelPriceMax", String(modelPriceMax));
    if (antennaDistanceMin != null) params.set("antennaDistanceMin", String(antennaDistanceMin));
    if (antennaDistanceMax != null) params.set("antennaDistanceMax", String(antennaDistanceMax));
    if (shelterDistanceMin != null) params.set("shelterDistanceMin", String(shelterDistanceMin));
    if (shelterDistanceMax != null) params.set("shelterDistanceMax", String(shelterDistanceMax));
    if (noiseLevelMin != null) params.set("noiseLevelMin", String(noiseLevelMin));
    if (noiseLevelMax != null) params.set("noiseLevelMax", String(noiseLevelMax));
    if (greenWithin300mFilter && greenWithin300mFilter !== "all") params.set("greenWithin300m", greenWithin300mFilter);
    if (schoolsWithin500mFilter && schoolsWithin500mFilter !== "all") params.set("schoolsWithin500m", schoolsWithin500mFilter);
    // High Priority Filters
    if (priceDroppedFilter && priceDroppedFilter !== "all") params.set("priceDropped", priceDroppedFilter);
    if (shelterFilter && shelterFilter !== "all") params.set("shelter", shelterFilter);
    if (accessibilityFilter && accessibilityFilter !== "all") params.set("accessibility", accessibilityFilter);
    if (buildingClassFilter && buildingClassFilter !== "all") params.set("buildingClass", buildingClassFilter);
    if (generalConditionFilter && generalConditionFilter !== "all") params.set("generalCondition", generalConditionFilter);
    if (investmentYieldMin != null) params.set("investmentYieldMin", String(investmentYieldMin));
    if (investmentYieldMax != null) params.set("investmentYieldMax", String(investmentYieldMax));
    if (approximateRentMin != null) params.set("approximateRentMin", String(approximateRentMin));
    if (approximateRentMax != null) params.set("approximateRentMax", String(approximateRentMax));
    if (commuteTimeMin != null) params.set("commuteTimeMin", String(commuteTimeMin));
    if (commuteTimeMax != null) params.set("commuteTimeMax", String(commuteTimeMax));
    if (publishedDaysMax != null) params.set("publishedDaysMax", String(publishedDaysMax));
    if (tagBestSchoolFilter && tagBestSchoolFilter !== "all") params.set("tagBestSchool", tagBestSchoolFilter);
    if (tagSafetyFilter && tagSafetyFilter !== "all") params.set("tagSafety", tagSafetyFilter);
    if (tagFamilyFriendlyFilter && tagFamilyFriendlyFilter !== "all") params.set("tagFamilyFriendly", tagFamilyFriendlyFilter);
    if (tagLightRailFilter && tagLightRailFilter !== "all") params.set("tagLightRail", tagLightRailFilter);
    if (exclusiveFilter && exclusiveFilter !== "all") params.set("exclusive", exclusiveFilter);

    return params;
  }, [
    debouncedSearch,
    city,
    typeFilter,
    priceMin,
    priceMax,
    neighborhood,
    zoning,
    riskFilter,
    documentsFilter,
    statusFilter,
    sourceFilter,
    rentalSaleFilter,
    sellerTypeFilter,
    commercialFilter,
    userAssetsFilter,
    buildingTypeFilter,
    floorMin,
    floorMax,
    areaMin,
    areaMax,
    bedroomsMin,
    bedroomsMax,
    bathroomsMin,
    bathroomsMax,
    totalFloorsMin,
    totalFloorsMax,
    totalAreaMin,
    totalAreaMax,
    balconyAreaMin,
    balconyAreaMax,
    parkingSpacesMin,
    parkingSpacesMax,
    yearBuiltMin,
    yearBuiltMax,
    rentPriceMin,
    rentPriceMax,
    rentEstimateMin,
    rentEstimateMax,
    priceGapPctMin,
    priceGapPctMax,
    capRatePctMin,
    capRatePctMax,
    roomsFilter,
    featuresFilter,
    pricePerSqmMin,
    pricePerSqmMax,
    remainingRightsMin,
    remainingRightsMax,
    blockFilter,
    parcelFilter,
    renovatedFilter,
    furnishedFilter,
    airConditioningFilter,
    storageRoomFilter,
    hasElevatorFilter,
    recentDealFilter,
    modelPriceMin,
    modelPriceMax,
    antennaDistanceMin,
    antennaDistanceMax,
    shelterDistanceMin,
    shelterDistanceMax,
    noiseLevelMin,
    noiseLevelMax,
    greenWithin300mFilter,
    schoolsWithin500mFilter,
    priceDroppedFilter,
    shelterFilter,
    accessibilityFilter,
    buildingClassFilter,
    generalConditionFilter,
    investmentYieldMin,
    investmentYieldMax,
    approximateRentMin,
    approximateRentMax,
    commuteTimeMin,
    commuteTimeMax,
    publishedDaysMax,
    tagBestSchoolFilter,
    tagSafetyFilter,
    tagFamilyFriendlyFilter,
    tagLightRailFilter,
    exclusiveFilter,
  ]);

  const fetchFilterMetadata = React.useCallback(async () => {
    // Only fetch if not already loaded
    if (filterMetadata.cities.length > 0) {
      return;
    }
    
    try {
      const response = await apiClient.get("/api/assets/filter-metadata");
      if (response.ok && response.data) {
        const filters = response.data as Partial<AssetFilterMetadata>;
        setFilterMetadata({
          cities: filters.cities ?? [],
          types: filters.types ?? [],
          neighborhoods: filters.neighborhoods ?? [],
          zonings: filters.zonings ?? [],
          blocks: filters.blocks ?? [],
          parcels: filters.parcels ?? [],
          sources: filters.sources ?? [],
          buildingTypes: filters.buildingTypes ?? [],
          rooms: filters.rooms ?? [],
          statusCounts: filters.statusCounts ?? {},
          bedroomCounts: filters.bedroomCounts ?? [],
          bathroomCounts: filters.bathroomCounts ?? [],
          totalFloorCounts: filters.totalFloorCounts ?? [],
          parkingSpaceCounts: filters.parkingSpaceCounts ?? [],
          balconyAreas: filters.balconyAreas ?? [],
          totalAreaRange: filters.totalAreaRange ?? { min: null, max: null },
          yearBuiltRange: filters.yearBuiltRange ?? { min: null, max: null },
          rentPriceRange: filters.rentPriceRange ?? { min: null, max: null },
          rentEstimateRange: filters.rentEstimateRange ?? { min: null, max: null },
          priceGapPctRange: filters.priceGapPctRange ?? { min: null, max: null },
          capRatePctRange: filters.capRatePctRange ?? { min: null, max: null },
          bedroomRange: filters.bedroomRange ?? { min: null, max: null },
          bathroomRange: filters.bathroomRange ?? { min: null, max: null },
          totalFloorRange: filters.totalFloorRange ?? { min: null, max: null },
          parkingSpaceRange: filters.parkingSpaceRange ?? { min: null, max: null },
          balconyAreaRange: filters.balconyAreaRange ?? { min: null, max: null },
        });
      }
    } catch (error) {
      console.error("Error fetching filter metadata:", error);
      // Don't show error to user, filters are optional
    }
  }, [filterMetadata.cities.length]);

  const fetchAssets = React.useCallback(async () => {
    try {
      setLoading(true);

      const isDefaultPageIndex = pagination.pageIndex === 0;
      const isDefaultPageSize = pagination.pageSize === DEFAULT_PAGE_SIZE;

      const params = buildFilterParams();

      if (!isDefaultPageIndex) {
        params.set("page", String(pagination.pageIndex + 1));
      }

      if (!isDefaultPageSize) {
        params.set("pageSize", String(pagination.pageSize));
      }

      // Add ordering parameter from sorting state
      if (sorting.length > 0) {
        const sortMapping: Record<string, string> = {
          address: 'address',
          city: 'city',
          street: 'street',
          number: 'number',
          apartment: 'apartment',
          block: 'block',
          parcel: 'parcel',
          subparcel: 'subparcel',
          area: 'area',
          totalArea: 'total_area',
          subparcelArea: 'subparcel_area',
          builtArea: 'built_area',
          floor: 'floor',
          totalFloors: 'total_floors',
          listingType: 'listing_type',
          adType: 'ad_type',
          price: 'price',
          rentPrice: 'rent_price',
          pricePerSqm: 'price_per_sqm',
          deltaVsAreaPct: 'delta_vs_area_pct',
          domPercentile: 'dom_percentile',
          competition1km: 'competition_1km',
          zoning: 'zoning',
          remainingRightsSqm: 'remaining_rights_sqm',
          program: 'program',
          lastPermitQ: 'last_permit_q',
          docsCount: 'documents_count',
          noiseLevel: 'noise_level',
          antennaDistanceM: 'antenna_distance_m',
          greenWithin300m: 'green_within_300m',
          shelterDistanceM: 'shelter_distance_m',
          assetStatus: 'asset_status',
          modelPrice: 'model_price',
          priceGapPct: 'price_gap_pct',
          confidencePct: 'confidence_pct',
          capRatePct: 'cap_rate_pct',
          rentEstimate: 'rent_estimate',
          recentDeal: 'recent_deal',
        };

        const primarySort = sorting[0];
        const backendField = sortMapping[primarySort.id] || 'created_at';
        const orderingValue = primarySort.desc ? `-${backendField}` : backendField;
        params.set("ordering", orderingValue);
      }

      const query = params.toString();
      const endpoint = query ? `/api/assets?${query}` : "/api/assets";
      const response = await apiClient.get(endpoint);

      if (response.ok) {
        const rows = response.data?.rows ?? [];
        const paginationInfo = response.data?.pagination;
        const total = paginationInfo?.total ?? rows.length;
        const pageSizeFromApi = paginationInfo?.page_size ?? pagination.pageSize;
        const requestedPageIndex = paginationInfo
          ? Math.max(0, (paginationInfo.page ?? 1) - 1)
          : pagination.pageIndex;
        const lastPageIndex = total > 0 ? Math.max(0, Math.ceil(total / pageSizeFromApi) - 1) : 0;
        const adjustedPageIndex = Math.min(requestedPageIndex, lastPageIndex);

        setTotalCount(total);

        if (rows.length === 0 && total > 0 && requestedPageIndex !== adjustedPageIndex) {
          setPagination(prev => {
            if (prev.pageIndex === adjustedPageIndex && prev.pageSize === pageSizeFromApi) {
              return prev;
            }
            return { pageIndex: adjustedPageIndex, pageSize: pageSizeFromApi };
          });
          return;
        }

        setAssets(rows);

        // Track asset list view
        const category = typeFilter !== "all" ? typeFilter : undefined;
        trackEvent("view_asset_list", {
          category: category || "all",
          total_count: total,
        });

        if (paginationInfo) {
          setPagination(prev => {
            if (prev.pageIndex === adjustedPageIndex && prev.pageSize === pageSizeFromApi) {
              return prev;
            }
            return { pageIndex: adjustedPageIndex, pageSize: pageSizeFromApi };
          });
        } else if (pageSizeFromApi !== pagination.pageSize) {
          setPagination(prev => {
            if (prev.pageSize === pageSizeFromApi) {
              return prev;
            }
            return { ...prev, pageSize: pageSizeFromApi };
          });
        }
      } else {
        console.error("Failed to fetch assets:", response.error);
      }
    } catch (error) {
      console.error("Error fetching assets:", error);
    } finally {
      setLoading(false);
    }
  }, [
    pagination.pageIndex,
    pagination.pageSize,
    sorting,
    buildFilterParams,
  ]);

  // Reset to first page when sorting changes
  React.useEffect(() => {
    setPagination(prev => (prev.pageIndex !== 0 ? { ...prev, pageIndex: 0 } : prev));
  }, [sorting]);

  // Fetch filter metadata once on initial load
  React.useEffect(() => {
    fetchFilterMetadata();
  }, [fetchFilterMetadata]);

  const updateAssetsWatchState = React.useCallback((ids: number[], watched: boolean) => {
    if (!ids.length) return;
    setAssets(prev => {
      if (!prev.length) {
        return prev;
      }
      const idSet = new Set(ids);
      let didChange = false;
      const next = prev.map(asset => {
        if (!idSet.has(asset.id)) {
          return asset;
        }
        if (asset.isWatched === watched) {
          return asset;
        }
        didChange = true;
        return { ...asset, isWatched: watched };
      });
      return didChange ? next : prev;
    });
  }, []);

  const handleToggleWatch = React.useCallback(
    async (asset: Asset) => {
      if (!isAuthenticated) {
        toast({
          title: "נדרשת התחברות",
          description: "עליך להתחבר כדי לנהל רשימת מעקב",
          variant: "destructive",
        });
        router.push("/auth?redirect=" + encodeURIComponent("/assets"));
        return;
      }

      const nextWatched = !(asset.isWatched ?? false);

      setWatchingAssetIds(prev => {
        const next = new Set(prev);
        next.add(asset.id);
        return next;
      });

      try {
        const response = await apiClient.request(`/api/assets/${asset.id}/watch`, {
          method: nextWatched ? "POST" : "DELETE",
        });

        if (response.ok) {
          if (!nextWatched && userAssetsFilter === "watchlist") {
            setAssets(prev => {
              const next = prev.filter(item => item.id !== asset.id);
              if (next.length !== prev.length) {
                setTotalCount(current => Math.max(0, current - 1));
              }
              return next;
            });
          } else {
            updateAssetsWatchState([asset.id], nextWatched);
          }
          toast({
            title: nextWatched ? "נוסף לרשימת המעקב" : "הוסר מרשימת המעקב",
            description: asset.address ?? undefined,
            variant: "success",
          });
        } else {
          toast({
            title: "שגיאה בעדכון רשימת המעקב",
            description: getUserFriendlyError(response),
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error("Error updating watchlist:", error);
        toast({
          title: "שגיאה בעדכון רשימת המעקב",
          description: getUserFriendlyError(error),
          variant: "destructive",
        });
      } finally {
        setWatchingAssetIds(prev => {
          const next = new Set(prev);
          next.delete(asset.id);
          return next;
        });
      }
    },
    [isAuthenticated, router, toast, updateAssetsWatchState, userAssetsFilter]
  );

  const handleExportAllAssets = React.useCallback(async () => {
    const EXPORT_PAGE_SIZE = 100;

    try {
      const baseParams = buildFilterParams();
      baseParams.set("pageSize", String(EXPORT_PAGE_SIZE));

      const allAssets: Asset[] = [];
      let page = 1;

      while (true) {
        const pageParams = new URLSearchParams(baseParams);
        pageParams.set("page", String(page));

        const query = pageParams.toString();
        const endpoint = query ? `/api/assets?${query}` : "/api/assets";
        const response = await apiClient.get(endpoint);

        if (!response.ok) {
          throw new Error(response.error || "Failed to fetch assets for export");
        }

        const rows = (Array.isArray(response.data?.rows) ? response.data?.rows : []) as Asset[];
        allAssets.push(...rows);

        const paginationInfo = response.data?.pagination;

        if (!paginationInfo) {
          if (rows.length < EXPORT_PAGE_SIZE) {
            break;
          }
        } else {
          const total = paginationInfo.total ?? allAssets.length;
          const pageSizeFromApi = paginationInfo.page_size ?? EXPORT_PAGE_SIZE;
          const currentPage = paginationInfo.page ?? page;

          if (pageSizeFromApi <= 0) {
            break;
          }
          if (currentPage * pageSizeFromApi >= total) {
            break;
          }
        }

        page += 1;
        if (page > 1000) {
          console.warn("Aborting export after 1000 pages to prevent infinite loop");
          break;
        }
      }

      return allAssets;
    } catch (error) {
      console.error("Error exporting all assets:", error);
      toast({
        title: "שגיאה בייצוא",
          description: getUserFriendlyError(error),
        variant: "destructive",
      });
      throw error;
    }
  }, [buildFilterParams, toast]);

  const handleDeleteAsset = async (assetId: number) => {
    // Check if user is authenticated
    if (!isAuthenticated) {
      toast({
        title: "נדרשת התחברות",
        description: "עליך להתחבר כדי למחוק נכסים",
        variant: "destructive",
      });
      router.push("/auth?redirect=" + encodeURIComponent("/assets"));
      return;
    }

    if (!isAdmin) {
      toast({
        title: "אין הרשאות", 
        description: "רק מנהל מערכת יכול למחוק נכסים", 
        variant: "destructive",
      });
      return;
    }

    const confirmed = await confirm({
      title: "מחיקת נכס",
      description: "האם אתה בטוח שברצונך למחוק נכס זה? פעולה זו לא ניתנת לביטול.",
      confirmText: "מחק",
      cancelText: "ביטול",
      variant: "destructive",
    });

    if (!confirmed) {
      return;
    }

    setDeleting(assetId);
    try {
      const response = await apiClient.request("/api/assets", {
        method: "DELETE",
        body: JSON.stringify({ assetId }),
      });

      if (response.ok) {
        await fetchAssets();
        toast({
          title: "הצלחה",
          description: "הנכס נמחק בהצלחה",
          variant: "success",
        });
      } else {
        toast({
          title: "שגיאה",
          description: getUserFriendlyError(response),
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error deleting asset:", error);
      toast({
        title: "שגיאה",
        description: getUserFriendlyError(error),
        variant: "destructive",
      });
    } finally {
      setDeleting(null);
    }
  };

  // Bulk actions
  type BulkActionHelpers = { clearSelection: () => void };
  type BulkActionResponseData = {
    success?: number;
    failed?: number;
    notFound?: number;
    message?: string;
    results?: Array<{ assetId: number; status: string }>;
  };

  const summarizeBulkAction = (label: string, data?: BulkActionResponseData) => {
    if (!data) return `${label} הושלמה`;
    if (data.message) return data.message;
    const success = data.success ?? 0;
    const failed = data.failed ?? 0;
    const notFound = data.notFound ?? 0;
    const parts: string[] = [];
    if (success) parts.push(`${success} הצליחו`);
    if (failed) parts.push(`${failed} נכשלו`);
    if (notFound) parts.push(`${notFound} לא נמצאו`);
    if (parts.length === 0) {
      return `${label} הושלמה`;
    }
    return `${label}: ${parts.join(" · ")}`;
  };

  const getSuccessfulIds = (data?: BulkActionResponseData) => {
    if (!data || !Array.isArray(data.results)) return [] as number[];
    return data.results.filter(result => result.status === "success").map(result => result.assetId);
  };

  const handleBulkDelete = async (selectedAssets: Asset[], { clearSelection }: BulkActionHelpers) => {
    if (!selectedAssets.length) return;

    if (!isAuthenticated) {
      toast({
        title: "נדרשת התחברות",
        description: "עליך להתחבר כדי למחוק נכסים",
        variant: "destructive",
      });
      router.push("/auth?redirect=" + encodeURIComponent("/assets"));
      return;
    }

    if (!isAdmin) {
      toast({
        title: "אין הרשאות",
        description: "רק מנהל מערכת יכול למחוק נכסים",
        variant: "destructive",
      });
      return;
    }

    const confirmed = await confirm({
      title: "מחיקת נכסים נבחרים",
      description: `האם אתה בטוח שברצונך למחוק ${selectedAssets.length} נכסים? פעולה זו לא ניתנת לביטול.`,
      confirmText: "מחק הכל",
      cancelText: "ביטול",
      variant: "destructive",
    });

    if (!confirmed) return;

    const assetIds = selectedAssets.map(asset => asset.id);

    try {
      const response = await apiClient.request<BulkActionResponseData>("/api/assets/bulk-action", {
        method: "POST",
        body: JSON.stringify({ action: "delete", assetIds }),
      });

      if (response.ok) {
        const successfulIds = getSuccessfulIds(response.data);
        if (successfulIds.length > 0) {
          setAssets(prev => prev.filter(asset => !successfulIds.includes(asset.id)));
          await fetchAssets();
        }
        toast({
          title: "מחיקה מרובה",
          description: summarizeBulkAction("מחיקה", response.data),
          variant: response.data && (response.data.failed || response.data.notFound) ? "default" : "success",
        });
        clearSelection();
      } else {
        toast({
          title: "שגיאה במחיקה מרובה",
            description: getUserFriendlyError(response),
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error performing bulk delete:", error);
      toast({
        title: "שגיאה במחיקה מרובה",
          description: getUserFriendlyError(error),
        variant: "destructive",
      });
    }
  };

  const handleBulkSync = async (selectedAssets: Asset[], { clearSelection }: BulkActionHelpers) => {
    if (!selectedAssets.length) return;

    if (!isAuthenticated) {
      toast({
        title: "נדרשת התחברות",
        description: "עליך להתחבר כדי לבצע סנכרון נתונים",
        variant: "destructive",
      });
      router.push("/auth?redirect=" + encodeURIComponent("/assets"));
      return;
    }

    const assetIds = selectedAssets.map(asset => asset.id);

    try {
      const response = await apiClient.request<BulkActionResponseData>("/api/assets/bulk-action", {
        method: "POST",
        body: JSON.stringify({ action: "sync", assetIds }),
      });

      if (response.ok) {
        const successfulIds = getSuccessfulIds(response.data);
        if (successfulIds.length > 0) {
          setAssets(prev =>
            prev.map(asset =>
              successfulIds.includes(asset.id)
                ? { ...asset, assetStatus: "syncing" }
                : asset
            )
          );
        }
        toast({
          title: "סנכרון נתונים",
          description: summarizeBulkAction("סנכרון", response.data),
          variant: response.data && (response.data.failed || response.data.notFound) ? "default" : "success",
        });
        clearSelection();
      } else {
        toast({
          title: "שגיאה בסנכרון",
            description: getUserFriendlyError(response),
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error performing bulk sync:", error);
      toast({
        title: "שגיאה בסנכרון",
          description: getUserFriendlyError(error),
        variant: "destructive",
      });
    }
  };

  const handleBulkWatch = async (selectedAssets: Asset[], { clearSelection }: BulkActionHelpers) => {
    if (!selectedAssets.length) return;

    if (!isAuthenticated) {
      toast({
        title: "נדרשת התחברות",
        description: "עליך להתחבר כדי לנהל רשימת מעקב",
        variant: "destructive",
      });
      router.push("/auth?redirect=" + encodeURIComponent("/assets"));
      return;
    }

    const assetIds = selectedAssets.map(asset => asset.id);

    try {
      const response = await apiClient.request<BulkActionResponseData>("/api/assets/bulk-action", {
        method: "POST",
        body: JSON.stringify({ action: "watch", assetIds }),
      });

      if (response.ok) {
        const successfulIds = getSuccessfulIds(response.data);
        if (successfulIds.length > 0) {
          updateAssetsWatchState(successfulIds, true);
        }
        toast({
          title: "הוספה למעקב",
          description: summarizeBulkAction("הוספה למעקב", response.data),
          variant: response.data && (response.data.failed || response.data.notFound) ? "default" : "success",
        });
        clearSelection();
      } else {
        toast({
          title: "שגיאה בהוספה למעקב",
            description: getUserFriendlyError(response),
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error performing bulk watch:", error);
      toast({
        title: "שגיאה בהוספה למעקב",
          description: getUserFriendlyError(error),
        variant: "destructive",
      });
    }
  };

  const handleBulkUnwatch = async (selectedAssets: Asset[], { clearSelection }: BulkActionHelpers) => {
    if (!selectedAssets.length) return;

    if (!isAuthenticated) {
      toast({
        title: "נדרשת התחברות",
        description: "עליך להתחבר כדי לנהל רשימת מעקב",
        variant: "destructive",
      });
      router.push("/auth?redirect=" + encodeURIComponent("/assets"));
      return;
    }

    const assetIds = selectedAssets.map(asset => asset.id);

    try {
      const response = await apiClient.request<BulkActionResponseData>("/api/assets/bulk-action", {
        method: "POST",
        body: JSON.stringify({ action: "unwatch", assetIds }),
      });

      if (response.ok) {
        const successfulIds = getSuccessfulIds(response.data);
        if (successfulIds.length > 0) {
          if (userAssetsFilter === "watchlist") {
            setAssets(prev => {
              const idSet = new Set(successfulIds);
              const next = prev.filter(asset => !idSet.has(asset.id));
              const removedCount = prev.length - next.length;
              if (removedCount > 0) {
                setTotalCount(current => Math.max(0, current - removedCount));
              }
              return next;
            });
          } else {
            updateAssetsWatchState(successfulIds, false);
          }
        }
        toast({
          title: "הסרה ממעקב",
          description: summarizeBulkAction("הסרה ממעקב", response.data),
          variant: response.data && (response.data.failed || response.data.notFound) ? "default" : "success",
        });
        clearSelection();
      } else {
        toast({
          title: "שגיאה בהסרה ממעקב",
            description: getUserFriendlyError(response),
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error performing bulk unwatch:", error);
      toast({
        title: "שגיאה בהסרה ממעקב",
          description: getUserFriendlyError(error),
        variant: "destructive",
      });
    }
  };

  const handleBulkCreateReports = async (selectedAssets: Asset[], { clearSelection }: BulkActionHelpers) => {
    if (!selectedAssets.length) return;

    if (!isAuthenticated) {
      toast({
        title: "נדרשת התחברות",
        description: "עליך להתחבר כדי ליצור דוחות",
        variant: "destructive",
      });
      router.push("/auth?redirect=" + encodeURIComponent("/assets"));
      return;
    }

    const assetIds = selectedAssets.map(asset => asset.id);

    try {
      const response = await apiClient.request<BulkActionResponseData>("/api/assets/bulk-action", {
        method: "POST",
        body: JSON.stringify({ action: "create_report", assetIds }),
      });

      if (response.ok) {
        toast({
          title: "יצירת דוחות",
          description: summarizeBulkAction("יצירת דוחות", response.data),
          variant: response.data && (response.data.failed || response.data.notFound) ? "default" : "success",
        });
        clearSelection();
      } else {
        toast({
          title: "שגיאה ביצירת דוחות",
            description: getUserFriendlyError(response),
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error creating bulk reports:", error);
      toast({
        title: "שגיאה ביצירת דוחות",
          description: getUserFriendlyError(error),
        variant: "destructive",
      });
    }
  };

  const handleBulkExport = (selectedAssets: Asset[], { clearSelection }: BulkActionHelpers) => {
    toast({
      title: "ייצוא מרובה",
      description: `ייצוא ${selectedAssets.length} נכסים נבחרים החל`,
    });
    clearSelection();
  };

  const newAssetSchema = z
    .object({
      locationType: z.enum(["address", "parcel"]),
      city: z.string().optional(),
      street: z.string().optional(),
      houseNumber: z.string().optional(),
      apartment: z.string().optional(),
      block: z.string().optional(),
      parcel: z.string().optional(),
      subparcel: z.string().optional(),
      radius: z.number().int().positive().default(DEFAULT_RADIUS_METERS),
    })
    .superRefine((data, ctx) => {
      if (data.locationType === "address") {
        if (!data.city) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["city"],
            message: "עיר נדרשת",
          });
        }
        if (!data.street) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["street"],
            message: "רחוב נדרש",
          });
        }
      } else {
        if (!data.block) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["block"],
            message: "גוש נדרש",
          });
        }
        if (!data.parcel) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["parcel"],
            message: "חלקה נדרשת",
          });
        }
      }
    });

  type NewAsset = z.infer<typeof newAssetSchema>;

  const form = useForm<NewAsset>({
    resolver: zodResolver(newAssetSchema),
    defaultValues: {
      locationType: "address",
      city: "",
      street: "",
      houseNumber: "",
      apartment: "",
      block: "",
      parcel: "",
      subparcel: "",
      radius: DEFAULT_RADIUS_METERS,
    },
  });

  const onSubmit = async (data: NewAsset) => {
    const radius = data.radius ?? DEFAULT_RADIUS_METERS;
    try {
      const body =
        data.locationType === "address"
          ? {
              scope: {
                type: "address",
                value: `${data.street} ${data.houseNumber ?? ""}`.trim(),
                city: data.city,
              },
              city: data.city,
              street: data.street,
              number: data.houseNumber ? Number(data.houseNumber) : undefined,
              apartment: data.apartment,
              radius,
            }
          : {
              scope: {
                type: "parcel",
                value: `${data.block}/${data.parcel}`,
              },
              block: data.block,
              parcel: data.parcel,
              subparcel: data.subparcel,
              radius,
            };

      const response = await apiClient.request("/api/assets", {
        method: "POST",
        body: JSON.stringify(body),
      });

      if (response.ok) {
        const createdAsset = response.data?.asset || response.data;
        const newAssetId = createdAsset?.id ?? createdAsset?.assetId;

        // Track asset creation
        const assetType = data.locationType === "address" ? "address" : "parcel";
        trackEvent("create_asset", {
          asset_type: assetType,
          city: data.city || undefined,
        });

        form.reset();
        setOpen(false);
        // Refresh user data to update onboarding progress
        await refreshUser();

        if (newAssetId) {
          // Keep the assets list fresh if the user navigates back
          void fetchAssets();
          toast({
            title: "הצלחה",
            description: "הנכס נוסף בהצלחה, אנחנו מכינים את הנתונים עבורך",
            variant: "success",
          });
          router.push(`/assets/${newAssetId}`);
        } else {
          // Refresh assets to show the new asset when id is missing for any reason
          await fetchAssets();
          toast({
            title: "הצלחה",
            description: "הנכס נוסף בהצלחה",
            variant: "success",
          });
        }
      } else {
        console.error("Failed to create asset:", response.error);
        
        // Handle plan limit errors
        if (response.status === 403 && response.data?.error === 'asset_limit_exceeded') {
          setPlanLimitError(response.data);
          setShowPlanLimitDialog(true);
        } else {
          toast({
            title: "שגיאה",
            description: getUserFriendlyError(response),
            variant: "destructive",
          });
        }
      }
    } catch (error) {
      console.error("Error creating asset:", error);
      toast({
        title: "שגיאה",
        description: getUserFriendlyError(error),
        variant: "destructive",
      });
    }
  };

  useDedupedEffect(() => {
    fetchAssets();
  }, [fetchAssets]);

  const pageCount = React.useMemo(
    () => (totalCount === 0 ? 1 : Math.ceil(totalCount / pagination.pageSize)),
    [totalCount, pagination.pageSize]
  );

  // Build current filter state for saving
  const buildCurrentFilters = React.useCallback(() => {
    return {
      search: debouncedSearch,
      city,
      type: typeFilter,
      priceMin,
      priceMax,
      neighborhood,
      zoning,
      risk: riskFilter,
      documents: documentsFilter,
      status: statusFilter,
      source: sourceFilter,
      rentalSale: rentalSaleFilter,
      sellerType: sellerTypeFilter,
      commercial: commercialFilter,
      userAssets: userAssetsFilter,
      buildingType: buildingTypeFilter,
      floorMin,
      floorMax,
      areaMin,
      areaMax,
      bedroomsMin,
      bedroomsMax,
      bathroomsMin,
      bathroomsMax,
      totalFloorsMin,
      totalFloorsMax,
      totalAreaMin,
      totalAreaMax,
      balconyAreaMin,
      balconyAreaMax,
      parkingSpacesMin,
      parkingSpacesMax,
      yearBuiltMin,
      yearBuiltMax,
      rentPriceMin,
      rentPriceMax,
      rentEstimateMin,
      rentEstimateMax,
      priceGapPctMin,
      priceGapPctMax,
      capRatePctMin,
      capRatePctMax,
      rooms: roomsFilter,
      features: featuresFilter,
      renovated: renovatedFilter,
      furnished: furnishedFilter,
      airConditioning: airConditioningFilter,
      storageRoom: storageRoomFilter,
      hasElevator: hasElevatorFilter,
      block: blockFilter,
      parcel: parcelFilter,
      pricePerSqmMin,
      pricePerSqmMax,
      remainingRightsMin,
      remainingRightsMax,
    };
  }, [
    debouncedSearch, city, typeFilter, priceMin, priceMax, neighborhood, zoning, riskFilter,
    documentsFilter, statusFilter, sourceFilter, rentalSaleFilter, sellerTypeFilter, commercialFilter,
    userAssetsFilter, buildingTypeFilter, floorMin, floorMax, areaMin, areaMax,
    bedroomsMin, bedroomsMax, bathroomsMin, bathroomsMax, totalFloorsMin, totalFloorsMax,
    totalAreaMin, totalAreaMax, balconyAreaMin, balconyAreaMax, parkingSpacesMin, parkingSpacesMax,
    yearBuiltMin, yearBuiltMax, rentPriceMin, rentPriceMax, rentEstimateMin, rentEstimateMax,
    priceGapPctMin, priceGapPctMax, capRatePctMin, capRatePctMax, roomsFilter, featuresFilter,
    renovatedFilter, furnishedFilter, airConditioningFilter, storageRoomFilter, hasElevatorFilter,
    blockFilter, parcelFilter, pricePerSqmMin, pricePerSqmMax, remainingRightsMin, remainingRightsMax,
  ]);

  // Apply saved filter
  const handleApplyFilter = React.useCallback((filterData: Record<string, any>) => {
    if (filterData.search !== undefined) {
      const searchValue = filterData.search || '';
      setSearchInput(searchValue);
      setDebouncedSearch(searchValue);
    }
    if (filterData.city !== undefined) setCity(filterData.city || 'all');
    if (filterData.type !== undefined) setTypeFilter(filterData.type || 'all');
    if (filterData.priceMin !== undefined) setPriceMin(filterData.priceMin);
    if (filterData.priceMax !== undefined) setPriceMax(filterData.priceMax);
    if (filterData.neighborhood !== undefined) setNeighborhood(filterData.neighborhood || 'all');
    if (filterData.zoning !== undefined) setZoning(filterData.zoning || 'all');
    if (filterData.risk !== undefined) setRiskFilter(filterData.risk || 'all');
    if (filterData.documents !== undefined) setDocumentsFilter(filterData.documents || 'all');
    if (filterData.status !== undefined) setStatusFilter(filterData.status || 'all');
    if (filterData.source !== undefined) setSourceFilter(filterData.source || 'all');
    if (filterData.rentalSale !== undefined) setRentalSaleFilter(filterData.rentalSale || 'all');
    if (filterData.sellerType !== undefined) setSellerTypeFilter(filterData.sellerType || 'all');
    if (filterData.adType !== undefined) setSellerTypeFilter(filterData.adType || 'all'); // Backward compatibility
    if (filterData.commercial !== undefined) setCommercialFilter(filterData.commercial || 'all');
    if (filterData.userAssets !== undefined) setUserAssetsFilter(filterData.userAssets || 'all');
    if (filterData.buildingType !== undefined) setBuildingTypeFilter(filterData.buildingType || 'all');
    if (filterData.floorMin !== undefined) setFloorMin(filterData.floorMin);
    if (filterData.floorMax !== undefined) setFloorMax(filterData.floorMax);
    if (filterData.areaMin !== undefined) setAreaMin(filterData.areaMin);
    if (filterData.areaMax !== undefined) setAreaMax(filterData.areaMax);
    if (filterData.bedroomsMin !== undefined) setBedroomsMin(filterData.bedroomsMin);
    if (filterData.bedroomsMax !== undefined) setBedroomsMax(filterData.bedroomsMax);
    if (filterData.bathroomsMin !== undefined) setBathroomsMin(filterData.bathroomsMin);
    if (filterData.bathroomsMax !== undefined) setBathroomsMax(filterData.bathroomsMax);
    if (filterData.totalFloorsMin !== undefined) setTotalFloorsMin(filterData.totalFloorsMin);
    if (filterData.totalFloorsMax !== undefined) setTotalFloorsMax(filterData.totalFloorsMax);
    if (filterData.totalAreaMin !== undefined) setTotalAreaMin(filterData.totalAreaMin);
    if (filterData.totalAreaMax !== undefined) setTotalAreaMax(filterData.totalAreaMax);
    if (filterData.balconyAreaMin !== undefined) setBalconyAreaMin(filterData.balconyAreaMin);
    if (filterData.balconyAreaMax !== undefined) setBalconyAreaMax(filterData.balconyAreaMax);
    if (filterData.parkingSpacesMin !== undefined) setParkingSpacesMin(filterData.parkingSpacesMin);
    if (filterData.parkingSpacesMax !== undefined) setParkingSpacesMax(filterData.parkingSpacesMax);
    if (filterData.yearBuiltMin !== undefined) setYearBuiltMin(filterData.yearBuiltMin);
    if (filterData.yearBuiltMax !== undefined) setYearBuiltMax(filterData.yearBuiltMax);
    if (filterData.rentPriceMin !== undefined) setRentPriceMin(filterData.rentPriceMin);
    if (filterData.rentPriceMax !== undefined) setRentPriceMax(filterData.rentPriceMax);
    if (filterData.rentEstimateMin !== undefined) setRentEstimateMin(filterData.rentEstimateMin);
    if (filterData.rentEstimateMax !== undefined) setRentEstimateMax(filterData.rentEstimateMax);
    if (filterData.priceGapPctMin !== undefined) setPriceGapPctMin(filterData.priceGapPctMin);
    if (filterData.priceGapPctMax !== undefined) setPriceGapPctMax(filterData.priceGapPctMax);
    if (filterData.capRatePctMin !== undefined) setCapRatePctMin(filterData.capRatePctMin);
    if (filterData.capRatePctMax !== undefined) setCapRatePctMax(filterData.capRatePctMax);
    if (filterData.rooms !== undefined) setRoomsFilter(filterData.rooms || 'all');
    if (filterData.features !== undefined) setFeaturesFilter(filterData.features || 'all');
    if (filterData.renovated !== undefined) setRenovatedFilter(filterData.renovated || 'all');
    if (filterData.furnished !== undefined) setFurnishedFilter(filterData.furnished || 'all');
    if (filterData.airConditioning !== undefined) setAirConditioningFilter(filterData.airConditioning || 'all');
    if (filterData.storageRoom !== undefined) setStorageRoomFilter(filterData.storageRoom || 'all');
    if (filterData.hasElevator !== undefined) setHasElevatorFilter(filterData.hasElevator || 'all');
    if (filterData.block !== undefined) setBlockFilter(filterData.block || 'all');
    if (filterData.parcel !== undefined) setParcelFilter(filterData.parcel || 'all');
    if (filterData.pricePerSqmMin !== undefined) setPricePerSqmMin(filterData.pricePerSqmMin);
    if (filterData.pricePerSqmMax !== undefined) setPricePerSqmMax(filterData.pricePerSqmMax);
    if (filterData.remainingRightsMin !== undefined) setRemainingRightsMin(filterData.remainingRightsMin);
    if (filterData.remainingRightsMax !== undefined) setRemainingRightsMax(filterData.remainingRightsMax);
  }, []);

  // Handle save current filters
  const handleSaveCurrentFilters = React.useCallback(() => {
    const currentFilters = buildCurrentFilters();
    const filterCount = Object.values(currentFilters).filter(v => 
      v !== undefined && v !== null && v !== '' && v !== 'all'
    ).length;
    
    if (filterCount === 0) {
      toast({
        title: 'אין מסננים לשמירה',
        description: 'הגדר לפחות מסנן אחד לפני שמירה',
        variant: 'default',
      });
      return;
    }

    const label = `מסננים מותאמים (${filterCount} מסננים)`;
    saveFilters(currentFilters, label);
    toast({
      title: 'מסננים נשמרו',
      description: 'המסננים נשמרו בהצלחה',
      variant: 'success',
    });
  }, [buildCurrentFilters, saveFilters, toast]);

  // Convert saved filters to presets
  const savedFilterPresets: SavedFilterPreset[] = React.useMemo(() => {
    return savedFilters.map((filter) => ({
      id: filter.id,
      label: filter.label,
      description: filter.description,
      isActive: false, // Could check if current filters match
      isStarred: filter.isStarred,
      onClick: () => {
        applyFilter(filter.id, handleApplyFilter);
        toast({
          title: 'מסננים הוחלו',
          description: `הוחל המסנן "${filter.label}"`,
          variant: 'default',
        });
      },
      onDelete: () => {
        deleteFilter(filter.id);
        toast({
          title: 'מסנן נמחק',
          description: `המסנן "${filter.label}" נמחק`,
          variant: 'default',
        });
      },
    }));
  }, [savedFilters, applyFilter, handleApplyFilter, deleteFilter, toast]);

  const hasActiveFiltersValue = React.useMemo(() => {
    return hasActiveFilters(buildCurrentFilters());
  }, [hasActiveFilters, buildCurrentFilters]);

  // Toolbar actions state
  const [toolbarActionsProps, setToolbarActionsProps] = React.useState<{
    columns?: TableActionColumn[]
    selectedCount?: number
    totalCount?: number
    onExportSelected?: () => void
    onExportAll?: () => void
    disableExportAll?: boolean
    onRefresh?: () => void
    onAddNew?: () => void
    loading?: boolean
    importAction?: { label: string; onClick: () => void; icon?: React.ReactNode }
    bulkActions?: TableAction[]
    onResetColumns?: () => void
  } | null>(null)

  const handleToolbarActionsReady = React.useCallback((props: any) => {
    setToolbarActionsProps(prev => {
      // Only update if props actually changed to prevent infinite loops
      const prevKey = prev ? JSON.stringify({
        columnsCount: prev.columns?.length,
        selectedCount: prev.selectedCount,
        totalCount: prev.totalCount,
        exportingAll: prev.disableExportAll,
        loading: prev.loading,
      }) : ''
      const newKey = JSON.stringify({
        columnsCount: props.columns?.length,
        selectedCount: props.selectedCount,
        totalCount: props.totalCount,
        exportingAll: props.disableExportAll,
        loading: props.loading,
      })
      if (prevKey === newKey && prev) {
        return prev
      }
      return props
    })
  }, [])


  const cityOptions = React.useMemo(() => filterMetadata.cities, [filterMetadata.cities]);
  const typeOptions = React.useMemo(() => filterMetadata.types, [filterMetadata.types]);
  const neighborhoodOptions = React.useMemo(() => filterMetadata.neighborhoods, [filterMetadata.neighborhoods]);
  const zoningOptions = React.useMemo(() => filterMetadata.zonings, [filterMetadata.zonings]);
  const blockOptions = React.useMemo(() => filterMetadata.blocks, [filterMetadata.blocks]);
  const parcelOptions = React.useMemo(() => filterMetadata.parcels, [filterMetadata.parcels]);

  const statusOptions = React.useMemo(() => {
    const getLabel = (value: string) => {
      switch (value) {
        case "done":
          return "מוכן";
        case "failed":
          return "שגיאה";
        case "enriching":
          return "מתעשר";
        case "pending":
          return "ממתין";
        case "active":
          return "פעיל";
        case "archived":
          return "בארכיון";
        case "draft":
          return "טיוטה";
        case "processing":
          return "בעיבוד";
        case "syncing":
          return "מסנכרן נתונים";
        case "synced":
          return "מסונכרן";
        case "none":
          return "ללא סטטוס";
        default:
          return value;
      }
    };

    return Object.entries(filterMetadata.statusCounts).map(([value, count]) => ({
      value,
      label: getLabel(value),
      count,
    }));
  }, [filterMetadata.statusCounts]);

  const riskFilterOptions = React.useMemo(
    () => [...RISK_FILTER_OPTIONS],
    []
  );

  const documentsFilterOptions = React.useMemo(
    () => [...DOCUMENTS_FILTER_OPTIONS],
    []
  );

  const rentalSaleFilterOptions = React.useMemo(
    () => [
      { value: "rent", label: "השכרה" },
      { value: "sale", label: "מכירה" },
    ],
    []
  );

  const sellerTypeFilterOptions = React.useMemo(
    () => [
      { value: "private", label: "פרטי" },
      { value: "broker", label: "מתווך" },
    ],
    []
  );

  const commercialFilterOptions = React.useMemo(
    () => [
      { value: "residential", label: "נכסים למגורים" },
      { value: "commercial", label: "נכסים מסחריים" },
    ],
    []
  );

  const userAssetsFilterOptions = React.useMemo(
    () => [
      { value: "mine", label: "נכסים שלי" },
      { value: "watchlist", label: "ברשימת המעקב שלי" },
      { value: "others", label: "נכסים של אחרים" },
    ],
    []
  );

  const listingSourceOptions = React.useMemo(
    () => {
      const sources = (filterMetadata.sources ?? []).length > 0 ? filterMetadata.sources : ['yad2', 'madlan', 'winwin'];
      return sources.map((value) => ({
        value,
        label: value === 'yad2' ? 'יד2' : value === 'madlan' ? 'מדלן' : value === 'winwin' ? 'WinWin' : value,
      }));
    },
    [filterMetadata.sources]
  );

  const buildingTypeOptions = React.useMemo(() => filterMetadata.buildingTypes, [filterMetadata.buildingTypes]);

  const roomsFilterOptions = React.useMemo(
    () =>
      (filterMetadata.rooms ?? []).map(room => ({
        value: room?.toString() || "0",
        label: `${room} חדרים`
      })),
    [filterMetadata.rooms]
  );

  const featuresFilterOptions = React.useMemo(
    () => [
      { value: "elevator", label: "מעלית" },
      { value: "parking", label: "חניה" },
      { value: "balcony", label: "מרפסת" },
      { value: "storage", label: "מחסן" },
      { value: "air_conditioning", label: "מיזוג אוויר" },
      { value: "furnished", label: "מרוהט" },
      { value: "renovated", label: "משופץ" },
    ],
    []
  );


  return (
    <DashboardLayout>
      <div className="w-full py-6 lg:py-8 px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6">
          {/* Header */}
          <SectionHeader
            title="רשימת נכסים"
            description={loading ? 'טוען נכסים...' : `${totalCount} נכסים עם נתוני שמאות ותכנון מלאים`}
            count={totalCount}
            countLabel="נכסים"
            savedFilterPresets={savedFilterPresets}
            onSaveCurrentFilters={handleSaveCurrentFilters}
            hasActiveFilters={hasActiveFiltersValue}
            toolbarActions={toolbarActionsProps && (
              <TableActionsToolbar
                columns={toolbarActionsProps.columns}
                onResetColumns={toolbarActionsProps.onResetColumns}
                exportAll={toolbarActionsProps.onExportAll}
                exportSelected={toolbarActionsProps.onExportSelected}
                importAction={toolbarActionsProps.importAction}
                bulkActions={toolbarActionsProps.bulkActions}
                selectedCount={toolbarActionsProps.selectedCount}
                totalCount={toolbarActionsProps.totalCount}
                disableExportAll={toolbarActionsProps.disableExportAll}
                onRefresh={toolbarActionsProps.onRefresh}
                onAddNew={toolbarActionsProps.onAddNew}
                loading={toolbarActionsProps.loading}
              />
            )}
          />


        {/* Asset Creation Sheet - Keep the form but remove the trigger button */}
        {isAuthenticated && (
          <Sheet open={open} onOpenChange={setOpen}>
                <SheetContent className="w-full sm:w-96 max-w-[95vw]">
                  <SheetHeader>
                    <SheetTitle>הוסף נכס חדש</SheetTitle>
                    <SheetDescription>
                      הזן פרטי הנכס כדי להתחיל תהליך העשרת מידע
                    </SheetDescription>
                  </SheetHeader>
                  <div className="max-h-[calc(100vh-200px)] overflow-y-auto">
                    <form
                      onSubmit={form.handleSubmit(onSubmit)}
                      className="space-y-4 mt-6"
                    >
                    <div className="space-y-2">
                      <Label htmlFor="locationType">סוג מיקום</Label>
                      <Controller
                        control={form.control}
                        name="locationType"
                        render={({ field }) => (
                          <Select
                            value={field.value}
                            onValueChange={field.onChange}
                          >
                            <SelectTrigger className="min-h-[44px]">
                              <SelectValue placeholder="בחר סוג" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="address">כתובת</SelectItem>
                              <SelectItem value="parcel">גוש/חלקה</SelectItem>
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </div>

                    {form.watch("locationType") === "address" && (
                      <>
                        <div className="space-y-2">
                          <Label htmlFor="city">עיר</Label>
                          <Input
                            id="city"
                            list="city-options"
                            placeholder="בחר עיר"
                            autoComplete="off"
                            className={`min-h-[44px] ${form.formState.errors.city ? "border-error" : ""}`}
                            {...form.register("city", {
                              onChange: (e) =>
                                fetchCitySuggestions(e.target.value),
                            })}
                            aria-invalid={!!form.formState.errors.city}
                            aria-describedby={form.formState.errors.city ? "city-error" : undefined}
                          />
                          <datalist id="city-options">
                            {citySuggestions.map((c) => (
                              <option key={c} value={c} />
                            ))}
                          </datalist>
                          {form.formState.errors.city && (
                            <p id="city-error" className="text-sm text-error">
                              {form.formState.errors.city.message}
                            </p>
                          )}
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="street">רחוב</Label>
                          <Input
                            id="street"
                            list="street-options"
                            placeholder="בחר רחוב"
                            autoComplete="off"
                            className={`min-h-[44px] ${form.formState.errors.street ? "border-error" : ""}`}
                            {...form.register("street", {
                              onChange: (e) =>
                                fetchStreetSuggestions(
                                  e.target.value,
                                  form.getValues("city") || ""
                                ),
                            })}
                            aria-invalid={!!form.formState.errors.street}
                            aria-describedby={form.formState.errors.street ? "street-error" : undefined}
                          />
                          <datalist id="street-options">
                            {streetSuggestions.map((s) => (
                              <option key={s} value={s} />
                            ))}
                          </datalist>
                          {form.formState.errors.street && (
                            <p id="street-error" className="text-sm text-error">
                              {form.formState.errors.street.message}
                            </p>
                          )}
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="houseNumber">מספר בית</Label>
                          <Input
                            id="houseNumber"
                            placeholder="הזן מספר בית"
                            className="min-h-[44px]"
                            {...form.register("houseNumber")}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="apartment">מספר דירה</Label>
                          <Input
                            id="apartment"
                            placeholder="הזן מספר דירה"
                            className="min-h-[44px]"
                            {...form.register("apartment")}
                          />
                        </div>
                      </>
                    )}

                    {form.watch("locationType") === "parcel" && (
                      <>
                        <div className="space-y-2">
                          <Label htmlFor="block">גוש</Label>
                          <Input
                            id="block"
                            placeholder="הזן מספר גוש"
                            className={`min-h-[44px] ${form.formState.errors.block ? "border-error" : ""}`}
                            {...form.register("block")}
                            aria-invalid={!!form.formState.errors.block}
                            aria-describedby={form.formState.errors.block ? "block-error" : undefined}
                          />
                          {form.formState.errors.block && (
                            <p id="block-error" className="text-sm text-error">
                              {form.formState.errors.block.message}
                            </p>
                          )}
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="parcel">חלקה</Label>
                          <Input
                            id="parcel"
                            placeholder="הזן מספר חלקה"
                            className={`min-h-[44px] ${form.formState.errors.parcel ? "border-error" : ""}`}
                            {...form.register("parcel")}
                            aria-invalid={!!form.formState.errors.parcel}
                            aria-describedby={form.formState.errors.parcel ? "parcel-error" : undefined}
                          />
                          {form.formState.errors.parcel && (
                            <p id="parcel-error" className="text-sm text-error">
                              {form.formState.errors.parcel.message}
                            </p>
                          )}
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="subparcel">תת חלקה</Label>
                          <Input
                            id="subparcel"
                            placeholder="הזן מספר תת חלקה"
                            className="min-h-[44px]"
                            {...form.register("subparcel")}
                          />
                        </div>
                      </>
                    )}

                    <Button type="submit" className="w-full min-h-[44px]">
                      הוסף נכס
                    </Button>
                    </form>
                  </div>
                </SheetContent>
              </Sheet>
            )}

          {/* Assets View - Full Width */}
          <div id="main-content" className="w-full z-0">
            {viewMode === 'map' ? (
            loading ? (
              <div className="flex flex-col items-center justify-center py-12 space-y-4">
                <RefreshCw className="h-8 w-8 animate-spin text-brand-teal" />
                <div className="text-center">
                  <p className="text-sm sm:text-base text-muted-foreground">טוען נכסים...</p>
                  <p className="text-xs sm:text-sm text-muted-foreground">אנא המתן בזמן שאנחנו מביאים את הנתונים העדכניים</p>
                </div>
              </div>
            ) : (
              <MapView
                key={`map-${viewMode}-${assets.length}`}
                assets={assets}
                center={[34.98, 31.0]}
                zoom={14}
                onAssetClick={(asset) => router.push(`/assets/${asset.id}`)}
                searchValue={searchInput}
                onSearchChange={setSearchInput}
                height="calc(100vh - 180px)"
                onBackToTable={() => handleViewModeChange('table')}
              />
            )
          ) : (
            <AssetsTable
              onToolbarActionsReady={handleToolbarActionsReady}
              data={assets}
              loading={loading}
              onDelete={isAdmin ? handleDeleteAsset : undefined}
              onToggleWatch={handleToggleWatch}
              watchingAssetIds={watchingAssetIds}
              onExportAllRequest={handleExportAllAssets}
              searchValue={searchInput}
              onSearchChange={setSearchInput}
              manualPagination
              paginationState={pagination}
              onPaginationChange={(next) => setPagination(next)}
              pageCount={pageCount}
              totalCount={totalCount}
              pageSizeOptions={PAGE_SIZE_OPTIONS}
              manualSorting
              sortingState={sorting}
              onSortingChange={(next) => setSorting(next)}
              filters={{
                city: {
                  value: city,
                  onChange: setCity,
                  options: cityOptions
                },
                type: {
                  value: typeFilter,
                  onChange: setTypeFilter,
                  options: typeOptions
                },
                priceMin: {
                  value: priceMin,
                  onChange: setPriceMin
                },
                priceMax: {
                  value: priceMax,
                  onChange: setPriceMax
                },
                neighborhood: {
                  value: neighborhood,
                  onChange: setNeighborhood,
                  options: neighborhoodOptions
                },
                zoning: {
                  value: zoning,
                  onChange: setZoning,
                  options: zoningOptions
                },
                risk: {
                  value: riskFilter,
                  onChange: setRiskFilter,
                  options: riskFilterOptions
                },
                documents: {
                  value: documentsFilter,
                  onChange: setDocumentsFilter,
                  options: documentsFilterOptions
                },
                status: {
                  value: statusFilter,
                  onChange: setStatusFilter,
                  options: statusOptions
                },
                source: {
                  value: sourceFilter,
                  onChange: setSourceFilter,
                  options: listingSourceOptions
                },
                pricePerSqmMin: {
                  value: pricePerSqmMin,
                  onChange: setPricePerSqmMin
                },
                pricePerSqmMax: {
                  value: pricePerSqmMax,
                  onChange: setPricePerSqmMax
                },
                remainingRightsMin: {
                  value: remainingRightsMin,
                  onChange: setRemainingRightsMin
                },
                remainingRightsMax: {
                  value: remainingRightsMax,
                  onChange: setRemainingRightsMax
                },
                block: {
                  value: blockFilter,
                  onChange: setBlockFilter,
                  options: blockOptions
                },
                parcel: {
                  value: parcelFilter,
                  onChange: setParcelFilter,
                  options: parcelOptions
                },
                rentalSale: {
                  value: rentalSaleFilter,
                  onChange: setRentalSaleFilter,
                  options: rentalSaleFilterOptions
                },
                sellerType: {
                  value: sellerTypeFilter,
                  onChange: setSellerTypeFilter,
                  options: sellerTypeFilterOptions
                },
                commercial: {
                  value: commercialFilter,
                  onChange: setCommercialFilter,
                  options: commercialFilterOptions
                },
                userAssets: {
                  value: userAssetsFilter,
                  onChange: setUserAssetsFilter,
                  options: userAssetsFilterOptions
                },
                buildingType: {
                  value: buildingTypeFilter,
                  onChange: setBuildingTypeFilter,
                  options: buildingTypeOptions
                },
                floorMin: {
                  value: floorMin,
                  onChange: setFloorMin
                },
                floorMax: {
                  value: floorMax,
                  onChange: setFloorMax
                },
                areaMin: {
                  value: areaMin,
                  onChange: setAreaMin
                },
                areaMax: {
                  value: areaMax,
                  onChange: setAreaMax
                },
                bedrooms: {
                  value: { min: bedroomsMin, max: bedroomsMax },
                  onChange: ({ min, max }: { min: number | undefined, max: number | undefined }) => {
                    setBedroomsMin(min);
                    setBedroomsMax(max);
                  },
                  minPlaceholder: filterMetadata.bedroomRange.min != null ? `${filterMetadata.bedroomRange.min}` : 'מינ חדרי שינה',
                  maxPlaceholder: filterMetadata.bedroomRange.max != null ? `${filterMetadata.bedroomRange.max}` : 'מקס חדרי שינה',
                },
                bathrooms: {
                  value: { min: bathroomsMin, max: bathroomsMax },
                  onChange: ({ min, max }: { min: number | undefined, max: number | undefined }) => {
                    setBathroomsMin(min);
                    setBathroomsMax(max);
                  },
                  minPlaceholder: filterMetadata.bathroomRange.min != null ? `${filterMetadata.bathroomRange.min}` : 'מינ חדרי רחצה',
                  maxPlaceholder: filterMetadata.bathroomRange.max != null ? `${filterMetadata.bathroomRange.max}` : 'מקס חדרי רחצה',
                },
                totalFloors: {
                  value: { min: totalFloorsMin, max: totalFloorsMax },
                  onChange: ({ min, max }: { min: number | undefined, max: number | undefined }) => {
                    setTotalFloorsMin(min);
                    setTotalFloorsMax(max);
                  },
                  minPlaceholder: filterMetadata.totalFloorRange.min != null ? `${filterMetadata.totalFloorRange.min}` : 'מינ קומות בבניין',
                  maxPlaceholder: filterMetadata.totalFloorRange.max != null ? `${filterMetadata.totalFloorRange.max}` : 'מקס קומות בבניין',
                },
                totalArea: {
                  value: { min: totalAreaMin, max: totalAreaMax },
                  onChange: ({ min, max }: { min: number | undefined, max: number | undefined }) => {
                    setTotalAreaMin(min);
                    setTotalAreaMax(max);
                  },
                  minPlaceholder: filterMetadata.totalAreaRange.min != null ? `${filterMetadata.totalAreaRange.min}` : 'מינ שטח כולל',
                  maxPlaceholder: filterMetadata.totalAreaRange.max != null ? `${filterMetadata.totalAreaRange.max}` : 'מקס שטח כולל',
                },
                balconyArea: {
                  value: { min: balconyAreaMin, max: balconyAreaMax },
                  onChange: ({ min, max }: { min: number | undefined, max: number | undefined }) => {
                    setBalconyAreaMin(min);
                    setBalconyAreaMax(max);
                  },
                  minPlaceholder: filterMetadata.balconyAreaRange.min != null ? `${filterMetadata.balconyAreaRange.min}` : 'מינ שטח מרפסת',
                  maxPlaceholder: filterMetadata.balconyAreaRange.max != null ? `${filterMetadata.balconyAreaRange.max}` : 'מקס שטח מרפסת',
                },
                parkingSpaces: {
                  value: { min: parkingSpacesMin, max: parkingSpacesMax },
                  onChange: ({ min, max }: { min: number | undefined, max: number | undefined }) => {
                    setParkingSpacesMin(min);
                    setParkingSpacesMax(max);
                  },
                  minPlaceholder: filterMetadata.parkingSpaceRange.min != null ? `${filterMetadata.parkingSpaceRange.min}` : 'מינ חניות',
                  maxPlaceholder: filterMetadata.parkingSpaceRange.max != null ? `${filterMetadata.parkingSpaceRange.max}` : 'מקס חניות',
                },
                yearBuilt: {
                  value: { min: yearBuiltMin, max: yearBuiltMax },
                  onChange: ({ min, max }: { min: number | undefined, max: number | undefined }) => {
                    setYearBuiltMin(min);
                    setYearBuiltMax(max);
                  },
                  minPlaceholder: filterMetadata.yearBuiltRange.min != null ? `${filterMetadata.yearBuiltRange.min}` : 'משנת',
                  maxPlaceholder: filterMetadata.yearBuiltRange.max != null ? `${filterMetadata.yearBuiltRange.max}` : 'עד שנת',
                  step: 1,
                },
                rentPrice: {
                  value: { min: rentPriceMin, max: rentPriceMax },
                  onChange: ({ min, max }: { min: number | undefined, max: number | undefined }) => {
                    setRentPriceMin(min);
                    setRentPriceMax(max);
                  },
                  minPlaceholder: filterMetadata.rentPriceRange.min != null ? `${filterMetadata.rentPriceRange.min}` : 'שכ"ד מינ',
                  maxPlaceholder: filterMetadata.rentPriceRange.max != null ? `${filterMetadata.rentPriceRange.max}` : 'שכ"ד מקס',
                },
                rentEstimate: {
                  value: { min: rentEstimateMin, max: rentEstimateMax },
                  onChange: ({ min, max }: { min: number | undefined, max: number | undefined }) => {
                    setRentEstimateMin(min);
                    setRentEstimateMax(max);
                  },
                  minPlaceholder: filterMetadata.rentEstimateRange.min != null ? `${filterMetadata.rentEstimateRange.min}` : 'שכירות מינ',
                  maxPlaceholder: filterMetadata.rentEstimateRange.max != null ? `${filterMetadata.rentEstimateRange.max}` : 'שכירות מקס',
                },
                priceGapPct: {
                  value: { min: priceGapPctMin, max: priceGapPctMax },
                  onChange: ({ min, max }: { min: number | undefined, max: number | undefined }) => {
                    setPriceGapPctMin(min);
                    setPriceGapPctMax(max);
                  },
                  minPlaceholder: filterMetadata.priceGapPctRange.min != null ? `${filterMetadata.priceGapPctRange.min}` : 'פער מינ %',
                  maxPlaceholder: filterMetadata.priceGapPctRange.max != null ? `${filterMetadata.priceGapPctRange.max}` : 'פער מקס %',
                  step: 0.5,
                },
                capRatePct: {
                  value: { min: capRatePctMin, max: capRatePctMax },
                  onChange: ({ min, max }: { min: number | undefined, max: number | undefined }) => {
                    setCapRatePctMin(min);
                    setCapRatePctMax(max);
                  },
                  minPlaceholder: filterMetadata.capRatePctRange.min != null ? `${filterMetadata.capRatePctRange.min}` : 'תשואה מינ %',
                  maxPlaceholder: filterMetadata.capRatePctRange.max != null ? `${filterMetadata.capRatePctRange.max}` : 'תשואה מקס %',
                  step: 0.1,
                },
                rooms: {
                  value: roomsFilter,
                  onChange: setRoomsFilter,
                  options: roomsFilterOptions
                },
                features: {
                  value: featuresFilter,
                  onChange: setFeaturesFilter,
                  options: featuresFilterOptions
                },
                renovated: {
                  value: renovatedFilter,
                  onChange: setRenovatedFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'משופץ' },
                    { value: 'false', label: 'לא משופץ' },
                  ]
                },
                furnished: {
                  value: furnishedFilter,
                  onChange: setFurnishedFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'מרוהט' },
                    { value: 'false', label: 'לא מרוהט' },
                  ]
                },
                airConditioning: {
                  value: airConditioningFilter,
                  onChange: setAirConditioningFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'עם מיזוג' },
                    { value: 'false', label: 'ללא מיזוג' },
                  ]
                },
                storageRoom: {
                  value: storageRoomFilter,
                  onChange: setStorageRoomFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'עם מחסן' },
                    { value: 'false', label: 'ללא מחסן' },
                  ]
                },
                hasElevator: {
                  value: hasElevatorFilter,
                  onChange: setHasElevatorFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'עם מעלית' },
                    { value: 'false', label: 'ללא מעלית' },
                  ]
                },
                recentDeal: {
                  value: recentDealFilter,
                  onChange: setRecentDealFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'כן' },
                    { value: 'false', label: 'לא' },
                  ]
                },
                modelPrice: {
                  value: { min: modelPriceMin, max: modelPriceMax },
                  onChange: ({ min, max }: { min: number | undefined, max: number | undefined }) => {
                    setModelPriceMin(min);
                    setModelPriceMax(max);
                  },
                  minPlaceholder: 'מחיר שוק מינ',
                  maxPlaceholder: 'מחיר שוק מקס',
                },
                antennaDistanceM: {
                  value: { min: antennaDistanceMin, max: antennaDistanceMax },
                  onChange: ({ min, max }: { min: number | undefined, max: number | undefined }) => {
                    setAntennaDistanceMin(min);
                    setAntennaDistanceMax(max);
                  },
                  minPlaceholder: 'מרחק מינ (מ")',
                  maxPlaceholder: 'מרחק מקס (מ")',
                },
                shelterDistanceM: {
                  value: { min: shelterDistanceMin, max: shelterDistanceMax },
                  onChange: ({ min, max }: { min: number | undefined, max: number | undefined }) => {
                    setShelterDistanceMin(min);
                    setShelterDistanceMax(max);
                  },
                  minPlaceholder: 'מרחק מינ (מ")',
                  maxPlaceholder: 'מרחק מקס (מ")',
                },
                noiseLevel: {
                  value: { min: noiseLevelMin, max: noiseLevelMax },
                  onChange: ({ min, max }: { min: number | undefined, max: number | undefined }) => {
                    setNoiseLevelMin(min);
                    setNoiseLevelMax(max);
                  },
                  minPlaceholder: 'רמת רעש מינ (0-5)',
                  maxPlaceholder: 'רמת רעש מקס (0-5)',
                  step: 0.5,
                },
                greenWithin300m: {
                  value: greenWithin300mFilter,
                  onChange: setGreenWithin300mFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'כן' },
                    { value: 'false', label: 'לא' },
                  ]
                },
                schoolsWithin500m: {
                  value: schoolsWithin500mFilter,
                  onChange: setSchoolsWithin500mFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'כן' },
                    { value: 'false', label: 'לא' },
                  ]
                },
                // High Priority Filters
                priceDropped: {
                  value: priceDroppedFilter,
                  onChange: setPriceDroppedFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'יש הורדת מחיר' },
                    { value: 'false', label: 'ללא הורדת מחיר' },
                  ]
                },
                shelter: {
                  value: shelterFilter,
                  onChange: setShelterFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'עם מקלט' },
                    { value: 'false', label: 'ללא מקלט' },
                  ]
                },
                accessibility: {
                  value: accessibilityFilter,
                  onChange: setAccessibilityFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'נגיש' },
                    { value: 'false', label: 'לא נגיש' },
                  ]
                },
                buildingClass: {
                  value: buildingClassFilter,
                  onChange: setBuildingClassFilter,
                  options: [] // Will be populated from filterMetadata
                },
                generalCondition: {
                  value: generalConditionFilter,
                  onChange: setGeneralConditionFilter,
                  options: [] // Will be populated from filterMetadata
                },
                investmentYield: {
                  value: { min: investmentYieldMin, max: investmentYieldMax },
                  onChange: ({ min, max }: { min?: number; max?: number }) => {
                    setInvestmentYieldMin(min);
                    setInvestmentYieldMax(max);
                  },
                  minPlaceholder: 'תשואה מינ %',
                  maxPlaceholder: 'תשואה מקס %',
                  step: 0.1,
                },
                approximateRent: {
                  value: { min: approximateRentMin, max: approximateRentMax },
                  onChange: ({ min, max }: { min?: number; max?: number }) => {
                    setApproximateRentMin(min);
                    setApproximateRentMax(max);
                  },
                  minPlaceholder: 'שכירות משוערת מינ',
                  maxPlaceholder: 'שכירות משוערת מקס',
                },
                commuteTime: {
                  value: { min: commuteTimeMin, max: commuteTimeMax },
                  onChange: ({ min, max }: { min?: number; max?: number }) => {
                    setCommuteTimeMin(min);
                    setCommuteTimeMax(max);
                  },
                  minPlaceholder: 'זמן נסיעה מינ (דקות)',
                  maxPlaceholder: 'זמן נסיעה מקס (דקות)',
                  step: 1,
                },
                publishedDays: {
                  value: { min: undefined, max: publishedDaysMax },
                  onChange: ({ min, max }: { min?: number; max?: number }) => {
                    setPublishedDaysMax(max);
                  },
                  minPlaceholder: '',
                  maxPlaceholder: 'פורסם ב-X ימים האחרונים',
                  step: 1,
                },
                tagBestSchool: {
                  value: tagBestSchoolFilter,
                  onChange: setTagBestSchoolFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'ליד בתי ספר מצוינים' },
                    { value: 'false', label: 'לא' },
                  ]
                },
                tagSafety: {
                  value: tagSafetyFilter,
                  onChange: setTagSafetyFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'בטוח' },
                    { value: 'false', label: 'לא' },
                  ]
                },
                tagFamilyFriendly: {
                  value: tagFamilyFriendlyFilter,
                  onChange: setTagFamilyFriendlyFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'ידידותי למשפחה' },
                    { value: 'false', label: 'לא' },
                  ]
                },
                tagLightRail: {
                  value: tagLightRailFilter,
                  onChange: setTagLightRailFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'ליד רכבת קלה' },
                    { value: 'false', label: 'לא' },
                  ]
                },
                exclusive: {
                  value: exclusiveFilter,
                  onChange: setExclusiveFilter,
                  options: [
                    { value: 'all', label: 'הכל' },
                    { value: 'true', label: 'בלעדי' },
                    { value: 'false', label: 'לא' },
                  ]
                },
              } as any}
              onRefresh={fetchAssets}
              onAddNew={() => {
                if (isAuthenticated) {
                  setOpen(true);
                } else {
                  handleProtectedAction("add-asset");
                }
              }}
              importAction={{
                label: 'ייבוא מנדל"ן וואן',
                onClick: () => setNadlanImportOpen(true),
                icon: <DownloadCloud className="h-4 w-4" />
              }}
              viewMode={viewMode}
              onViewModeChange={handleViewModeChange}
              bulkActions={[
                {
                  label: "הוסף למעקב",
                  action: handleBulkWatch,
                  icon: <Star className="h-4 w-4" fill="currentColor" />,
                },
                {
                  label: "הסר ממעקב",
                  action: handleBulkUnwatch,
                  icon: <StarOff className="h-4 w-4" />,
                },
                {
                  label: "סנכרן נתונים",
                  action: handleBulkSync,
                  icon: <RefreshCw className="h-4 w-4" />,
                },
                {
                  label: "צור דוחות",
                  action: handleBulkCreateReports,
                  icon: <FileText className="h-4 w-4" />,
                },
                ...(isAdmin
                  ? [
                      {
                        label: "מחק נבחרים",
                        action: handleBulkDelete,
                        icon: <Trash2 className="h-4 w-4 text-red-600" />,
                      },
                    ]
                  : []),
              ]}
            />
          )}
          </div>

          {/* Summary */}
          <div className="flex items-center justify-between mt-6">
            <p className="text-sm text-muted-foreground">
              מציג {assets.length} מתוך {totalCount} נכסים
            </p>
          </div>

          {/* Plan Limit Dialog */}
          {planLimitError && (
            <PlanLimitDialog
              open={showPlanLimitDialog}
              onOpenChange={setShowPlanLimitDialog}
              error={planLimitError}
            />
          )}

          <ImportDialogNadlanOne
              open={nadlanImportOpen}
              onOpenChange={setNadlanImportOpen}
              mode="properties"
          />
        </div>
      </div>
    </DashboardLayout>
  );
}
