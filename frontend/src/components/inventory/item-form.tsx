"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Supplier {
  id: string;
  name: string;
  contact_person: string;
  email: string;
  phone: string;
  address: string;
  lead_time_days: number;
  payment_terms: string;
  is_active: boolean;
  notes: string;
}

interface ItemFormData {
  name: string;
  category: string;
  unit: string;
  sku: string;
  barcode: string;
  reorder_point: number;
  reorder_quantity: number;
  unit_cost: string;
  unit_price: string;
  requires_batch_tracking: boolean;
  requires_refrigeration: boolean;
  supplier: string;
  notes: string;
}

interface ItemFormProps {
  initialValues?: Partial<ItemFormData>;
  suppliers: Supplier[];
  onSubmit: (data: ItemFormData) => Promise<void>;
  loading: boolean;
}

const CATEGORIES = ["medicine", "supply", "equipment", "consumable", "other"];
const UNITS = ["each", "box", "bottle", "vial", "tablet", "capsule", "ml", "l", "g", "mg", "pair", "set", "pack", "roll"];

export function ItemForm({ initialValues = {}, suppliers, onSubmit, loading }: ItemFormProps) {
  const [form, setForm] = useState<ItemFormData>({
    name: "",
    category: "other",
    unit: "each",
    sku: "",
    barcode: "",
    reorder_point: 0,
    reorder_quantity: 0,
    unit_cost: "",
    unit_price: "",
    requires_batch_tracking: false,
    requires_refrigeration: false,
    supplier: "",
    notes: "",
    ...initialValues,
  });

  const set = (k: keyof ItemFormData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>,
  ) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const setNum = (k: keyof ItemFormData) => (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => setForm((f) => ({ ...f, [k]: Number(e.target.value) }));

  const setCheck = (k: keyof ItemFormData) => (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => setForm((f) => ({ ...f, [k]: e.target.checked }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(form);
  };

  const selectCls = "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Item Details</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="space-y-1.5">
            <Label htmlFor="name">Name *</Label>
            <Input id="name" value={form.name} onChange={set("name")} required />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="category">Category *</Label>
            <select id="category" value={form.category} onChange={set("category")} required className={selectCls}>
              {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="unit">Unit *</Label>
            <select id="unit" value={form.unit} onChange={set("unit")} required className={selectCls}>
              {UNITS.map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="sku">SKU</Label>
            <Input id="sku" value={form.sku} onChange={set("sku")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="barcode">Barcode</Label>
            <Input id="barcode" value={form.barcode} onChange={set("barcode")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="reorder_point">Reorder point *</Label>
            <Input id="reorder_point" type="number" min={0} value={form.reorder_point || ""} onChange={setNum("reorder_point")} required />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="reorder_quantity">Reorder qty</Label>
            <Input id="reorder_quantity" type="number" min={0} value={form.reorder_quantity || ""} onChange={setNum("reorder_quantity")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="unit_cost">Unit cost ($)</Label>
            <Input id="unit_cost" type="number" min={0} step="0.01" value={form.unit_cost} onChange={set("unit_cost")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="unit_price">Unit price ($)</Label>
            <Input id="unit_price" type="number" min={0} step="0.01" value={form.unit_price} onChange={set("unit_price")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="supplier">Supplier</Label>
            <select id="supplier" value={form.supplier} onChange={set("supplier")} className={selectCls}>
              <option value="">—</option>
              {suppliers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Settings</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="requires_batch_tracking"
              checked={form.requires_batch_tracking}
              onChange={setCheck("requires_batch_tracking")}
              className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <Label htmlFor="requires_batch_tracking">Requires batch/lot tracking</Label>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="requires_refrigeration"
              checked={form.requires_refrigeration}
              onChange={setCheck("requires_refrigeration")}
              className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <Label htmlFor="requires_refrigeration">Requires refrigeration</Label>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="notes">Notes</Label>
            <textarea
              id="notes"
              value={form.notes}
              onChange={set("notes")}
              className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Button type="submit" disabled={loading}>
          {loading ? "Saving..." : "Save Item"}
        </Button>
      </div>
    </form>
  );
}
