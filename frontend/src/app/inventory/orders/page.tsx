"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Icons } from "@/components/icons";
import { SkeletonTable } from "@/components/ui/skeleton";
import { PurchaseOrderCard } from "@/components/inventory/purchase-order-card";
import { api } from "@/lib/api/client";
import type { PurchaseOrder } from "@/components/inventory/purchase-order-card";

const STATUSES = ["", "draft", "sent", "partially_received", "received", "cancelled"];

export default function PurchaseOrdersPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) load();
  }, [isAuthenticated, statusFilter]);

  const load = async () => {
    setLoading(true);
    try {
      const q = statusFilter ? `?status=${statusFilter}` : "";
      const data = await api.get<{ results: PurchaseOrder[] }>(`/inventory/orders/${q}`);
      setOrders(data.results);
    } catch { setPageError("Failed to load orders."); }
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
            <h1 className="text-3xl font-bold tracking-tight">Purchase Orders</h1>
            <p className="text-muted-foreground">{orders.length} orders</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/inventory")}>
              <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back to Inventory
            </Button>
            <Button onClick={() => router.push("/inventory/orders/new")}>
              <Icons.plus className="mr-2 h-4 w-4" /> New PO
            </Button>
          </div>
        </div>

        {pageError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>}

        <div className="flex gap-2 flex-wrap">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className={selectCls}>
            {STATUSES.map((s) => <option key={s} value={s}>{s || "All statuses"}</option>)}
          </select>
        </div>

        {loading ? <SkeletonTable rows={8} /> : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {orders.map((order) => (
              <PurchaseOrderCard key={order.id} order={order} onClick={() => router.push(`/inventory/orders/${order.id}`)} />
            ))}
            {orders.length === 0 && (
              <div className="col-span-full rounded-lg border border-dashed p-12 text-center text-muted-foreground">
                <Icons.fileText className="mx-auto mb-3 h-8 w-8" />
                <p>No purchase orders found.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
