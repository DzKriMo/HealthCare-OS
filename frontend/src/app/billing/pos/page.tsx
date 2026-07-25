"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api, ApiRequestError } from "@/lib/api/client";

interface CatalogItem { id: string; name: string; price: string; tax_rate: string; category: string; }
interface CartItem { billing_item_id: string; description: string; quantity: number; unit_price: string; tax_rate: string; }

const METHODS = ["cash", "card", "transfer", "insurance", "other"];

export default function POSPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [patients, setPatients] = useState<{ id: string; label: string }[]>([]);
  const [patient, setPatient] = useState("");
  const [cart, setCart] = useState<CartItem[]>([]);
  const [paymentMethod, setPaymentMethod] = useState("cash");
  const [paymentRef, setPaymentRef] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => { if (!authLoading && !isAuthenticated) router.push("/login"); }, [authLoading, isAuthenticated, router]);
  useEffect(() => { if (isAuthenticated) { loadCatalog(); loadPatients(); } }, [isAuthenticated]);

  const loadCatalog = async () => {
    try { const d = await api.get<{ results: CatalogItem[] }>("/billing/items/"); setCatalog(d.results); } catch { }
  };
  const loadPatients = async () => {
    try { const d = await api.get<{ results: { id: string; full_name: string }[] }>("/patients/"); setPatients(d.results.map((p) => ({ id: p.id, label: p.full_name }))); } catch { }
  };

  const addToCart = (item: CatalogItem) => {
    setCart((prev) => {
      const existing = prev.find((c) => c.billing_item_id === item.id);
      if (existing) return prev.map((c) => c.billing_item_id === item.id ? { ...c, quantity: c.quantity + 1 } : c);
      return [...prev, { billing_item_id: item.id, description: item.name, quantity: 1, unit_price: item.price, tax_rate: item.tax_rate }];
    });
  };

  const updateQty = (id: string, qty: number) => {
    if (qty <= 0) { setCart((prev) => prev.filter((c) => c.billing_item_id !== id)); return; }
    setCart((prev) => prev.map((c) => c.billing_item_id === id ? { ...c, quantity: qty } : c));
  };

  const total = cart.reduce((sum, c) => {
    const price = Number(c.unit_price) || 0; const qty = c.quantity || 0;
    const tax = (Number(c.tax_rate) || 0) / 100;
    return sum + price * qty * (1 + tax);
  }, 0);

  const handleCheckout = async () => {
    if (cart.length === 0) { setError("Cart is empty."); return; }
    setSubmitting(true); setError(""); setSuccess("");
    try {
      const result = await api.post<{ invoice: { id: string } }>("/billing/pos/checkout/", {
        patient_id: patient || null,
        line_items: cart.map((c) => ({ billing_item_id: c.billing_item_id, description: c.description, quantity: c.quantity, unit_price: c.unit_price, tax_rate: c.tax_rate })),
        discount: "0", payment_method: paymentMethod, payment_reference: paymentRef,
      });
      setSuccess(`Payment processed! Invoice #${result.invoice.id.slice(0, 8)}`);
      setCart([]); setPatient(""); setPaymentRef("");
    } catch (err) { setError(err instanceof ApiRequestError ? err.message : "Checkout failed."); }
    finally { setSubmitting(false); }
  };

  if (authLoading || !user) return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;

  const filtered = catalog.filter((i) => i.name.toLowerCase().includes(searchTerm.toLowerCase()));
  const selectCls = "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-center justify-between">
          <div><h1 className="text-3xl font-bold tracking-tight">POS Checkout</h1><p className="text-muted-foreground">Quick walk-in payment.</p></div>
          <Button variant="outline" onClick={() => router.push("/billing")}><Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back</Button>
        </div>

        {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}
        {success && <div className="rounded-md bg-green-50 border border-green-200 p-3 text-sm text-green-800">{success}</div>}

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-4">
            <Card>
              <CardHeader><CardTitle>Item Catalog</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <Input placeholder="Search items..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
                <div className="max-h-80 space-y-1 overflow-y-auto">
                  {filtered.map((item) => (
                    <div key={item.id} className="flex items-center justify-between rounded-lg border p-2 hover:bg-muted/50 cursor-pointer" onClick={() => addToCart(item)}>
                      <div>
                        <div className="text-sm font-medium">{item.name}</div>
                        <div className="text-xs text-muted-foreground">{item.category} · ${Number(item.price).toFixed(2)}</div>
                      </div>
                      <Button size="sm" variant="ghost"><Icons.plus className="h-4 w-4" /></Button>
                    </div>
                  ))}
                  {filtered.length === 0 && <p className="text-sm text-muted-foreground">No items found.</p>}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            <Card>
              <CardHeader><CardTitle>Cart</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {cart.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Click items to add to cart.</p>
                ) : (
                  <>
                    {cart.map((c) => (
                      <div key={c.billing_item_id} className="flex items-center justify-between rounded-lg border p-2">
                        <div className="flex-1">
                          <div className="text-sm font-medium">{c.description}</div>
                          <div className="text-xs text-muted-foreground">${Number(c.unit_price).toFixed(2)} each</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button size="sm" variant="outline" className="h-7 w-7 p-0" onClick={() => updateQty(c.billing_item_id, c.quantity - 1)}>-</Button>
                          <span className="w-6 text-center text-sm">{c.quantity}</span>
                          <Button size="sm" variant="outline" className="h-7 w-7 p-0" onClick={() => updateQty(c.billing_item_id, c.quantity + 1)}>+</Button>
                          <span className="w-16 text-right text-sm font-medium">
                            ${(Number(c.unit_price) * c.quantity).toFixed(2)}
                          </span>
                        </div>
                      </div>
                    ))}
                    <div className="border-t pt-2 text-right">
                      <span className="text-lg font-bold">Total: ${total.toFixed(2)}</span>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Payment</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-1.5">
                  <Label>Patient (optional)</Label>
                  <select value={patient} onChange={(e) => setPatient(e.target.value)} className={selectCls}>
                    <option value="">Walk-in (no patient)</option>
                    {patients.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label>Method</Label>
                    <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)} className={selectCls}>
                      {METHODS.map((m) => <option key={m} value={m}>{m}</option>)}
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <Label>Reference</Label>
                    <Input value={paymentRef} onChange={(e) => setPaymentRef(e.target.value)} placeholder="Txn #" />
                  </div>
                </div>
                <Button className="w-full" size="lg" disabled={submitting || cart.length === 0} onClick={handleCheckout}>
                  {submitting ? "Processing..." : `Charge $${total.toFixed(2)}`}
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
