"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import { Switch } from "@/components/ui/switch";
import { AlertCircle, DownloadCloud, FileJson, FileSpreadsheet, Loader2, RefreshCcw } from "lucide-react";
import { cn } from "@/lib/utils";

const POLL_INTERVAL_MS = 1500;

interface ImportDialogNadlanOneProps {
  open: boolean;
  onOpenChange: (value: boolean) => void;
  mode: "customers" | "properties";
}

interface ImportSummary {
  [key: string]: number | string;
}

interface ImportRowResult {
  mode: string;
  identifier: string;
  status: string;
  message?: string;
}

export function ImportDialogNadlanOne({ open, onOpenChange, mode }: ImportDialogNadlanOneProps) {
  const [customersFile, setCustomersFile] = useState<File | null>(null);
  const [propertiesFile, setPropertiesFile] = useState<File | null>(null);
  const [dryRun, setDryRun] = useState(false);
  const [conflictPolicy, setConflictPolicy] = useState<"update" | "skip">("update");
  const [enableLinking, setEnableLinking] = useState(mode === "properties");
  const [submitting, setSubmitting] = useState(false);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [summary, setSummary] = useState<ImportSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reportCsv, setReportCsv] = useState<string | null>(null);
  const [reportJson, setReportJson] = useState<string | null>(null);
  const [rowResults, setRowResults] = useState<ImportRowResult[]>([]);

  useEffect(() => {
    if (!open) {
      resetState();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const resetState = useCallback(() => {
    setCustomersFile(null);
    setPropertiesFile(null);
    setDryRun(false);
    setConflictPolicy("update");
    setEnableLinking(mode === "properties");
    setSubmitting(false);
    setBatchId(null);
    setStatus(null);
    setSummary(null);
    setError(null);
    setReportCsv(null);
    setReportJson(null);
    setRowResults([]);
  }, [mode]);

  const canSubmit = useMemo(() => {
    if (submitting) return false;
    if (!open) return false;
    if (mode === "customers" && !customersFile) return false;
    if (mode === "properties" && !propertiesFile) return false;
    return true;
  }, [submitting, open, mode, customersFile, propertiesFile]);

  const startPolling = useCallback(
    (id: string) => {
      let cancelled = false;
      const poll = async () => {
        if (cancelled) return;
        try {
          const accessToken = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
          const response = await fetch(`/api/imports/${id}`, {
            method: "GET",
            credentials: "include",
            cache: "no-store",
            headers: {
              ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
            },
          });
          if (!response.ok) {
            throw new Error("שגיאה בבדיקת סטטוס הייבוא");
          }
          const data = await response.json();
          setStatus(data.status);
          setSummary(data.totals || null);
          setReportCsv(data.report_csv_url || null);
          setReportJson(data.report_json_url || null);

          if (data.status === "COMPLETED" || data.status === "FAILED" || data.status === "CANCELLED") {
            if (data.report_json_url) {
              try {
                const reportResponse = await fetch(data.report_json_url, { cache: "no-store" });
                if (reportResponse.ok) {
                  const json = await reportResponse.json();
                  setRowResults(Array.isArray(json) ? json : []);
                }
              } catch (err) {
                console.warn("Failed to fetch report JSON", err);
              }
            }
            if (data.status === "FAILED" && data.totals?.error) {
              setError(data.totals.error as string);
            }
            return;
          }
        } catch (err) {
          console.error(err);
          setError(err instanceof Error ? err.message : "אירעה שגיאה");
        }
      };

      poll();
      const timer = setInterval(poll, POLL_INTERVAL_MS);
      return () => {
        cancelled = true;
        clearInterval(timer);
      };
    },
    []
  );

  useEffect(() => {
    if (!batchId || !open) {
      return;
    }
    const stopPolling = startPolling(batchId);
    return () => {
      if (stopPolling) {
        stopPolling();
      }
    };
  }, [batchId, open, startPolling]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);

    const formData = new FormData();
    formData.append("mode", mode);
    formData.append("dry_run", dryRun ? "true" : "false");
    formData.append("conflict_policy", conflictPolicy);
    formData.append("enable_linking", enableLinking ? "true" : "false");
    const accessToken = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (customersFile) {
      formData.append("customers_csv", customersFile, customersFile.name);
    }
    if (propertiesFile) {
      formData.append("properties_csv", propertiesFile, propertiesFile.name);
    }

    try {
      const response = await fetch("/api/imports/nadlanone", {
        method: "POST",
        body: formData,
        credentials: "include",
        headers: {
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "הייבוא נכשל");
      }
      setBatchId(payload.batch_id);
      setStatus(payload.status);
    } catch (err) {
      setError(err instanceof Error ? err.message : "אירעה שגיאה");
      setSubmitting(false);
    }
  };

  const handleCancel = async () => {
    if (!batchId) return;
    try {
      const accessToken = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const response = await fetch(`/api/imports/${batchId}`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
        body: JSON.stringify({ action: "cancel" }),
      });
      if (!response.ok) {
        throw new Error("לא ניתן לבטל את הייבוא");
      }
      const data = await response.json();
      setStatus(data.status);
      setSummary(data.totals || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "אירעה שגיאה");
    }
  };

  const topErrors = useMemo(() => {
    return rowResults.filter(item => item.status === "error").slice(0, 5);
  }, [rowResults]);

  const summaryEntries = useMemo(() => {
    if (!summary) return [];
    return Object.entries(summary);
  }, [summary]);

  const showProgress = batchId !== null && status !== "COMPLETED" && status !== "FAILED" && status !== "CANCELLED";
  const showResults = status === "COMPLETED";
  const showFailure = status === "FAILED";

  const customersLabel = mode === "customers" ? "קובץ לקוחות (CSV)" : "קובץ לקוחות (CSV, אופציונלי)";
  const propertiesLabel = mode === "properties" ? "קובץ נכסים (CSV)" : "קובץ נכסים (CSV, אופציונלי)";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl" dir="rtl">
        <DialogHeader>
          <DialogTitle>ייבוא נתונים מנדל&quot;ן וואן</DialogTitle>
          <DialogDescription>
            העלו קובצי CSV מיוצאים ממערכת נדל&quot;ן וואן ונבצע ייבוא חכם של {mode === "customers" ? "לקוחות" : "נכסים"} לתוך Nadlaner.
          </DialogDescription>
        </DialogHeader>

        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div className="grid gap-2">
              <Label htmlFor="customers-file">{customersLabel}</Label>
              <Input
                id="customers-file"
                type="file"
                accept=".csv,text/csv"
                onChange={event => setCustomersFile(event.target.files?.[0] ?? null)}
              />
              {customersFile && <span className="text-xs text-muted-foreground">{customersFile.name}</span>}
            </div>

            <div className="grid gap-2">
              <Label htmlFor="properties-file">{propertiesLabel}</Label>
              <Input
                id="properties-file"
                type="file"
                accept=".csv,text/csv"
                onChange={event => setPropertiesFile(event.target.files?.[0] ?? null)}
              />
              {propertiesFile && <span className="text-xs text-muted-foreground">{propertiesFile.name}</span>}
            </div>

            <div className="grid gap-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <Label htmlFor="dry-run" className="font-medium">בדיקת יבוא (ללא יצירה)</Label>
                  <p className="text-xs text-muted-foreground">נבצע ולידציה מלאה ונציג תוצאות מבלי לשנות את הנתונים במערכת.</p>
                </div>
                <Switch id="dry-run" checked={dryRun} onCheckedChange={setDryRun} />
              </div>

              <div className="grid gap-1">
                <Label>טיפול בהתנגשויות</Label>
                <Select value={conflictPolicy} onValueChange={value => setConflictPolicy(value as "update" | "skip") }>
                  <SelectTrigger>
                    <SelectValue placeholder="בחרו מדיניות" />
                  </SelectTrigger>
                  <SelectContent className="rtl:text-right">
                    <SelectItem value="update">עדכן רשומות קיימות</SelectItem>
                    <SelectItem value="skip">דלג על רשומות קיימות</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between gap-3">
                <div>
                  <Label htmlFor="linking" className="font-medium">קישור אוטומטי בין לקוחות ונכסים</Label>
                  <p className="text-xs text-muted-foreground">התאמת נכסים ללקוחות לפי טלפון והתאמה מטושטשת של שמות.</p>
                </div>
                <Switch id="linking" checked={enableLinking} onCheckedChange={setEnableLinking} />
              </div>
            </div>
          </div>

          {error && (
            <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive flex gap-2">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {batchId && (
            <div className="rounded-md border bg-muted/30 p-4 space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <div className="font-medium">סטטוס ייבוא</div>
                <div className={cn("px-2 py-1 text-xs rounded-full", {
                  "bg-amber-100 text-amber-900": showProgress,
                  "bg-emerald-100 text-emerald-900": status === "COMPLETED",
                  "bg-red-100 text-red-900": status === "FAILED",
                  "bg-slate-200 text-slate-900": status === "CANCELLED",
                })}>
                  {status || "PENDING"}
                </div>
              </div>

              {showProgress && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  מתבצע ייבוא... אפשר להמשיך לעבוד במערכת.
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={handleCancel}
                    className="ml-auto rtl:ml-0 rtl:mr-auto"
                  >
                    <RefreshCcw className="h-4 w-4 mr-2 rtl:ml-2 rtl:mr-0" />
                    בטל ייבוא
                  </Button>
                </div>
              )}

              {summaryEntries.length > 0 && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {summaryEntries.map(([key, value]) => (
                    <div key={key} className="rounded bg-white/70 p-2 text-xs shadow-sm">
                      <div className="font-semibold text-foreground">{key}</div>
                      <div className="text-muted-foreground text-sm">{String(value)}</div>
                    </div>
                  ))}
                </div>
              )}

              {showResults && reportCsv && (
                <div className="flex flex-wrap gap-2 text-xs">
                  <Button asChild variant="outline" size="sm">
                    <a href={reportCsv} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2">
                      <FileSpreadsheet className="h-4 w-4" />
                      דוח CSV
                    </a>
                  </Button>
                  {reportJson && (
                    <Button asChild variant="outline" size="sm">
                      <a href={reportJson} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2">
                        <FileJson className="h-4 w-4" />
                        דוח JSON
                      </a>
                    </Button>
                  )}
                </div>
              )}

              {showFailure && topErrors.length > 0 && (
                <div className="space-y-2">
                  <div className="font-medium text-destructive">שגיאות מובילות</div>
                  <ul className="list-disc pr-5 rtl:pr-0 rtl:pl-5 text-xs text-destructive">
                    {topErrors.map(item => (
                      <li key={`${item.mode}-${item.identifier}`}>{item.identifier}: {item.message}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          <DialogFooter className="flex-col-reverse sm:flex-row sm:justify-between gap-2">
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)} className="w-full sm:w-auto">
              סגור
            </Button>
            <Button type="submit" disabled={!canSubmit} className="w-full sm:w-auto">
              {submitting ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  מעלה...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <DownloadCloud className="h-4 w-4" />
                  התחלת ייבוא
                </span>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default ImportDialogNadlanOne;
