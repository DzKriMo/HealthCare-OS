"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";

interface InventoryItem {
  id: string;
  name: string;
}

interface LineItem {
  item_id: string;
  item_name: string;
  quantity: number;
  unit_cost: string;
}

interface PurchaseOrderFormData {
  supplier: string;
  line_items: LineItem[];
  notes: string;
  expected_date: string;
}

interface PurchaseOrderFormProps {
  onSubmit: (data: PurchaseOrderFormData) => Promise<void>;
  loading: boolean;
}

export function PurchaseOrderForm({ onSubmit, loading }: PurchaseOrderFormProps) {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [suppliers, setSuppliers] = useState<{ id: string; name: string }[]>([]);
  const [form, setForm] = useState<PurchaseOrderFormData>({
    supplier: "",
    line_items: [{ item_id: "", item_name: "", quantity: 1, unit_cost: "" }],
    notes: "",
    expected_date: "",
  });

  useEffect(() => {
    const load = async () => {
      try {
        const [itemsData, suppliersData] = await Promise.all([
          api.get<InventoryItem[]>("/inventory/items/"),
          api.get<{ id: string; name: string }[]>("/inventory/suppliers/"),
        ]);
        setItems(itemsData);
        setSuppliers(suppliersData);
      } catch { }
    };
    load();
  }, []);

  const set = (k: keyof PurchaseOrderFormData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>,
  ) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const setLineItem = (index: number, k: keyof LineItem) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    setForm((f) => {
      const line_items = f.line_items.map((li, i) => {
        if (i !== index) return li;
        const val = e.target.value;
        if (k === "item_id") {
          const selected = items.find((it) => it.id === val);
          return { ...li, item_id: val, item_name: selected?.name || "" };
        }
        if (k === "quantity") return { ...li, quantity: Number(val) };
        return { ...li, [k]: val };
      });
      return { ...f, line_items };
    });
  };

  const addLineItem = () => {
    setForm((f) => ({
      ...f,
      line_items: [...f.line_items, { item_id: "", item_name: "", quantity: 1, unit_cost: "" }],
    }));
  };

  const removeLineItem = (index: number) => {
    setForm((f) => ({
      ...f,
      line_items: f.line_items.filter((_, i) => i !== index),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(form);
  };

  const selectCls = "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Purchase Order</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="supplier">Supplier *</Label>
            <select id="supplier" value={form.supplier} onChange={set("supplier")} required className={selectCls}>
              <option value="">Select supplier...</option>
              {suppliers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="expected_date">Expected date</Label>
            <Input id="expected_date" type="date" value={form.expected_date} onChange={set("expected_date")} />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="po_notes">Notes</Label>
            <textarea
              id="po_notes"
              value={form.notes}
              onChange={set("notes")}
              className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle>Line Items</CardTitle>
          <Button type="button" size="sm" variant="outline" onClick={addLineItem}>
            <Icons.plus className="mr-1 h-4 w-4" />
            Add Item
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {form.line_items.map((li, index) => (
            <div key={index} className="flex items-end gap-3 rounded-md border p-3">
              <div className="flex-1 space-y-1.5">
                <Label htmlFor={`li_item_${index}`}>Item *</Label>
                <select
                  id={`li_item_${index}`}
                  value={li.item_id}
                  onChange={setLineItem(index, "item_id")}
                  required
                  className={selectCls}
                >
                  <option value="">Select item...</option>
                  {items.map((it) => <option key={it.id} value={it.id}>{it.name}</option>)}
                </select>
              </div>
              <div className="w-24 space-y-1.5">
                <Label htmlFor={`li_qty_${index}`}>Qty *</Label>
                <Input id={`li_qty_${index}`} type="number" min={1} value={li.quantity || ""} onChange={setLineItem(index, "quantity")} required />
              </div>
              <div className="w-32 space-y-1.5">
                <Label htmlFor={`li_cost_${index}`}>Unit cost ($)</Label>
                <Input id={`li_cost_${index}`} type="number" min={0} step="0.01" value={li.unit_cost} onChange={setLineItem(index, "unit_cost")} />
              </div>
              {form.line_items.length > 1 && (
                <Button type="button" variant="ghost" size="icon" className="mb-0.5 shrink-0" onClick={() => removeLineItem(index)}>
                  <Icons.x className="h-4 w-4" />
                </Button>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Button type="submit" disabled={loading}>
          {loading ? "Creating..." : "Create Purchase Order"}
        </Button>
      </div>
    </form>
  );
}
