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
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Plus,
  RefreshCw,
  Search,
  Trash2,
  Download,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import OnboardingProgress from "@/components/OnboardingProgress";
import { selectOnboardingState, getCompletionPct } from "@/onboarding/selectors";
import type { Asset } from "@/lib/normalizers/asset";
import AssetsTable from "@/components/AssetsTable";
import MapView from "@/components/MapView";
import DashboardLayout from "@/components/layout/dashboard-layout";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useToast } from "@/hooks/use-toast";
import { useConfirm } from "@/hooks/use-confirm";
import PlanLimitDialog from "@/components/PlanLimitDialog";
import { apiClient } from "@/lib/api-client";

const DEFAULT_RADIUS_METERS = 100;

const RISK_FILTER_OPTIONS = [
  { value: "flagged", label: "עם דגלי סיכון" },
  { value: "clean", label: "ללא דגלי סיכון" },
] as const;

const DOCUMENTS_FILTER_OPTIONS = [
  { value: "with", label: "עם מסמכים" },
  { value: "without", label: "ללא מסמכים" },
] as const;

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
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
  const [viewMode, setViewMode] = useState<'table' | 'cards' | 'map'>('table');
  const { user, isAuthenticated, refreshUser } = useAuth();
  const onboardingState = React.useMemo(() => selectOnboardingState(user), [user]);
  const router = useRouter();
  const pathname = usePathname();
  const { toast } = useToast();
  const { confirm } = useConfirm();

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
    router,
    pathname,
    searchParams,
  ]);

  // Function to fetch assets
  const fetchAssets = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get("/api/assets");
      if (response.ok) {
        setAssets(response.data.rows);
      } else {
        console.error("Failed to fetch assets:", response.error);
      }
    } catch (error) {
      console.error("Error fetching assets:", error);
    } finally {
      setLoading(false);
    }
  };

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
        setAssets(prev => prev.filter(a => a.id !== assetId));
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
  const handleBulkDelete = async () => {
    if (!isAuthenticated) {
      router.push("/auth?redirect=" + encodeURIComponent("/assets"));
      return;
    }

    const confirmed = await confirm({
      title: "מחיקת נכסים נבחרים",
      description: "האם אתה בטוח שברצונך למחוק את הנכסים הנבחרים? פעולה זו לא ניתנת לביטול.",
      confirmText: "מחק הכל",
      cancelText: "ביטול",
      variant: "destructive",
    });

    if (!confirmed) return;

    // This would be implemented with actual bulk delete API
    toast({
      title: "פונקציונליות במפתח",
      description: "מחיקה מרובה תהיה זמינה בקרוב",
    });
  };

  const handleBulkExport = () => {
    // This would trigger export of selected assets
    toast({
      title: "ייצוא מרובה",
      description: "ייצוא נכסים נבחרים החל",
    });
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

  useEffect(() => {
    fetchAssets();
  }, []);


  const cityOptions = React.useMemo(
    () =>
      Array.from(
        new Set(assets.map((l) => l.city).filter(Boolean))
      ) as string[],
    [assets]
  );
  const typeOptions = React.useMemo(
    () =>
      Array.from(
        new Set(assets.map((l) => l.type).filter(Boolean))
      ) as string[],
    [assets]
  );
  const neighborhoodOptions = React.useMemo(
    () =>
      Array.from(
        new Set(assets.map((l) => l.neighborhood).filter(Boolean))
      ) as string[],
    [assets]
  );
  const zoningOptions = React.useMemo(
    () =>
      Array.from(
        new Set(assets.map((l) => l.zoning).filter(Boolean))
      ) as string[],
    [assets]
  );

  const statusOptions = React.useMemo(() => {
    const counts = new Map<string, { label: string; count: number }>();
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

    assets.forEach((asset) => {
      const statusValue = asset.assetStatus ?? "none";
      const existing = counts.get(statusValue);
      if (existing) {
        existing.count += 1;
      } else {
        counts.set(statusValue, { label: getLabel(statusValue), count: 1 });
      }
    });

    return Array.from(counts.entries()).map(([value, data]) => ({
      value,
      label: data.label,
      count: data.count,
    }));
  }, [assets]);

  const riskFilterOptions = React.useMemo(
    () => [...RISK_FILTER_OPTIONS],
    []
  );

  const documentsFilterOptions = React.useMemo(
    () => [...DOCUMENTS_FILTER_OPTIONS],
    []
  );

  const filteredAssets = React.useMemo(
    () =>
      assets.filter((l) => {
        // Search filter
        if (search) {
          const lower = search.toLowerCase();
          const addressLower = l.address?.toLowerCase() || '';
          const cityLower = l.city?.toLowerCase() || '';
          const typeLower = l.type?.toLowerCase() || '';
          if (!(addressLower.includes(lower) || cityLower.includes(lower) || typeLower.includes(lower))) {
            return false;
          }
        }
        
        // City filter
        if (city && city !== "all" && l.city !== city) {
          return false;
        }
        
        // Type filter
        if (typeFilter && typeFilter !== "all" && l.type !== typeFilter) {
          return false;
        }

        // Price filters - exclude items without price when price filters are applied
        if (priceMin != null || priceMax != null) {
          if (l.price == null) {
            return false;
          }
          if (priceMin != null && l.price < priceMin) {
            return false;
          }
          if (priceMax != null && l.price > priceMax) {
            return false;
          }
        }

        if (neighborhood && neighborhood !== "all" && l.neighborhood !== neighborhood) {
          return false;
        }

        if (zoning && zoning !== "all" && l.zoning !== zoning) {
          return false;
        }

        if (riskFilter === "flagged" && !(l.riskFlags && l.riskFlags.length > 0)) {
          return false;
        }

        if (riskFilter === "clean" && l.riskFlags && l.riskFlags.length > 0) {
          return false;
        }

        if (documentsFilter === "with" && !(l.documents && l.documents.length > 0)) {
          return false;
        }

        if (documentsFilter === "without" && l.documents && l.documents.length > 0) {
          return false;
        }

        if (statusFilter && statusFilter !== "all") {
          const value = l.assetStatus ?? "none";
          if (value !== statusFilter) {
            return false;
          }
        }

        return true;
      }),
    [
      assets,
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
    ]
  );

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        {isAuthenticated && getCompletionPct(onboardingState) < 100 && <OnboardingProgress state={onboardingState} />}
        {/* Skip link for accessibility */}
        <a href="#main-content" className="skip-link">דלג לתוכן הראשי</a>
        
        {/* Header */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">רשימת נכסים</h1>
            <p className="text-muted-foreground">
              {loading ? 'טוען נכסים...' : `${assets.length} נכסים עם נתוני שמאות ותכנון מלאים`}
            </p>
          </div>
        </div>


        {/* Asset Creation Sheet - Keep the form but remove the trigger button */}
        {isAuthenticated && (
          <Sheet open={open} onOpenChange={setOpen}>
                <SheetContent>
                  <SheetHeader>
                    <SheetTitle>הוסף נכס חדש</SheetTitle>
                    <SheetDescription>
                      הזן פרטי הנכס כדי להתחיל תהליך העשרת מידע
                    </SheetDescription>
                  </SheetHeader>
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
                            <SelectTrigger>
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
                            className={form.formState.errors.city ? "border-error" : ""}
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
                            className={form.formState.errors.street ? "border-error" : ""}
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
                            {...form.register("houseNumber")}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="apartment">מספר דירה</Label>
                          <Input
                            id="apartment"
                            placeholder="הזן מספר דירה"
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
                            className={form.formState.errors.block ? "border-error" : ""}
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
                            className={form.formState.errors.parcel ? "border-error" : ""}
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
                        {...form.register("radius", { valueAsNumber: true })}
                      />
                    </div>

                    <Button type="submit" className="w-full">
                      הוסף נכס
                    </Button>
                  </form>
                </SheetContent>
              </Sheet>
            )}


        {/* Assets View */}
        <Card id="main-content">
          <CardHeader>
            <CardTitle>נכסים זמינים</CardTitle>
            <CardDescription>
              {viewMode === 'map' 
                ? 'מפת נכסים עם שכבות מידע ממשלתיות ועירוניות'
                : 'טבלת נכסים עם נתוני שמאות, תכנון וניתוח שווי'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                <div className="flex flex-col items-center justify-center py-12 space-y-4">
                  <RefreshCw className="h-8 w-8 animate-spin text-brand-teal" />
                  <div className="text-center">
                    <p className="text-muted-foreground">טוען נכסים...</p>
                    <p className="text-sm text-muted-foreground">אנא המתן בזמן שאנחנו מביאים את הנתונים העדכניים</p>
                  </div>
                </div>
                {/* Skeleton table for better UX */}
                <div className="hidden sm:block">
                  <div className="space-y-3">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <div key={i} className="flex space-x-4">
                        <Skeleton className="h-4 w-4" />
                        <Skeleton className="h-4 w-48" />
                        <Skeleton className="h-4 w-20" />
                        <Skeleton className="h-4 w-16" />
                        <Skeleton className="h-4 w-12" />
                        <Skeleton className="h-4 w-16" />
                        <Skeleton className="h-4 w-20" />
                        <Skeleton className="h-4 w-16" />
                      </div>
                    ))}
                  </div>
                </div>
                {/* Skeleton cards for mobile */}
                <div className="sm:hidden space-y-2">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="p-4 border rounded-lg space-y-2">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-1/2" />
                      <div className="flex space-x-2">
                        <Skeleton className="h-6 w-16" />
                        <Skeleton className="h-6 w-20" />
                        <Skeleton className="h-6 w-12" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : viewMode === 'map' ? (
              <MapView
                key={`map-${viewMode}-${filteredAssets.length}`}
                assets={filteredAssets}
                center={[34.98, 31.0]}
                zoom={14}
                onAssetClick={(asset) => router.push(`/assets/${asset.id}`)}
                searchValue={search}
                onSearchChange={setSearch}
                height="600px"
                onBackToTable={() => setViewMode('table')}
              />
            ) : (
              <AssetsTable 
                data={filteredAssets} 
                loading={loading} 
                onDelete={handleDeleteAsset}
                searchValue={search}
                onSearchChange={setSearch}
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
                  }
                }}
                onRefresh={fetchAssets}
                onAddNew={() => {
                  if (isAuthenticated) {
                    setOpen(true);
                  } else {
                    handleProtectedAction("add-asset");
                  }
                }}
                viewMode={viewMode}
                onViewModeChange={setViewMode}
                bulkActions={[
                  {
                    label: "מחק נבחרים",
                    action: handleBulkDelete,
                    icon: <Trash2 className="h-4 w-4" />,
                  },
                  {
                    label: "ייצא נבחרים",
                    action: handleBulkExport,
                    icon: <Download className="h-4 w-4" />,
                  }
                ]}
              />
            )}
          </CardContent>
        </Card>

        {/* Summary */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            מציג {filteredAssets.length} מתוך {assets.length} נכסים
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

      </div>
    </DashboardLayout>
  );
}
