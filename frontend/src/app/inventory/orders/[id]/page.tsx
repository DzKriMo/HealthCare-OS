"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonCard } from "@/components/ui/skeleton";
import { api, ApiRequestError } from "@/lib/api/client";
import { cn } from "@/lib/utils";

interface LineItem {
  id: number; item: string; item_name: string;
  quantity: number; unit_cost: string; line_total: string;
}

interface PurchaseOrderDetail {
  id: string; supplier: string; supplier_name: string;
  po_number: string; status: string; notes: string;
  line_items: LineItem[]; total_cost: string;
  ordered_by_name: string; ordered_date: string;
  expected_date: string; received_date: string;
}

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  sent: "bg-blue-100 text-blue-700",
  partially_received: "bg-amber-100 text-amber-700",
  received: "bg-green-100 text-green-700",
  cancelled: "bg-red-100 text-red-700",
};

export default function PurchaseOrderDetailPage() {
  const router = useRouter(); const params = useParams();
  const orderId = params.id as string;
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [order, setOrder] = useState<PurchaseOrderDetail | null>(null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);

  const [showReceive, setShowReceive] = useState(false);
  const [receipts, setReceipts] = useState<Record<string, string>>({});
  const [recvBusy, setRecvBusy] = useState(false);
  const [recvError, setRecvError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => { if (!authLoading && !isAuthenticated) router.push("/login"); }, [authLoading, isAuthenticated, router]);
  useEffect(() => { if (isAuthenticated && orderId) load(); }, [isAuthenticated, orderId]);

  const load = async () => {
    setLoading(true); setLoadError("");
    try {
      const d = await api.get<PurchaseOrderDetail>(`/inventory/orders/${orderId}/`);
      setOrder(d);
      const initial: Record<string, string> = {};
      d.line_items.forEach((li) => { initial[li.item] = String(li.quantity); });
      setReceipts(initial);
    } catch { setLoadError("Failed to load order."); }
    finally { setLoading(false); }
  };

  const canReceive = order && ["sent", "partially_received"].includes(order.status);

  const handleReceive = async (e: React.FormEvent) => {
    e.preventDefault(); setRecvBusy(true); setRecvError("");
    if (!order) return;
    const item_receipts = Object.entries(receipts)
      .filter(([, qty]) => Number(qty) > 0)
      .map(([item_id, quantity]) => ({ item_id, quantity: Number(quantity) }));
    if (item_receipts.length === 0) { setRecvError("Enter at least one receipt."); setRecvBusy(false); return; }
    try {
      await api.post(`/inventory/orders/${orderId}/receive/`, { item_receipts });
      setShowReceive(false); await load();
    } catch (err) { setRecvError(err instanceof ApiRequestError ? err.message : "Failed."); }
    finally { setRecvBusy(false); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  const money = (v: string | number) => Number(v || 0).toFixed(2);
  const selectCls = "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-4xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/inventory/orders")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
        </Button>

        {loadError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{loadError} <Button variant="link" size="sm" onClick={load}>Retry</Button></div>}
        {loading && !order && <SkeletonCard />}

        {order && (
          <>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold">{order.po_number}</h1>
                  <span className={cn("rounded-full px-3 py-1 text-sm font-medium", STATUS_STYLES[order.status] || "bg-gray-100 text-gray-700")}>
                    {order.status.replace(/_/g, " ")}
                  </span>
                </div>
                <p className="text-muted-foreground">{order.supplier_name}</p>
              </div>
              {canReceive && (
                <Button onClick={() => setShowReceive((v) => !v)}>
                  {showReceive ? "Cancel" : "Receive"}
                </Button>
              )}
            </div>

            {recvError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{recvError}</div>}

            <Card>
              <CardHeader><CardTitle className="text-lg">Order Details</CardTitle></CardHeader>
              <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-3 text-sm">
                <div><span className="text-muted-foreground">Supplier</span><p>{order.supplier_name}</p></div>
                <div><span className="text-muted-foreground">Total cost</span><p className="font-semibold">${money(order.total_cost)}</p></div>
                <div><span className="text-muted-foreground">Ordered by</span><p>{order.ordered_by_name || "—"}</p></div>
                <div><span className="text-muted-foreground">Ordered date</span><p>{order.ordered_date ? new Date(order.ordered_date).toLocaleDateString() : "—"}</p></div>
                <div><span className="text-muted-foreground">Expected date</span><p>{order.expected_date ? new Date(order.expected_date).toLocaleDateString() : "—"}</p></div>
                <div><span className="text-muted-foreground">Received date</span><p>{order.received_date ? new Date(order.received_date).toLocaleDateString() : "—"}</p></div>
                {order.notes && <div className="sm:col-span-3"><span className="text-muted-foreground">Notes</span><p className="whitespace-pre-wrap">{order.notes}</p></div>}
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="text-lg">Line Items</CardTitle></CardHeader>
              <CardContent className="p-0">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-xs uppercase text-muted-foreground">
                      <th className="pb-2 pl-4 pr-4 font-medium">Item</th>
                      <th className="pb-2 pr-4 font-medium">Qty</th>
                      <th className="pb-2 pr-4 font-medium">Unit Cost</th>
                      <th className="pb-2 pr-4 font-medium">Line Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {order.line_items.map((li) => (
                      <tr key={li.id} className="border-b last:border-0">
                        <td className="py-2 pl-4 pr-4">{li.item_name}</td>
                        <td className="py-2 pr-4">{li.quantity}</td>
                        <td className="py-2 pr-4">${money(li.unit_cost)}</td>
                        <td className="py-2 pr-4 font-medium">${money(li.line_total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>

            {showReceive && canReceive && (
              <Card>
                <CardHeader><CardTitle className="text-lg">Receive Items</CardTitle></CardHeader>
                <CardContent>
                  <form onSubmit={handleReceive} className="space-y-4">
                    {order.line_items.map((li) => (
                      <div key={li.id} className="flex items-end gap-3 rounded-md border p-3">
                        <div className="flex-1">
                          <Label className="text-xs">{li.item_name}</Label>
                          <p className="text-xs text-muted-foreground">Ordered: {li.quantity}</p>
                        </div>
                        <div className="w-32 space-y-1.5">
                          <Label htmlFor={`rcv_${li.id}`} className="text-xs">Received</Label>
                          <Input
                            id={`rcv_${li.id}`}
                            type="number"
                            min={0}
                            max={li.quantity}
                            value={receipts[li.item] ?? ""}
                            onChange={(e) => setReceipts((r) => ({ ...r, [li.item]: e.target.value }))}
                          />
                        </div>
                      </div>
                    ))}
                    <div className="flex gap-2">
                      <Button type="submit" disabled={recvBusy}>{recvBusy ? "Recording..." : "Confirm Receipt"}</Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </DashboardShell>
  );
}
