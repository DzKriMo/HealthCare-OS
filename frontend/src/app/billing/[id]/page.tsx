"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, ApiRequestError } from "@/lib/api/client";

interface LineItem {
  description: string;
  quantity: number | string;
  unit_price: string;
  tax_rate: string;
}

interface InvoiceDetail {
  id: string;
  patient: string;
  patient_name: string;
  invoice_number: string;
  status: string;
  line_items: LineItem[];
  subtotal: string;
  tax_total: string;
  discount_total: string;
  grand_total: string;
  amount_paid: string;
  balance_due: string;
  is_paid: boolean;
  issued_date: string | null;
  due_date: string | null;
  paid_date: string | null;
  notes: string;
}

const METHODS = ["cash", "card", "transfer", "insurance", "other"];

export default function InvoiceDetailPage() {
  const router = useRouter();
  const params = useParams();
  const invoiceId = params.id as string;
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } =
    useAuthStore();

  const [invoice, setInvoice] = useState<InvoiceDetail | null>(null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");

  // Payment form
  const [payAmount, setPayAmount] = useState("");
  const [payMethod, setPayMethod] = useState("cash");
  const [payReference, setPayReference] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated && invoiceId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, invoiceId]);

  const load = async () => {
    setLoading(true);
    setLoadError("");
    try {
      const data = await api.get<InvoiceDetail>(`/billing/invoices/${invoiceId}/`);
      setInvoice(data);
      setPayAmount(data.balance_due);
    } catch {
      setLoadError("Failed to load invoice.");
    } finally {
      setLoading(false);
    }
  };
  const issue = async () => {
    setBusy(true);
    setActionError("");
    try {
      await api.post(`/billing/invoices/${invoiceId}/issue/`, {});
      await load();
    } catch (err) {
      setActionError(err instanceof ApiRequestError ? err.message : "Failed to issue invoice.");
    } finally {
      setBusy(false);
    }
  };

  const recordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setActionError("");
    if (!invoice) return;
    const amt = Number(payAmount);
    if (!amt || amt <= 0) {
      setActionError("Enter a payment amount greater than zero.");
      setBusy(false);
      return;
    }
    try {
      await api.post("/billing/payments/", {
        patient: invoice.patient,
        amount: payAmount,
        method: payMethod,
        reference: payReference,
        payment_date: new Date().toISOString(),
        allocations: [{ invoice_id: invoice.id, amount: payAmount }],
      });
      setPayReference("");
      await load();
    } catch (err) {
      setActionError(err instanceof ApiRequestError ? err.message : "Failed to record payment.");
    } finally {
      setBusy(false);
    }
  };

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  const money = (v: string | number) => Number(v || 0).toFixed(2);
  const canIssue = invoice?.status === "draft";
  const canPay = invoice && !["draft", "paid", "cancelled", "void"].includes(invoice.status) && Number(invoice.balance_due) > 0;

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-3xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/billing")}>
          ← Back to billing
        </Button>

        {loadError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {loadError}
            <Button variant="link" size="sm" onClick={load}>Retry</Button>
          </div>
        )}

        {loading && !invoice && <div className="h-60 animate-pulse rounded-lg bg-muted" />}

        {invoice && (
          <>
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-2xl font-bold">{invoice.invoice_number}</h1>
                <p className="text-muted-foreground">{invoice.patient_name}</p>
                {invoice.due_date && (
                  <p className="text-sm text-muted-foreground">
                    Due {new Date(invoice.due_date).toLocaleDateString()}
                  </p>
                )}
              </div>
              <span className="rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
                {invoice.status.replace("_", " ")}
              </span>
            </div>

            {actionError && (
              <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{actionError}</div>
            )}

            <Card>
              <CardHeader><CardTitle className="text-lg">Line items</CardTitle></CardHeader>
              <CardContent className="space-y-2 text-sm">
                {invoice.line_items?.map((l, i) => (
                  <div key={i} className="flex justify-between border-b pb-1 last:border-0">
                    <span>{l.description} <span className="text-muted-foreground">×{l.quantity}</span></span>
                    <span>{money(Number(l.unit_price) * Number(l.quantity))}</span>
                  </div>
                ))}
                <div className="space-y-1 pt-2">
                  <div className="flex justify-between"><span className="text-muted-foreground">Subtotal</span><span>{money(invoice.subtotal)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Tax</span><span>{money(invoice.tax_total)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Discount</span><span>-{money(invoice.discount_total)}</span></div>
                  <div className="flex justify-between border-t pt-1 font-semibold"><span>Total</span><span>{money(invoice.grand_total)}</span></div>
                  <div className="flex justify-between text-green-600"><span>Paid</span><span>{money(invoice.amount_paid)}</span></div>
                  <div className="flex justify-between font-semibold"><span>Balance due</span><span>{money(invoice.balance_due)}</span></div>
                </div>
              </CardContent>
            </Card>

            {canIssue && (
              <Card>
                <CardHeader><CardTitle className="text-lg">Draft</CardTitle></CardHeader>
                <CardContent>
                  <p className="mb-3 text-sm text-muted-foreground">
                    This invoice is a draft. Issue it to make it official and enable payments.
                  </p>
                  <Button onClick={issue} disabled={busy}>{busy ? "Issuing..." : "Issue invoice"}</Button>
                </CardContent>
              </Card>
            )}

            {canPay && (
              <Card>
                <CardHeader><CardTitle className="text-lg">Record payment</CardTitle></CardHeader>
                <CardContent>
                  <form onSubmit={recordPayment} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="amt">Amount</Label>
                      <Input id="amt" type="number" min={0} step="0.01" value={payAmount} onChange={(e) => setPayAmount(e.target.value)} />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="method">Method</Label>
                      <select id="method" value={payMethod} onChange={(e) => setPayMethod(e.target.value)}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                        {METHODS.map((m) => <option key={m} value={m}>{m}</option>)}
                      </select>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="ref">Reference</Label>
                      <Input id="ref" value={payReference} onChange={(e) => setPayReference(e.target.value)} placeholder="Txn / check #" />
                    </div>
                    <div className="sm:col-span-3">
                      <Button type="submit" disabled={busy}>{busy ? "Recording..." : "Record payment"}</Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            {invoice.notes && (
              <Card>
                <CardHeader><CardTitle className="text-lg">Notes</CardTitle></CardHeader>
                <CardContent className="text-sm">{invoice.notes}</CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </DashboardShell>
  );
}
