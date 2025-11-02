"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import DashboardLayout from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/Badge";
import { Loader2, RefreshCcw, FileSpreadsheet, FileJson } from "lucide-react";
import { InlineAlert } from "@/components/ui/inline-alert";
import { useToast } from "@/hooks/use-toast";

interface ImportBatchRow {
  id: string;
  source: string;
  mode: "customers" | "properties";
  status: string;
  totals: Record<string, any> | null;
  created_at: string;
  updated_at: string;
  report_csv_url?: string | null;
  report_json_url?: string | null;
}

const MODE_LABELS: Record<string, string> = {
  customers: "לקוחות",
  properties: "נכסים",
};

const STATUS_VARIANTS: Record<string, { label: string; variant: "default" | "secondary" | "success" | "destructive" | "outline" }> = {
  PENDING: { label: "ממתין", variant: "secondary" },
  RUNNING: { label: "בתהליך", variant: "secondary" },
  COMPLETED: { label: "הושלם", variant: "success" },
  FAILED: { label: "נכשל", variant: "destructive" },
  CANCELLED: { label: "בוטל", variant: "outline" },
};

function formatDate(value: string) {
  if (!value) return "";
  try {
    const date = new Date(value);
    return new Intl.DateTimeFormat("he-IL", {
      dateStyle: "short",
      timeStyle: "short",
    }).format(date);
  } catch (error) {
    return value;
  }
}

function extractTotal(totals: Record<string, any> | null | undefined, key: string): string {
  if (!totals) return "0";
  const raw = totals[key];
  if (raw === undefined || raw === null) return "0";
  return typeof raw === "number" ? raw.toString() : String(raw);
}

export default function ImportHistoryPage() {
  const [modeFilter, setModeFilter] = useState<"all" | "customers" | "properties">("all");
  const [loading, setLoading] = useState(false);
  const [rows, setRows] = useState<ImportBatchRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const loadImports = useCallback(async ({ withSuccessToast = false } = {}) => {
    try {
      setLoading(true);
      setError(null);
      const query = modeFilter === "all" ? "" : `?mode=${modeFilter}`;
      const response = await fetch(`/api/imports${query}`, {
        credentials: "include",
        cache: "no-store",
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || "טעינת הייבוא נכשלה");
      }
      const payload = await response.json();
      setRows(payload.results || []);
      if (withSuccessToast) {
        toast({
          variant: "success",
          title: "הרשימה עודכנה",
          description: "ייבוא הנתונים נטען מחדש בהצלחה.",
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "אירעה שגיאה בטעינת נתוני הייבוא";
      setError(message);
      toast({
        variant: "destructive",
        title: "שגיאה בטעינת הייבוא",
        description: message,
      });
    } finally {
      setLoading(false);
    }
  }, [modeFilter, toast]);

  useEffect(() => {
    loadImports();
  }, [loadImports]);

  const hasRows = rows.length > 0;

  const modeOptions = useMemo(
    () => [
      { value: "all", label: "הכל" },
      { value: "customers", label: "לקוחות" },
      { value: "properties", label: "נכסים" },
    ],
    []
  );

  return (
    <DashboardLayout>
      <div className="container mx-auto p-4 sm:p-6 space-y-6" dir="rtl">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold">היסטוריית ייבוא מנדל&quot;ן וואן</h1>
            <p className="text-sm text-muted-foreground">עקבו אחר ייבוא הלקוחות והנכסים ודלו את דוחות הסיכום.</p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <Select value={modeFilter} onValueChange={(value) => setModeFilter(value as typeof modeFilter)}>
              <SelectTrigger className="w-full sm:w-40">
                <SelectValue placeholder="סינון לפי סוג" />
              </SelectTrigger>
              <SelectContent className="rtl:text-right">
                {modeOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              onClick={() => loadImports({ withSuccessToast: true })}
              disabled={loading}
              className="flex items-center gap-2"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCcw className="h-4 w-4" />}
              רענון
            </Button>
          </div>
        </div>

        <InlineAlert
          variant="info"
          title="כיצד מתבצע הייבוא?"
          className="border-dashed bg-info/5"
        >
          <ol className="list-decimal space-y-1 pr-4 text-sm rtl:pr-0 rtl:pl-4">
            <li>סננו לפי סוג הייבוא כדי להתמקד בקבוצת הנתונים הרלוונטית.</li>
            <li>פתחו את דוח הסיכום לבחינת השורות שנוצרו, עודכנו או דולגו.</li>
            <li>השתמשו בדוח השגיאות כדי לטפל במהירות ברישומים שנכשלו.</li>
          </ol>
        </InlineAlert>

        {error && (
          <InlineAlert variant="destructive" title="טעינת הנתונים נכשלה" className="border-solid">
            {error}
          </InlineAlert>
        )}

        <div className="rounded-xl border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-right">מזהה</TableHead>
                <TableHead className="text-right">סוג</TableHead>
                <TableHead className="text-right">סטטוס</TableHead>
                <TableHead className="text-right">נוצר</TableHead>
                <TableHead className="text-right">נעדכן</TableHead>
                <TableHead className="text-right">נוצרו</TableHead>
                <TableHead className="text-right">עודכנו</TableHead>
                <TableHead className="text-right">דלגו</TableHead>
                <TableHead className="text-right">שגיאות</TableHead>
                <TableHead className="text-right">דוחות</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {!hasRows && !loading && (
                <TableRow>
                  <TableCell colSpan={10} className="py-10">
                    <InlineAlert
                      variant="info"
                      title="אין ייבואים להצגה עדיין"
                      className="mx-auto max-w-xl flex-col items-center text-center sm:flex-row sm:items-start sm:text-right"
                    >
                      התחילו תהליך ייבוא חדש ממסך הייבוא, או חזרו לכאן לאחר שהדאטה סונכרנה.
                    </InlineAlert>
                  </TableCell>
                </TableRow>
              )}
              {rows.map((row) => {
                const totals = row.totals || {};
                const statusMeta = STATUS_VARIANTS[row.status] || { label: row.status, variant: "secondary" as const };
                return (
                  <TableRow key={row.id}>
                    <TableCell className="font-mono text-xs">{row.id}</TableCell>
                    <TableCell>{MODE_LABELS[row.mode] || row.mode}</TableCell>
                    <TableCell>
                      <Badge variant={statusMeta.variant}>{statusMeta.label}</Badge>
                    </TableCell>
                    <TableCell>{formatDate(row.created_at)}</TableCell>
                    <TableCell>{formatDate(row.updated_at)}</TableCell>
                    <TableCell>{extractTotal(totals, "inserted")}</TableCell>
                    <TableCell>{extractTotal(totals, "updated")}</TableCell>
                    <TableCell>{extractTotal(totals, "skipped")}</TableCell>
                    <TableCell>{extractTotal(totals, "errors")}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        {row.report_csv_url && (
                          <Button asChild variant="ghost" size="sm" className="h-8 px-2 text-xs">
                            <a href={row.report_csv_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1">
                              <FileSpreadsheet className="h-4 w-4" />CSV
                            </a>
                          </Button>
                        )}
                        {row.report_json_url && (
                          <Button asChild variant="ghost" size="sm" className="h-8 px-2 text-xs">
                            <a href={row.report_json_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1">
                              <FileJson className="h-4 w-4" />JSON
                            </a>
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
              {loading && (
                <TableRow>
                  <TableCell colSpan={10} className="text-center py-10">
                    <div className="flex flex-col items-center gap-2 text-muted-foreground">
                      <Loader2 className="h-5 w-5 animate-spin" />
                      טוען נתוני ייבוא...
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </DashboardLayout>
  );
}
