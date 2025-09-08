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
import {
  Plus,
  RefreshCw,
  Search,
  Filter,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import OnboardingProgress from "@/components/OnboardingProgress";
import { selectOnboardingState } from "@/onboarding/selectors";
import type { Asset } from "@/lib/normalizers/asset";
import AssetsTable from "@/components/AssetsTable";
import DashboardLayout from "@/components/layout/dashboard-layout";
import { useRouter, useSearchParams, usePathname } from "next/navigation";

const DEFAULT_RADIUS_METERS = 100;

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [filtersOpen, setFiltersOpen] = useState(false);
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
  const { user, isAuthenticated } = useAuth();
  const onboardingState = selectOnboardingState(user);
  const router = useRouter();
  const pathname = usePathname();

  const [citySuggestions, setCitySuggestions] = useState<string[]>([]);
  const [streetSuggestions, setStreetSuggestions] = useState<string[]>([]);

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

  const handleProtectedAction = () => {
    if (!isAuthenticated) {
      router.push("/auth?redirect=" + encodeURIComponent("/assets"));
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
    const query = params.toString();
    const newUrl = query ? `${pathname}?${query}` : pathname;
    const currentQuery = searchParams.toString();
    const currentUrl = currentQuery ? `${pathname}?${currentQuery}` : pathname;
    if (newUrl !== currentUrl) {
      router.replace(newUrl, { scroll: false });
    }
  }, [search, city, typeFilter, priceMin, priceMax, router, pathname, searchParams]);

  // Function to fetch assets
  const fetchAssets = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/assets");
      if (response.ok) {
        const data = await response.json();
        setAssets(data.rows);
      } else {
        console.error("Failed to fetch assets");
      }
    } catch (error) {
      console.error("Error fetching assets:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAsset = async (assetId: number) => {
    if (!confirm("האם אתה בטוח שברצונך למחוק נכס זה?")) {
      return;
    }

    setDeleting(assetId);
    try {
      const response = await fetch("/api/assets", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ assetId }),
      });

      if (response.ok) {
        setAssets(prev => prev.filter(a => a.id !== assetId));
        alert("הנכס נמחק בהצלחה");
      } else {
        const error = await response.json();
        alert(`שגיאה במחיקת הנכס: ${error.error}`);
      }
    } catch (error) {
      console.error("Error deleting asset:", error);
      alert("שגיאה במחיקת הנכס");
    } finally {
      setDeleting(null);
    }
  };

  const newAssetSchema = z
    .object({
      locationType: z.enum(["address", "parcel"]),
      city: z.string().optional(),
      street: z.string().optional(),
      houseNumber: z.string().optional(),
      apartment: z.string().optional(),
      gush: z.string().optional(),
      helka: z.string().optional(),
      subHelka: z.string().optional(),
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
        if (!data.gush) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["gush"],
            message: "גוש נדרש",
          });
        }
        if (!data.helka) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["helka"],
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
      gush: "",
      helka: "",
      subHelka: "",
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
                value: `${data.gush}/${data.helka}`,
              },
              gush: data.gush,
              helka: data.helka,
              subhelka: data.subHelka,
              radius: data.radius,
            };

      const response = await fetch("/api/assets", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      if (response.ok) {
        form.reset();
        setOpen(false);
        // Refresh assets to show the new asset
        await fetchAssets();
      } else {
        const errorData = await response.json();
        console.error("Failed to create asset:", errorData);
      }
    } catch (error) {
      console.error("Error creating asset:", error);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, []);

  // Show filters by default on desktop, hide on mobile
  useEffect(() => {
    if (typeof window !== "undefined" && window.innerWidth >= 768) {
      setFiltersOpen(true);
    }
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

  const filteredAssets = React.useMemo(
    () =>
      assets.filter((l) => {
        if (search) {
          const lower = search.toLowerCase();
          const addressLower = l.address?.toLowerCase();
          const cityLower = l.city?.toLowerCase();
          if (!(addressLower?.includes(lower) || cityLower?.includes(lower))) {
            return false;
          }
        }
        if (city && city !== "all" && l.city !== city) {
          return false;
        }
        if (typeFilter && typeFilter !== "all" && l.type !== typeFilter) {
          return false;
        }
        if (priceMin != null && l.price != null && l.price < priceMin) {
          return false;
        }
        if (priceMax != null && l.price != null && l.price > priceMax) {
          return false;
        }
        return true;
      }),
    [assets, search, city, typeFilter, priceMin, priceMax]
  );

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        {isAuthenticated && <OnboardingProgress state={onboardingState} />}
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">רשימת נכסים</h1>
            <p className="text-muted-foreground">
              {assets.length} נכסים עם נתוני שמאות ותכנון מלאים
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Button onClick={fetchAssets} variant="outline" disabled={loading}>
              <RefreshCw className="h-4 w-4 mr-2" />
              רענן
            </Button>
            {isAuthenticated ? (
              <Sheet open={open} onOpenChange={setOpen}>
                <SheetTrigger asChild>
                  <Button className="bg-[var(--brand-teal)] text-white hover:bg-[color-mix(in oklab, var(--brand-teal), black 10%)]">
                    הוסף נכס חדש
                  </Button>
                </SheetTrigger>
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
                            {...form.register("city", {
                              onChange: (e) =>
                                fetchCitySuggestions(e.target.value),
                            })}
                          />
                          <datalist id="city-options">
                            {citySuggestions.map((c) => (
                              <option key={c} value={c} />
                            ))}
                          </datalist>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="street">רחוב</Label>
                          <Input
                            id="street"
                            list="street-options"
                            placeholder="בחר רחוב"
                            {...form.register("street", {
                              onChange: (e) =>
                                fetchStreetSuggestions(
                                  e.target.value,
                                  form.getValues("city") || ""
                                ),
                            })}
                          />
                          <datalist id="street-options">
                            {streetSuggestions.map((s) => (
                              <option key={s} value={s} />
                            ))}
                          </datalist>
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
                          <Label htmlFor="gush">גוש</Label>
                          <Input
                            id="gush"
                            placeholder="הזן מספר גוש"
                            {...form.register("gush")}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="helka">חלקה</Label>
                          <Input
                            id="helka"
                            placeholder="הזן מספר חלקה"
                            {...form.register("helka")}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="subHelka">תת חלקה</Label>
                          <Input
                            id="subHelka"
                            placeholder="הזן מספר תת חלקה"
                            {...form.register("subHelka")}
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
            ) : (
              <Button onClick={handleProtectedAction}>
                <Plus className="h-4 w-4 mr-2" />
                התחבר להוספת נכס
              </Button>
            )}
          </div>
        </div>

        {/* Filters */}
        <Card className="border-0 shadow-sm bg-gray-50/50">
          <CardHeader className="pb-4 flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Filter className="h-4 w-4" />
              סינון נכסים
            </CardTitle>
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setFiltersOpen((prev) => !prev)}
            >
              {filtersOpen ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
              <span className="sr-only">Toggle filters</span>
            </Button>
          </CardHeader>
          {filtersOpen && (
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              <div className="space-y-2">
                <Label htmlFor="search">חיפוש</Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="search"
                    placeholder="חיפוש בכתובת או עיר..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="city">עיר</Label>
                <Select value={city} onValueChange={setCity}>
                  <SelectTrigger>
                    <SelectValue placeholder="כל הערים" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">כל הערים</SelectItem>
                    {cityOptions.map((cityOption) => (
                      <SelectItem key={cityOption} value={cityOption}>
                        {cityOption}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="type">סוג נכס</Label>
                <Select value={typeFilter} onValueChange={setTypeFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="כל הסוגים" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">כל הסוגים</SelectItem>
                    {typeOptions.map((type) => (
                      <SelectItem key={type} value={type}>
                        {type}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="priceMin">מחיר מינימלי</Label>
                <Input
                  id="priceMin"
                  type="number"
                  placeholder="₪"
                  value={priceMin || ""}
                  onChange={(e) =>
                    setPriceMin(
                      e.target.value ? Number(e.target.value) : undefined
                    )
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="priceMax">מחיר מקסימלי</Label>
                <Input
                  id="priceMax"
                  type="number"
                  placeholder="₪"
                  value={priceMax || ""}
                  onChange={(e) =>
                    setPriceMax(
                      e.target.value ? Number(e.target.value) : undefined
                    )
                  }
                />
              </div>
            </div>
            </CardContent>
          )}
        </Card>

        {/* Assets Table */}
        <Card>
          <CardHeader>
            <CardTitle>נכסים זמינים</CardTitle>
            <CardDescription>
              טבלת נכסים עם נתוני שמאות, תכנון וניתוח שווי
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-8 w-8 animate-spin" />
                <span className="ml-2">טוען נכסים...</span>
              </div>
            ) : (
              <AssetsTable data={filteredAssets} loading={loading} onDelete={handleDeleteAsset} />
            )}
          </CardContent>
        </Card>

        {/* Summary */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            מציג {filteredAssets.length} מתוך {assets.length} נכסים
          </p>
        </div>

        <Button
          size="icon"
          className="fixed bottom-4 right-4 rounded-full h-14 w-14 sm:hidden"
          onClick={() => setOpen(true)}
        >
          <Plus className="h-6 w-6" />
          <span className="sr-only">הוספת נכס חדש</span>
        </Button>
      </div>
    </DashboardLayout>
  );
}
