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
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import OnboardingProgress from "@/components/OnboardingProgress";
import { selectOnboardingState, isOnboardingComplete } from "@/onboarding/selectors";
import type { Asset } from "@/lib/normalizers/asset";
import AssetsTable from "@/components/AssetsTable";
import ImportDialogNadlanOne from "@/components/import/ImportDialogNadlanOne";

import MapView from "@/components/MapView";
import DashboardLayout from "@/components/layout/dashboard-layout";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useToast } from "@/hooks/use-toast";
import { useConfirm } from "@/hooks/use-confirm";
import PlanLimitDialog from "@/components/PlanLimitDialog";
import { apiClient } from "@/lib/api-client";
import { useDedupedEffect } from "@/hooks/use-deduped-effect";
import type { PaginationState } from "@tanstack/react-table";

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
  rentEstimateRange: { min: number | null; max: number | null };
  priceGapPctRange: { min: number | null; max: number | null };
  capRatePctRange: { min: number | null; max: number | null };
  bedroomRange: { min: number | null; max: number | null };
  bathroomRange: { min: number | null; max: number | null };
  totalFloorRange: { min: number | null; max: number | null };
  parkingSpaceRange: { min: number | null; max: number | null };
  balconyAreaRange: { min: number | null; max: number | null };
};

type ViewMode = 'table' | 'cards' | 'map' | 'split';

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [nadlanImportOpen, setNadlanImportOpen] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: DEFAULT_PAGE_SIZE });
  const [totalCount, setTotalCount] = useState(0);
  const [filterMetadata, setFilterMetadata] = useState<AssetFilterMetadata>({
    cities: [],
    types: [],
    neighborhoods: [],
    zonings: [],
    blocks: [],
    parcels: [],
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
  const [search, setSearch] = useState(() => searchParams.get("search") ?? "");
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
  const [rentalSaleFilter, setRentalSaleFilter] = useState<string>(() => searchParams.get("rentalSale") ?? "all");
  const [adTypeFilter, setAdTypeFilter] = useState<string>(() => searchParams.get("adType") ?? "all");
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
  const [viewMode, setViewMode] = useState<ViewMode>('table');
  const userSelectedViewMode = React.useRef(false);
  const handleViewModeChange = React.useCallback((mode: ViewMode) => {
    userSelectedViewMode.current = mode !== 'split';
    setViewMode(mode);
  }, []);
  const { user, isAuthenticated, refreshUser } = useAuth();
  const isAdmin = user?.role === 'admin';
  const onboardingState = React.useMemo(() => selectOnboardingState(user), [user]);
  const router = useRouter();
  const pathname = usePathname();
  const { toast } = useToast();
  const { confirm } = useConfirm();

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return;
    }

    const mediaQuery = window.matchMedia('(min-width: 1280px)');

    const applyResponsiveView = (matches: boolean) => {
      setViewMode(prev => {
        if (matches) {
          if (prev === 'split' || userSelectedViewMode.current) {
            return prev;
          }
          return 'split';
        }

        if (prev === 'split') {
          return 'table';
        }

        return prev;
      });
    };

    applyResponsiveView(mediaQuery.matches);

    const handleChange = (event: MediaQueryListEvent) => {
      applyResponsiveView(event.matches);
    };

    mediaQuery.addEventListener('change', handleChange);

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

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


  useEffect(() => {
    setSearch(searchParams.get("search") ?? "");
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
    setRentalSaleFilter(searchParams.get("rentalSale") ?? "all");
    setAdTypeFilter(searchParams.get("adType") ?? "all");
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
    const params = new URLSearchParams(searchParams.toString());
    if (search) {
      params.set("search", search);
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
    if (rentalSaleFilter && rentalSaleFilter !== "all") {
      params.set("rentalSale", rentalSaleFilter);
    } else {
      params.delete("rentalSale");
    }
    if (adTypeFilter && adTypeFilter !== "all") {
      params.set("adType", adTypeFilter);
    } else {
      params.delete("adType");
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
    search,
    city,
    typeFilter,
    priceMin,
    priceMax,
    neighborhood,
    zoning,
    riskFilter,
    documentsFilter,
    statusFilter,
    rentalSaleFilter,
    adTypeFilter,
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
    pagination.pageIndex,
    pagination.pageSize,
    router,
    pathname,
    searchParams,
  ]);

  React.useEffect(() => {
    setPagination(prev => (prev.pageIndex === 0 ? prev : { ...prev, pageIndex: 0 }));
  }, [
    search,
    city,
    typeFilter,
    priceMin,
    priceMax,
    neighborhood,
    zoning,
    riskFilter,
    documentsFilter,
    statusFilter,
    rentalSaleFilter,
    adTypeFilter,
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
  ]);

  // Function to fetch assets
  const fetchAssets = React.useCallback(async () => {
    try {
      setLoading(true);

      const params = new URLSearchParams();
      const isDefaultPageIndex = pagination.pageIndex === 0;
      const isDefaultPageSize = pagination.pageSize === DEFAULT_PAGE_SIZE;

      if (!isDefaultPageIndex) {
        params.set("page", String(pagination.pageIndex + 1));
      }

      if (!isDefaultPageSize) {
        params.set("pageSize", String(pagination.pageSize));
      }

      if (search) params.set("search", search);
      if (city && city !== "all") params.set("city", city);
      if (typeFilter && typeFilter !== "all") params.set("type", typeFilter);
      if (priceMin != null) params.set("priceMin", String(priceMin));
      if (priceMax != null) params.set("priceMax", String(priceMax));
      if (neighborhood && neighborhood !== "all") params.set("neighborhood", neighborhood);
      if (zoning && zoning !== "all") params.set("zoning", zoning);
      if (riskFilter && riskFilter !== "all") params.set("risk", riskFilter);
      if (documentsFilter && documentsFilter !== "all") params.set("documents", documentsFilter);
      if (statusFilter && statusFilter !== "all") params.set("status", statusFilter);
      if (rentalSaleFilter && rentalSaleFilter !== "all") params.set("rentalSale", rentalSaleFilter);
      if (adTypeFilter && adTypeFilter !== "all") params.set("adType", adTypeFilter);
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

        if (response.data?.filters) {
          const filters = response.data.filters as Partial<AssetFilterMetadata>;
          setFilterMetadata({
            cities: filters.cities ?? [],
            types: filters.types ?? [],
            neighborhoods: filters.neighborhoods ?? [],
            zonings: filters.zonings ?? [],
            blocks: filters.blocks ?? [],
            parcels: filters.parcels ?? [],
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
    search,
    city,
    typeFilter,
    priceMin,
    priceMax,
    neighborhood,
    zoning,
    riskFilter,
    documentsFilter,
    statusFilter,
    rentalSaleFilter,
    adTypeFilter,
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
  ]);

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
          description: `שגיאה במחיקת הנכס: ${response.error}`,
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error deleting asset:", error);
      toast({
        title: "שגיאה",
        description: "שגיאה במחיקת הנכס",
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
          description: response.error || "הפעולה נכשלה",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error performing bulk delete:", error);
      toast({
        title: "שגיאה במחיקה מרובה",
        description: error instanceof Error ? error.message : "הפעולה נכשלה",
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
          description: response.error || "הפעולה נכשלה",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error performing bulk sync:", error);
      toast({
        title: "שגיאה בסנכרון",
        description: error instanceof Error ? error.message : "הפעולה נכשלה",
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
          description: response.error || "הפעולה נכשלה",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error creating bulk reports:", error);
      toast({
        title: "שגיאה ביצירת דוחות",
        description: error instanceof Error ? error.message : "הפעולה נכשלה",
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
              radius: data.radius,
            }
          : {
              scope: {
                type: "parcel",
                value: `${data.block}/${data.parcel}`,
              },
              block: data.block,
              parcel: data.parcel,
              subparcel: data.subparcel,
              radius: data.radius,
            };

      const response = await apiClient.request("/api/assets", {
        method: "POST",
        body: JSON.stringify(body),
      });

      if (response.ok) {
        form.reset();
        setOpen(false);
        // Refresh assets to show the new asset
        await fetchAssets();
        // Refresh user data to update onboarding progress
        await refreshUser();
        toast({
          title: "הצלחה",
          description: "הנכס נוסף בהצלחה",
          variant: "success",
        });
      } else {
        console.error("Failed to create asset:", response.error);
        
        // Handle plan limit errors
        if (response.status === 403 && response.data?.error === 'asset_limit_exceeded') {
          setPlanLimitError(response.data);
          setShowPlanLimitDialog(true);
        } else {
          toast({
            title: "שגיאה",
            description: `שגיאה ביצירת הנכס: ${response.error || 'שגיאה לא ידועה'}`,
            variant: "destructive",
          });
        }
      }
    } catch (error) {
      console.error("Error creating asset:", error);
      toast({
        title: "שגיאה",
        description: "שגיאה ביצירת הנכס",
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

  const adTypeFilterOptions = React.useMemo(
    () => [
      { value: "private", label: "פרטי" },
      { value: "broker", label: "מתווך" },
    ],
    []
  );

  const commercialFilterOptions = React.useMemo(
    () => [
      { value: "commercial", label: "נכסים מסחריים" },
      { value: "residential", label: "נכסים למגורים" },
    ],
    []
  );

  const userAssetsFilterOptions = React.useMemo(
    () => [
      { value: "mine", label: "נכסים שלי" },
      { value: "others", label: "נכסים של אחרים" },
    ],
    []
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

  const renderAssetsTable = () => (
    <AssetsTable
      data={assets}
      loading={loading}
      onDelete={isAdmin ? handleDeleteAsset : undefined}
      searchValue={search}
      onSearchChange={setSearch}
      manualPagination
      paginationState={pagination}
      onPaginationChange={(next) => setPagination(next)}
      pageCount={pageCount}
      totalCount={totalCount}
      pageSizeOptions={PAGE_SIZE_OPTIONS}
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
        adType: {
          value: adTypeFilter,
          onChange: setAdTypeFilter,
          options: adTypeFilterOptions
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
          onChange: ({ min, max }) => {
            setBedroomsMin(min);
            setBedroomsMax(max);
          },
          minPlaceholder: filterMetadata.bedroomRange.min != null ? `${filterMetadata.bedroomRange.min}` : 'מינ חדרי שינה',
          maxPlaceholder: filterMetadata.bedroomRange.max != null ? `${filterMetadata.bedroomRange.max}` : 'מקס חדרי שינה',
        },
        bathrooms: {
          value: { min: bathroomsMin, max: bathroomsMax },
          onChange: ({ min, max }) => {
            setBathroomsMin(min);
            setBathroomsMax(max);
          },
          minPlaceholder: filterMetadata.bathroomRange.min != null ? `${filterMetadata.bathroomRange.min}` : 'מינ חדרי רחצה',
          maxPlaceholder: filterMetadata.bathroomRange.max != null ? `${filterMetadata.bathroomRange.max}` : 'מקס חדרי רחצה',
        },
        totalFloors: {
          value: { min: totalFloorsMin, max: totalFloorsMax },
          onChange: ({ min, max }) => {
            setTotalFloorsMin(min);
            setTotalFloorsMax(max);
          },
          minPlaceholder: filterMetadata.totalFloorRange.min != null ? `${filterMetadata.totalFloorRange.min}` : 'מינ קומות בבניין',
          maxPlaceholder: filterMetadata.totalFloorRange.max != null ? `${filterMetadata.totalFloorRange.max}` : 'מקס קומות בבניין',
        },
        totalArea: {
          value: { min: totalAreaMin, max: totalAreaMax },
          onChange: ({ min, max }) => {
            setTotalAreaMin(min);
            setTotalAreaMax(max);
          },
          minPlaceholder: filterMetadata.totalAreaRange.min != null ? `${filterMetadata.totalAreaRange.min}` : 'מינ שטח כולל',
          maxPlaceholder: filterMetadata.totalAreaRange.max != null ? `${filterMetadata.totalAreaRange.max}` : 'מקס שטח כולל',
        },
        balconyArea: {
          value: { min: balconyAreaMin, max: balconyAreaMax },
          onChange: ({ min, max }) => {
            setBalconyAreaMin(min);
            setBalconyAreaMax(max);
          },
          minPlaceholder: filterMetadata.balconyAreaRange.min != null ? `${filterMetadata.balconyAreaRange.min}` : 'מינ שטח מרפסת',
          maxPlaceholder: filterMetadata.balconyAreaRange.max != null ? `${filterMetadata.balconyAreaRange.max}` : 'מקס שטח מרפסת',
        },
        parkingSpaces: {
          value: { min: parkingSpacesMin, max: parkingSpacesMax },
          onChange: ({ min, max }) => {
            setParkingSpacesMin(min);
            setParkingSpacesMax(max);
          },
          minPlaceholder: filterMetadata.parkingSpaceRange.min != null ? `${filterMetadata.parkingSpaceRange.min}` : 'מינ חניות',
          maxPlaceholder: filterMetadata.parkingSpaceRange.max != null ? `${filterMetadata.parkingSpaceRange.max}` : 'מקס חניות',
        },
        yearBuilt: {
          value: { min: yearBuiltMin, max: yearBuiltMax },
          onChange: ({ min, max }) => {
            setYearBuiltMin(min);
            setYearBuiltMax(max);
          },
          minPlaceholder: filterMetadata.yearBuiltRange.min != null ? `${filterMetadata.yearBuiltRange.min}` : 'משנת',
          maxPlaceholder: filterMetadata.yearBuiltRange.max != null ? `${filterMetadata.yearBuiltRange.max}` : 'עד שנת',
          step: 1,
        },
        rentEstimate: {
          value: { min: rentEstimateMin, max: rentEstimateMax },
          onChange: ({ min, max }) => {
            setRentEstimateMin(min);
            setRentEstimateMax(max);
          },
          minPlaceholder: filterMetadata.rentEstimateRange.min != null ? `${filterMetadata.rentEstimateRange.min}` : 'שכירות מינ',
          maxPlaceholder: filterMetadata.rentEstimateRange.max != null ? `${filterMetadata.rentEstimateRange.max}` : 'שכירות מקס',
        },
        priceGapPct: {
          value: { min: priceGapPctMin, max: priceGapPctMax },
          onChange: ({ min, max }) => {
            setPriceGapPctMin(min);
            setPriceGapPctMax(max);
          },
          minPlaceholder: filterMetadata.priceGapPctRange.min != null ? `${filterMetadata.priceGapPctRange.min}` : 'פער מינ %',
          maxPlaceholder: filterMetadata.priceGapPctRange.max != null ? `${filterMetadata.priceGapPctRange.max}` : 'פער מקס %',
          step: 0.5,
        },
        capRatePct: {
          value: { min: capRatePctMin, max: capRatePctMax },
          onChange: ({ min, max }) => {
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
      }}
      onRefresh={fetchAssets}
      onAddNew={() => {
        if (isAuthenticated) {
          setOpen(true);
        } else {
          handleProtectedAction("add-asset");
        }
      }}
      extraActions={
        <Button
          onClick={() => setNadlanImportOpen(true)}
          size="sm"
          variant="outline"
          className="min-h-[44px] rounded-full px-4 flex items-center gap-2 flex-shrink-0"
        >
          <DownloadCloud className="h-4 w-4" />
          ייבוא מנדל&quot;ן וואן
        </Button>
      }
      viewMode={viewMode}
      onViewModeChange={handleViewModeChange}
      bulkActions={[
        ...(isAdmin
          ? [
              {
                label: "מחק נבחרים",
                action: handleBulkDelete,
                icon: <Trash2 className="h-4 w-4" />,
              },
            ]
          : []),
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
        {
          label: "ייצא נבחרים",
          action: handleBulkExport,
          icon: <Download className="h-4 w-4" />,
        }
      ]}
    />
  );


  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        {isAuthenticated && user?.onboarding_flags && !isOnboardingComplete(onboardingState) && (
          <OnboardingProgress state={onboardingState} />
        )}
        {/* Header */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-foreground">רשימת נכסים</h1>
            <p className="text-sm sm:text-base text-muted-foreground">
              {loading ? 'טוען נכסים...' : `${totalCount} נכסים עם נתוני שמאות ותכנון מלאים`}
            </p>
          </div>
        </div>


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

                    <div className="space-y-2">
                      <Label htmlFor="radius">רדיוס (מטרים)</Label>
                      <Input
                        id="radius"
                        type="number"
                        className="min-h-[44px]"
                        {...form.register("radius", { valueAsNumber: true })}
                      />
                    </div>

                    <Button type="submit" className="w-full min-h-[44px]">
                      הוסף נכס
                    </Button>
                    </form>
                  </div>
                </SheetContent>
              </Sheet>
            )}


        {/* Assets View */}
        <div id="main-content">
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
                searchValue={search}
                onSearchChange={setSearch}
                height="600px"
                onBackToTable={() => handleViewModeChange('table')}
              />
            )
          ) : viewMode === 'split' ? (
            <div className="flex flex-col gap-4 lg:grid lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] lg:items-start">
              <div className="order-2 lg:order-1">{renderAssetsTable()}</div>
              <div className="order-1 lg:order-2">
                <div className="h-[360px] lg:h-[min(70vh,720px)] rounded-xl border border-border bg-card overflow-hidden">
                  {loading ? (
                    <div className="flex h-full flex-col items-center justify-center space-y-4 bg-muted/40">
                      <RefreshCw className="h-8 w-8 animate-spin text-brand-teal" />
                      <div className="text-center text-sm text-muted-foreground">
                        טוען נכסים למפה...
                      </div>
                    </div>
                  ) : (
                    <MapView
                      key={`map-${viewMode}-${assets.length}`}
                      assets={assets}
                      center={[34.98, 31.0]}
                      zoom={14}
                      onAssetClick={(asset) => router.push(`/assets/${asset.id}`)}
                      searchValue={search}
                      onSearchChange={setSearch}
                      height="100%"
                      className="h-full"
                    />
                  )}
                </div>
              </div>
            </div>
          ) : (
            renderAssetsTable()
          )}
        </div>
        {/* Summary */}
        <div className="flex items-center justify-between">
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
    </DashboardLayout>
  );
}
