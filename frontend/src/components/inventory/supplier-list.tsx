"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";

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

interface SupplierFormData {
  name: string;
  contact_person: string;
  email: string;
  phone: string;
  address: string;
  lead_time_days: number;
  payment_terms: string;
  notes: string;
}

export function SupplierList() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState<SupplierFormData>({
    name: "",
    contact_person: "",
    email: "",
    phone: "",
    address: "",
    lead_time_days: 0,
    payment_terms: "",
    notes: "",
  });

  useEffect(() => {
    const load = async () => {
      try {
        setSuppliers(await api.get<Supplier[]>("/inventory/suppliers/"));
      } catch { }
      setLoading(false);
    };
    load();
  }, []);

  const set = (k: keyof SupplierFormData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const setNum = (k: keyof SupplierFormData) => (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => setForm((f) => ({ ...f, [k]: Number(e.target.value) }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const created = await api.post<Supplier>("/inventory/suppliers/", form);
      setSuppliers((prev) => [...prev, created]);
      setForm({ name: "", contact_person: "", email: "", phone: "", address: "", lead_time_days: 0, payment_terms: "", notes: "" });
      setShowForm(false);
    } catch { }
    setSubmitting(false);
  };

  const selectCls = "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

  if (loading) {
    return <div className="text-sm text-muted-foreground">Loading suppliers...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Suppliers ({suppliers.length})</h3>
        <Button size="sm" onClick={() => setShowForm((v) => !v)}>
          <Icons.plus className="mr-1 h-4 w-4" />
          {showForm ? "Cancel" : "Add"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>New Supplier</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="s_name">Name *</Label>
                  <Input id="s_name" value={form.name} onChange={set("name")} required />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="s_contact">Contact person</Label>
                  <Input id="s_contact" value={form.contact_person} onChange={set("contact_person")} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="s_email">Email</Label>
                  <Input id="s_email" type="email" value={form.email} onChange={set("email")} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="s_phone">Phone</Label>
                  <Input id="s_phone" value={form.phone} onChange={set("phone")} />
                </div>
                <div className="space-y-1.5 sm:col-span-2">
                  <Label htmlFor="s_address">Address</Label>
                  <Input id="s_address" value={form.address} onChange={set("address")} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="s_lead_time">Lead time (days)</Label>
                  <Input id="s_lead_time" type="number" min={0} value={form.lead_time_days || ""} onChange={setNum("lead_time_days")} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="s_payment_terms">Payment terms</Label>
                  <select id="s_payment_terms" value={form.payment_terms} onChange={set("payment_terms")} className={selectCls}>
                    <option value="">—</option>
                    <option value="net_15">Net 15</option>
                    <option value="net_30">Net 30</option>
                    <option value="net_60">Net 60</option>
                    <option value="cod">COD</option>
                    <option value="prepaid">Prepaid</option>
                  </select>
                </div>
                <div className="space-y-1.5 sm:col-span-2">
                  <Label htmlFor="s_notes">Notes</Label>
                  <textarea
                    id="s_notes"
                    value={form.notes}
                    onChange={set("notes")}
                    className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  />
                </div>
              </div>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Saving..." : "Save Supplier"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="space-y-2">
        {suppliers.map((s) => (
          <Card key={s.id}>
            <CardContent className="flex items-center justify-between p-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{s.name}</span>
                  {!s.is_active && (
                    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-600">inactive</span>
                  )}
                </div>
                <div className="mt-0.5 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-muted-foreground">
                  {s.contact_person && <span>{s.contact_person}</span>}
                  {s.email && <span>{s.email}</span>}
                  {s.phone && <span>{s.phone}</span>}
                  {s.lead_time_days > 0 && <span>Lead: {s.lead_time_days}d</span>}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        {suppliers.length === 0 && (
          <p className="text-sm text-muted-foreground">No suppliers found.</p>
        )}
      </div>
    </div>
  );
}
