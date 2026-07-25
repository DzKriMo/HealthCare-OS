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
import { ItemForm } from "@/components/inventory/item-form";
import { StockMovementList } from "@/components/inventory/stock-movement-list";
import { BatchList } from "@/components/inventory/batch-list";
import { api, ApiRequestError } from "@/lib/api/client";
import { cn } from "@/lib/utils";
import type { InventoryItem } from "@/components/inventory/item-card";
import type { Supplier } from "@/components/inventory/item-form";

const CATEGORY_STYLES: Record<string, string> = {
  medicine: "bg-red-100 text-red-700",
  supply: "bg-blue-100 text-blue-700",
  equipment: "bg-purple-100 text-purple-700",
  consumable: "bg-amber-100 text-amber-700",
  other: "bg-gray-100 text-gray-700",
};

export default function ItemDetailPage() {
  const router = useRouter(); const params = useParams();
  const itemId = params.id as string;
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [item, setItem] = useState<InventoryItem | null>(null);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");

  const [adjType, setAdjType] = useState("adjustment");
  const [adjQty, setAdjQty] = useState("");
  const [adjReason, setAdjReason] = useState("");
  const [adjBusy, setAdjBusy] = useState(false);
  const [adjError, setAdjError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => { if (!authLoading && !isAuthenticated) router.push("/login"); }, [authLoading, isAuthenticated, router]);
  useEffect(() => { if (isAuthenticated && itemId) load(); }, [isAuthenticated, itemId]);

  const load = async () => {
    setLoading(true); setLoadError("");
    try {
      const [d, s] = await Promise.all([
        api.get<InventoryItem>(`/inventory/items/${itemId}/`),
        api.get<Supplier[]>("/inventory/suppliers/"),
      ]);
      setItem(d); setSuppliers(s);
    } catch { setLoadError("Failed to load item."); }
    finally { setLoading(false); }
  };

  const handleAdjust = async (e: React.FormEvent) => {
    e.preventDefault(); setAdjBusy(true); setAdjError("");
    const qty = Number(adjQty);
    if (!qty || qty === 0) { setAdjError("Enter a non-zero quantity."); setAdjBusy(false); return; }
    try {
      await api.post("/inventory/stock/adjust/", {
        item_id: itemId, quantity: qty, movement_type: adjType, reason: adjReason,
      });
      setAdjQty(""); setAdjReason(""); await load();
    } catch (err) { setAdjError(err instanceof ApiRequestError ? err.message : "Failed."); }
    finally { setAdjBusy(false); }
  };

  const handleSave = async (data: Parameters<typeof api.post>[1]) => {
    setSaving(true); setSaveError("");
    try {
      await api.put(`/inventory/items/${itemId}/`, data);
      setEditing(false); await load();
    } catch (err) { setSaveError(err instanceof ApiRequestError ? err.message : "Failed to update."); }
    finally { setSaving(false); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  const selectCls = "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-4xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/inventory")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
        </Button>

        {loadError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{loadError} <Button variant="link" size="sm" onClick={load}>Retry</Button></div>}
        {loading && !item && <SkeletonCard />}

        {item && (
          <>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold">{item.name}</h1>
                  <span className={cn("rounded-full px-3 py-1 text-sm font-medium", CATEGORY_STYLES[item.category] || CATEGORY_STYLES.other)}>
                    {item.category}
                  </span>
                  {item.requires_refrigeration && <span className="text-sm text-blue-600">❄ Refrigerated</span>}
                </div>
                <div className="flex gap-4 text-sm mt-1">
                  <span className={cn("font-semibold", item.is_low_stock && "text-destructive")}>
                    On hand: {item.quantity_on_hand} {item.unit}
                  </span>
                  {item.sku && <span className="text-muted-foreground">SKU: {item.sku}</span>}
                </div>
              </div>
              <Button variant="outline" onClick={() => setEditing((v) => !v)}>
                <Icons.settings className="mr-2 h-4 w-4" /> {editing ? "Cancel" : "Edit"}
              </Button>
            </div>

            {saveError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{saveError}</div>}

            {editing ? (
              <ItemForm initialValues={item} suppliers={suppliers} onSubmit={handleSave} loading={saving} />
            ) : (
              <>
                <Card>
                  <CardHeader><CardTitle className="text-lg">Details</CardTitle></CardHeader>
                  <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-3 text-sm">
                    <div><span className="text-muted-foreground">Supplier</span><p>{item.supplier_name || "—"}</p></div>
                    <div><span className="text-muted-foreground">SKU</span><p>{item.sku || "—"}</p></div>
                    <div><span className="text-muted-foreground">Barcode</span><p>{item.barcode || "—"}</p></div>
                    <div><span className="text-muted-foreground">Unit cost</span><p>{item.unit_cost ? `$${Number(item.unit_cost).toFixed(2)}` : "—"}</p></div>
                    <div><span className="text-muted-foreground">Unit price</span><p>{item.unit_price ? `$${Number(item.unit_price).toFixed(2)}` : "—"}</p></div>
                    <div><span className="text-muted-foreground">Reorder point</span><p>{item.reorder_point}</p></div>
                    <div><span className="text-muted-foreground">Reorder qty</span><p>{item.reorder_quantity}</p></div>
                    <div><span className="text-muted-foreground">Batch tracking</span><p>{item.requires_batch_tracking ? "Yes" : "No"}</p></div>
                    <div><span className="text-muted-foreground">Refrigeration</span><p>{item.requires_refrigeration ? "Yes" : "No"}</p></div>
                    {item.notes && <div className="sm:col-span-3"><span className="text-muted-foreground">Notes</span><p className="whitespace-pre-wrap">{item.notes}</p></div>}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader><CardTitle className="text-lg">Stock Adjustment</CardTitle></CardHeader>
                  <CardContent>
                    {adjError && <div className="mb-3 rounded-md bg-destructive/10 p-2 text-sm text-destructive">{adjError}</div>}
                    <form onSubmit={handleAdjust} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                      <div className="space-y-1.5">
                        <Label htmlFor="adj_type">Type</Label>
                        <select id="adj_type" value={adjType} onChange={(e) => setAdjType(e.target.value)} className={selectCls}>
                          <option value="adjustment">Adjustment</option>
                          <option value="waste">Waste</option>
                          <option value="return">Return</option>
                        </select>
                      </div>
                      <div className="space-y-1.5">
                        <Label htmlFor="adj_qty">Quantity</Label>
                        <Input id="adj_qty" type="number" value={adjQty} onChange={(e) => setAdjQty(e.target.value)} placeholder="e.g. -5 or +10" />
                      </div>
                      <div className="space-y-1.5">
                        <Label htmlFor="adj_reason">Reason</Label>
                        <textarea
                          id="adj_reason"
                          value={adjReason}
                          onChange={(e) => setAdjReason(e.target.value)}
                          className="flex min-h-[40px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                        />
                      </div>
                      <div className="sm:col-span-3">
                        <Button type="submit" disabled={adjBusy}>{adjBusy ? "Saving..." : "Apply Adjustment"}</Button>
                      </div>
                    </form>
                  </CardContent>
                </Card>

                <StockMovementList itemId={item.id} />

                {item.requires_batch_tracking && <BatchList itemId={item.id} />}
              </>
            )}
          </>
        )}
      </div>
    </DashboardShell>
  );
}
