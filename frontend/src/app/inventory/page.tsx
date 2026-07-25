"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonTable } from "@/components/ui/skeleton";
import { ItemCard } from "@/components/inventory/item-card";
import { api } from "@/lib/api/client";
import type { InventoryItem } from "@/components/inventory/item-card";

interface DashboardStats {
  low_stock_count: number;
  expiring_batches: number;
  pending_pos: number;
  total_stock_value: number;
}

const CATEGORIES = ["", "medicine", "supply", "equipment", "consumable", "other"];

export default function InventoryPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [lowStockOnly, setLowStockOnly] = useState(false);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) { loadStats(); loadItems(); }
  }, [isAuthenticated, category, lowStockOnly]);

  const loadStats = async () => {
    try { setStats(await api.get<DashboardStats>("/inventory/dashboard/")); } catch { }
  };

  const loadItems = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (category) params.set("category", category);
      if (lowStockOnly) params.set("low_stock", "true");
      const q = params.toString();
      const data = await api.get<{ results: InventoryItem[] }>(`/inventory/items/${q ? `?${q}` : ""}`);
      setItems(data.results);
    } catch { setPageError("Failed to load inventory."); }
    finally { setLoading(false); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  const money = (v: string | number) => Number(v || 0).toFixed(2);
  const selectCls = "flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm";

  const filtered = search
    ? items.filter((i) => i.name.toLowerCase().includes(search.toLowerCase()) || i.sku?.toLowerCase().includes(search.toLowerCase()))
    : items;

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Inventory</h1>
            <p className="text-muted-foreground">{items.length} items</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/inventory/suppliers")}>
              <Icons.users className="mr-2 h-4 w-4" /> Suppliers
            </Button>
            <Button variant="outline" onClick={() => router.push("/inventory/orders")}>
              <Icons.fileText className="mr-2 h-4 w-4" /> Purchase Orders
            </Button>
            <Button onClick={() => router.push("/inventory/items/new")}>
              <Icons.plus className="mr-2 h-4 w-4" /> New Item
            </Button>
          </div>
        </div>

        {stats && (
          <div className="grid gap-4 sm:grid-cols-4">
            <Card><CardContent className="p-4">
              <p className="text-sm text-muted-foreground">Low Stock</p>
              <p className="text-2xl font-bold text-destructive">{stats.low_stock_count}</p>
            </CardContent></Card>
            <Card><CardContent className="p-4">
              <p className="text-sm text-muted-foreground">Expiring Soon</p>
              <p className="text-2xl font-bold text-amber-600">{stats.expiring_batches}</p>
            </CardContent></Card>
            <Card><CardContent className="p-4">
              <p className="text-sm text-muted-foreground">Pending POs</p>
              <p className="text-2xl font-bold">{stats.pending_pos}</p>
            </CardContent></Card>
            <Card><CardContent className="p-4">
              <p className="text-sm text-muted-foreground">Stock Value</p>
              <p className="text-2xl font-bold">${money(stats.total_stock_value)}</p>
            </CardContent></Card>
          </div>
        )}

        {pageError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>}

        <div className="flex gap-2 flex-wrap items-center">
          <select value={category} onChange={(e) => setCategory(e.target.value)} className={selectCls}>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c || "All categories"}</option>)}
          </select>
          <Input placeholder="Search items..." value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-xs" />
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" checked={lowStockOnly} onChange={(e) => setLowStockOnly(e.target.checked)} className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary" />
            Low stock only
          </label>
        </div>

        {loading ? <SkeletonTable rows={8} /> : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((item) => (
              <ItemCard key={item.id} item={item} onClick={() => router.push(`/inventory/items/${item.id}`)} />
            ))}
            {filtered.length === 0 && (
              <div className="col-span-full rounded-lg border border-dashed p-12 text-center text-muted-foreground">
                <Icons.plus className="mx-auto mb-3 h-8 w-8" />
                <p>No items found.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
