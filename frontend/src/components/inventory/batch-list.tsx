"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api/client";

interface Batch {
  id: string;
  item: string;
  item_name: string;
  lot_number: string;
  quantity: number;
  manufacturing_date: string;
  expiration_date: string;
  received_date: string;
  is_expired: boolean;
  days_until_expiry: number;
  is_expiring_soon: boolean;
}

interface BatchListProps {
  itemId: string;
}

export function BatchList({ itemId }: BatchListProps) {
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    lot_number: "",
    quantity: 0,
    manufacturing_date: "",
    expiration_date: "",
  });

  useEffect(() => {
    if (!itemId) return;
    const load = async () => {
      try {
        setBatches(await api.get<Batch[]>(`/inventory/batches/?item=${itemId}`));
      } catch { }
      setLoading(false);
    };
    load();
  }, [itemId]);

  const set = (k: keyof typeof form) => (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const setNum = (k: keyof typeof form) => (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => setForm((f) => ({ ...f, [k]: Number(e.target.value) }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const created = await api.post<Batch>("/inventory/batches/", { ...form, item: itemId });
      setBatches((prev) => [...prev, created]);
      setForm({ lot_number: "", quantity: 0, manufacturing_date: "", expiration_date: "" });
      setShowForm(false);
    } catch { }
    setSubmitting(false);
  };

  if (!itemId) {
    return <div className="text-sm text-muted-foreground">Select an item to view batches.</div>;
  }

  if (loading) {
    return <div className="text-sm text-muted-foreground">Loading batches...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Batches ({batches.length})</h3>
        <Button size="sm" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancel" : "Add Batch"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>New Batch</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="lot_number">Lot number *</Label>
                <Input id="lot_number" value={form.lot_number} onChange={set("lot_number")} required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="b_qty">Quantity *</Label>
                <Input id="b_qty" type="number" min={0} value={form.quantity || ""} onChange={setNum("quantity")} required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="manufacturing_date">Manufacturing date</Label>
                <Input id="manufacturing_date" type="date" value={form.manufacturing_date} onChange={set("manufacturing_date")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="expiration_date">Expiration date *</Label>
                <Input id="expiration_date" type="date" value={form.expiration_date} onChange={set("expiration_date")} required />
              </div>
              <div className="sm:col-span-2">
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Saving..." : "Save Batch"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="space-y-2">
        {batches.map((b) => {
          const isExpiredOrSoon = b.is_expired || b.is_expiring_soon;
          return (
            <Card key={b.id}>
              <CardContent className="p-3">
                <div className="flex items-start justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{b.lot_number}</span>
                      {b.is_expired && (
                        <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-medium text-red-700">expired</span>
                      )}
                      {b.is_expiring_soon && !b.is_expired && (
                        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-700">expiring soon</span>
                      )}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-sm">
                      <span className={cn("font-semibold", isExpiredOrSoon && "text-destructive")}>
                        Qty: {b.quantity}
                      </span>
                      <span className={cn(isExpiredOrSoon && "text-destructive")}>
                        Exp: {b.expiration_date ? new Date(b.expiration_date).toLocaleDateString() : "—"}
                      </span>
                      {b.manufacturing_date && (
                        <span className="text-muted-foreground">Mfg: {new Date(b.manufacturing_date).toLocaleDateString()}</span>
                      )}
                      {b.received_date && (
                        <span className="text-muted-foreground">Rcvd: {new Date(b.received_date).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
        {batches.length === 0 && (
          <p className="text-sm text-muted-foreground">No batches found for this item.</p>
        )}
      </div>
    </div>
  );
}
