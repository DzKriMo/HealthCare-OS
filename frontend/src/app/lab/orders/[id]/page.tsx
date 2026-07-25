"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonCard } from "@/components/ui/skeleton";
import { SpecimenList } from "@/components/laboratory/specimen-list";
import { ResultEntryForm } from "@/components/laboratory/result-entry-form";
import { api, ApiRequestError } from "@/lib/api/client";
import { cn } from "@/lib/utils";

interface OrderDetail {
  id: string;
  patient: string;
  patient_name: string;
  encounter?: string;
  tests: string[];
  test_names: string[];
  status: string;
  priority: string;
  ordered_by_name?: string;
  notes?: string;
  ordered_at: string;
  specimens: unknown[];
  results: ResultItem[];
}

interface ResultItem {
  id: string;
  test_name: string;
  value?: number;
  value_text?: string;
  unit?: string;
  reference_range?: string;
  status: string;
  approved_by_name?: string;
  approved_at?: string;
  notes?: string;
}

const STATUS_BADGES: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  ordered: "bg-blue-100 text-blue-700",
  collected: "bg-yellow-100 text-yellow-700",
  received: "bg-purple-100 text-purple-700",
  in_progress: "bg-indigo-100 text-indigo-700",
  completed: "bg-green-100 text-green-700",
  reviewed: "bg-teal-100 text-teal-700",
  cancelled: "bg-red-100 text-red-700",
};

const PRIORITY_STYLES: Record<string, string> = {
  routine: "border-gray-300 text-gray-600",
  urgent: "border-amber-300 text-amber-700 bg-amber-50",
  stat: "border-red-300 text-red-700 bg-red-50",
};

export default function OrderDetailPage() {
  const router = useRouter(); const params = useParams();
  const orderId = params.id as string;
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [loadError, setLoadError] = useState(""); const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => { if (isAuthenticated && orderId) load(); }, [isAuthenticated, orderId]);

  const load = async () => {
    setLoading(true); setLoadError("");
    try { const d = await api.get<OrderDetail>(`/lab/orders/${orderId}/`); setOrder(d); }
    catch { setLoadError("Failed to load order."); } finally { setLoading(false); }
  };

  const handleResultSubmit = async (data: { test: string; specimen?: string; value?: number; value_text?: string; notes?: string }) => {
    await api.post(`/lab/results/`, { ...data, lab_order: orderId });
    await load();
  };

  const handleApprove = async (resultId: string, action: string) => {
    setBusy(resultId);
    try {
      await api.post(`/lab/results/${resultId}/approve/`, { action });
      await load();
    } catch { /* error handled by UI state */ }
    finally { setBusy(null); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-4xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/lab")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
        </Button>

        {loadError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{loadError} <Button variant="link" size="sm" onClick={load}>Retry</Button></div>}
        {loading && !order && <SkeletonCard />}

        {order && (
          <>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold">{order.patient_name}</h1>
                  <span className={cn("rounded-full px-3 py-1 text-sm font-medium", STATUS_BADGES[order.status] || "")}>
                    {order.status.replace(/_/g, " ")}
                  </span>
                  <span className={cn("inline-flex shrink-0 items-center rounded-full border px-2 py-0.5 text-xs font-semibold uppercase", PRIORITY_STYLES[order.priority] || PRIORITY_STYLES.routine)}>
                    {order.priority}
                  </span>
                </div>
                <div className="flex gap-4 text-sm text-muted-foreground mt-1">
                  <span>Ordered: {new Date(order.ordered_at).toLocaleDateString()}</span>
                  {order.ordered_by_name && <span>By {order.ordered_by_name}</span>}
                </div>
              </div>
            </div>

            <Card>
              <CardHeader><CardTitle className="text-lg">Ordered Tests</CardTitle></CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {order.test_names.map((name, i) => (
                    <span key={i} className="rounded-full bg-muted px-3 py-1 text-sm">{name}</span>
                  ))}
                </div>
              </CardContent>
            </Card>

            {order.notes && (
              <Card>
                <CardHeader><CardTitle className="text-lg">Notes</CardTitle></CardHeader>
                <CardContent className="text-sm whitespace-pre-wrap">{order.notes}</CardContent>
              </Card>
            )}

            <SpecimenList orderId={order.id} />

            <Card>
              <CardHeader><CardTitle className="text-lg">Results</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {order.results.length === 0 && (
                  <p className="text-sm text-muted-foreground">No results entered yet.</p>
                )}
                {order.results.map((r) => (
                  <div key={r.id} className="rounded-lg border p-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{r.test_name}</span>
                          <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-medium", r.status === "approved" ? "bg-green-100 text-green-700" : r.status === "reviewed" ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-700")}>
                            {r.status}
                          </span>
                        </div>
                        <p className="text-sm mt-1">
                          {r.value != null ? `${r.value} ${r.unit || ""}` : r.value_text || "—"}
                          {r.reference_range && <span className="text-muted-foreground ml-2">(Ref: {r.reference_range})</span>}
                        </p>
                        {r.approved_by_name && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Approved by {r.approved_by_name}{r.approved_at ? ` on ${new Date(r.approved_at).toLocaleDateString()}` : ""}
                          </p>
                        )}
                        {r.notes && <p className="text-xs text-muted-foreground mt-1">{r.notes}</p>}
                      </div>
                      {r.status === "pending" && (
                        <Button size="sm" variant="outline" disabled={busy === r.id} onClick={() => handleApprove(r.id, "review")}>
                          {busy === r.id ? "..." : "Review"}
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <ResultEntryForm orderId={order.id} onSubmit={handleResultSubmit} />
          </>
        )}
      </div>
    </DashboardShell>
  );
}
