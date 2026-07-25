"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api, ApiRequestError } from "@/lib/api/client";

interface LineItem {
  description: string;
  quantity: number;
  unit_price: string;
  tax_rate: string;
}

const EMPTY_LINE: LineItem = { description: "", quantity: 1, unit_price: "0.00", tax_rate: "0" };

function NewInvoiceInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const presetPatient = searchParams.get("patient") || "";
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } =
    useAuthStore();

  const [patients, setPatients] = useState<{ id: string; label: string }[]>([]);
  const [patient, setPatient] = useState(presetPatient);
  const [lines, setLines] = useState<LineItem[]>([{ ...EMPTY_LINE }]);
  const [discount, setDiscount] = useState("0");
  const [dueDate, setDueDate] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [correlationId, setCorrelationId] = useState<string | undefined>();

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) loadPatients();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const loadPatients = async () => {
    try {
      const p = await api.get<{ results: { id: string; full_name: string }[] }>("/patients/");
      setPatients(p.results.map((x) => ({ id: x.id, label: x.full_name })));
    } catch { /* empty state */ }
  };

  const setLine = (i: number, k: keyof LineItem, v: string | number) =>
    setLines((ls) => ls.map((l, idx) => (idx === i ? { ...l, [k]: v } : l)));
  const addLine = () => setLines((ls) => [...ls, { ...EMPTY_LINE }]);
  const removeLine = (i: number) => setLines((ls) => ls.filter((_, idx) => idx !== i));

  const computed = lines.reduce(
    (acc, l) => {
      const qty = Number(l.quantity) || 0;
      const price = Number(l.unit_price) || 0;
      const tax = Number(l.tax_rate) || 0;
      const lineSub = qty * price;
      acc.subtotal += lineSub;
      acc.tax += lineSub * (tax / 100);
      return acc;
    },
    { subtotal: 0, tax: 0 },
  );
  const disc = Number(discount) || 0;
  const grand = Math.max(0, computed.subtotal + computed.tax - disc);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setCorrelationId(undefined);
    if (!patient) { setError("Select a patient."); return; }
    if (lines.some((l) => !l.description.trim())) { setError("Every line needs a description."); return; }

    setSubmitting(true);
    try {
      const created = await api.post<{ id: string }>("/billing/invoices/", {
        patient,
        line_items: lines.map((l) => ({
          description: l.description,
          quantity: Number(l.quantity),
          unit_price: l.unit_price,
          tax_rate: l.tax_rate,
        })),
        discount_total: discount,
        due_date: dueDate || undefined,
        notes,
      });
      router.push(`/billing/${created.id}`);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.message);
        setCorrelationId(err.correlationId);
      } else {
        setError("Failed to create invoice.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  const selectCls = "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">New Invoice</h1>
          <p className="text-muted-foreground">Build an invoice with line items.</p>
        </div>

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
            {correlationId && <span className="mt-1 block text-xs opacity-70">Ref: {correlationId}</span>}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Patient</CardTitle></CardHeader>
            <CardContent>
              <select value={patient} onChange={(e) => setPatient(e.target.value)} className={selectCls} required>
                <option value="">Select patient...</option>
                {patients.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
              </select>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle>Line items</CardTitle>
              <Button type="button" variant="outline" size="sm" onClick={addLine}>
                <Icons.plus className="mr-1 h-4 w-4" /> Add line
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              {lines.map((l, i) => (
                <div key={i} className="grid grid-cols-12 items-end gap-2">
                  <div className="col-span-5 space-y-1">
                    {i === 0 && <Label className="text-xs">Description</Label>}
                    <Input value={l.description} onChange={(e) => setLine(i, "description", e.target.value)} placeholder="Service or item" />
                  </div>
                  <div className="col-span-2 space-y-1">
                    {i === 0 && <Label className="text-xs">Qty</Label>}
                    <Input type="number" min={1} value={l.quantity} onChange={(e) => setLine(i, "quantity", Number(e.target.value))} />
                  </div>
                  <div className="col-span-2 space-y-1">
                    {i === 0 && <Label className="text-xs">Price</Label>}
                    <Input type="number" min={0} step="0.01" value={l.unit_price} onChange={(e) => setLine(i, "unit_price", e.target.value)} />
                  </div>
                  <div className="col-span-2 space-y-1">
                    {i === 0 && <Label className="text-xs">Tax %</Label>}
                    <Input type="number" min={0} step="0.01" value={l.tax_rate} onChange={(e) => setLine(i, "tax_rate", e.target.value)} />
                  </div>
                  <div className="col-span-1">
                    {lines.length > 1 && (
                      <Button type="button" variant="ghost" size="sm" onClick={() => removeLine(i)}>
                        <Icons.x className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-3 pt-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="discount">Discount</Label>
                  <Input id="discount" type="number" min={0} step="0.01" value={discount} onChange={(e) => setDiscount(e.target.value)} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="due">Due date</Label>
                  <Input id="due" type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="notes">Notes</Label>
                <Input id="notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
              </div>
              <div className="rounded-md bg-muted p-3 text-sm">
                <div className="flex justify-between"><span>Subtotal</span><span>{computed.subtotal.toFixed(2)}</span></div>
                <div className="flex justify-between"><span>Tax</span><span>{computed.tax.toFixed(2)}</span></div>
                <div className="flex justify-between"><span>Discount</span><span>-{disc.toFixed(2)}</span></div>
                <div className="mt-1 flex justify-between border-t pt-1 font-semibold"><span>Total</span><span>{grand.toFixed(2)}</span></div>
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-2">
            <Button type="submit" disabled={submitting}>{submitting ? "Creating..." : "Create Invoice"}</Button>
            <Button type="button" variant="outline" onClick={() => router.push("/billing")}>Cancel</Button>
          </div>
        </form>
      </div>
    </DashboardShell>
  );
}

export default function NewInvoicePage() {
  return (
    <Suspense fallback={null}>
      <NewInvoiceInner />
    </Suspense>
  );
}
