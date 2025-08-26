"use client";
import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
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
} from "@/components/ui/card";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Plus, RefreshCw, Search, Filter } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Asset } from "@/lib/data";
import AssetsTable from "@/components/AssetsTable";
import DashboardLayout from "@/components/layout/dashboard-layout";
import { useRouter } from "next/navigation";

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [city, setCity] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [priceMin, setPriceMin] = useState<number>();
  const [priceMax, setPriceMax] = useState<number>();
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  const handleProtectedAction = () => {
    if (!isAuthenticated) {
      router.push("/auth?redirect=" + encodeURIComponent("/assets"));
    }
  };

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

  const newAssetSchema = z.object({
    scopeType: z.enum(["address", "neighborhood", "street", "city", "parcel"]),
    // Common fields
    address: z.string().min(1, "כתובת נדרשת"),
    city: z.string().min(1, "עיר נדרשת"),
    // Street-specific fields
    street: z.string().optional(),
    number: z.number().optional(),
    // Parcel-specific fields
    gush: z.string().optional(),
    helka: z.string().optional(),
    // Radius for neighborhood/city searches
    radius: z.number().min(100).max(5000).optional(),
  });

  type NewAsset = z.infer<typeof newAssetSchema>;

  const form = useForm<NewAsset>({
    resolver: zodResolver(newAssetSchema),
    defaultValues: {
      scopeType: "address",
      address: "",
      city: "",
      street: "",
      number: undefined,
      gush: "",
      helka: "",
      radius: 500,
    },
  });

  const onSubmit = async (data: NewAsset) => {
    try {
      const body = {
        scope: {
          type: data.scopeType,
          value:
            data.scopeType === "address"
              ? data.address
              : data.scopeType === "street"
              ? `${data.street} ${data.number}`
              : data.scopeType === "parcel"
              ? `${data.gush}/${data.helka}`
              : data.address,
          city: data.city,
        },
        address: data.address,
        city: data.city,
        street: data.street,
        number: data.number,
        gush: data.gush,
        helka: data.helka,
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
        if (
          search &&
          !l.address.toLowerCase().includes(search.toLowerCase()) &&
          !l.city?.toLowerCase().includes(search.toLowerCase())
        ) {
          return false;
        }
        if (city && city !== "all" && l.city !== city) {
          return false;
        }
        if (typeFilter && typeFilter !== "all" && l.type !== typeFilter) {
          return false;
        }
        if (priceMin && l.price < priceMin) {
          return false;
        }
        if (priceMax && l.price > priceMax) {
          return false;
        }
        return true;
      }),
    [assets, search, city, typeFilter, priceMin, priceMax]
  );

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
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
                      <Label htmlFor="scopeType">סוג חיפוש</Label>
                      <Select
                        onValueChange={(value) =>
                          form.setValue("scopeType", value as any)
                        }
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="בחר סוג חיפוש" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="address">כתובת מדויקת</SelectItem>
                          <SelectItem value="neighborhood">שכונה</SelectItem>
                          <SelectItem value="street">רחוב</SelectItem>
                          <SelectItem value="city">עיר</SelectItem>
                          <SelectItem value="parcel">גוש/חלקה</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="address">כתובת</Label>
                      <Input
                        id="address"
                        placeholder="הזן כתובת"
                        {...form.register("address")}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="city">עיר</Label>
                      <Input
                        id="city"
                        placeholder="הזן עיר"
                        {...form.register("city")}
                      />
                    </div>

                    {form.watch("scopeType") === "street" && (
                      <>
                        <div className="space-y-2">
                          <Label htmlFor="street">רחוב</Label>
                          <Input
                            id="street"
                            placeholder="הזן רחוב"
                            {...form.register("street")}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="number">מספר בית</Label>
                          <Input
                            id="number"
                            type="number"
                            placeholder="הזן מספר בית"
                            {...form.register("number", {
                              valueAsNumber: true,
                            })}
                          />
                        </div>
                      </>
                    )}

                    {form.watch("scopeType") === "parcel" && (
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
                      </>
                    )}

                    {(form.watch("scopeType") === "neighborhood" ||
                      form.watch("scopeType") === "city") && (
                      <div className="space-y-2">
                        <Label htmlFor="radius">רדיוס חיפוש (מטרים)</Label>
                        <Input
                          id="radius"
                          type="number"
                          placeholder="500"
                          {...form.register("radius", { valueAsNumber: true })}
                        />
                      </div>
                    )}

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
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Filter className="h-4 w-4" />
              סינון נכסים
            </CardTitle>
          </CardHeader>
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
              <AssetsTable data={filteredAssets} />
            )}
          </CardContent>
        </Card>

        {/* Summary */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            מציג {filteredAssets.length} מתוך {assets.length} נכסים עם נתוני
            שמאות מלאים
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}
