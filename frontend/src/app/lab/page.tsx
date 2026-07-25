"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonTable } from "@/components/ui/skeleton";
import { LabOrderCard } from "@/components/laboratory/lab-order-card";
import { api } from "@/lib/api/client";

interface DashboardStats {
  pending_results: number;
  critical_results: number;
  orders_today: number;
}

interface LabOrder {
  id: string;
  patient_name: string;
  patient_id: string;
  status: string;
  priority: string;
  test_names: string[];
  ordered_at: string;
  ordered_by_name?: string;
  encounter?: string;
  notes?: string;
}

const STATUSES = ["", "draft", "ordered", "collected", "received", "in_progress", "completed", "reviewed", "cancelled"];

export default function LabPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [stats, setStats] = useState<DashboardStats>({ pending_results: 0, critical_results: 0, orders_today: 0 });
  const [orders, setOrders] = useState<LabOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => { if (isAuthenticated) load(); }, [isAuthenticated, statusFilter]);

  const load = async () => {
    setLoading(true);
    try {
      const [dashData, ordersData] = await Promise.all([
        api.get<DashboardStats>("/lab/dashboard/"),
        api.get<{ results: LabOrder[] }>(`/lab/orders/${statusFilter ? `?status=${statusFilter}` : ""}`),
      ]);
      setStats(dashData);
      setOrders(ordersData.results);
    } catch { setPageError("Failed to load lab data."); }
    finally { setLoading(false); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  const selectCls = "flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm";

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Laboratory</h1>
            <p className="text-muted-foreground">{orders.length} orders</p>
          </div>
          <Button onClick={() => router.push("/lab/orders/new")}>
            <Icons.plus className="mr-2 h-4 w-4" /> New Order
          </Button>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="p-4">
              <p className="text-sm text-muted-foreground">Pending Results</p>
              <p className="text-2xl font-bold">{stats.pending_results}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-sm text-muted-foreground">Critical Results</p>
              <p className={`text-2xl font-bold ${stats.critical_results > 0 ? "text-destructive" : ""}`}>{stats.critical_results}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-sm text-muted-foreground">Orders Today</p>
              <p className="text-2xl font-bold">{stats.orders_today}</p>
            </CardContent>
          </Card>
        </div>

        {pageError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>}

        <div className="flex gap-2 flex-wrap">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className={selectCls}>
            {STATUSES.map((s) => <option key={s} value={s}>{s || "All statuses"}</option>)}
          </select>
        </div>

        {loading ? <SkeletonTable rows={8} /> : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {orders.map((o) => (
              <LabOrderCard key={o.id} order={o} onClick={() => router.push(`/lab/orders/${o.id}`)} />
            ))}
            {orders.length === 0 && (
              <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground sm:col-span-2 lg:col-span-3">
                <Icons.fileText className="mx-auto mb-3 h-8 w-8" />
                <p>No lab orders found.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
