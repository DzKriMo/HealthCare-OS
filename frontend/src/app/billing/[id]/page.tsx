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
import { PaymentHistory } from "@/components/billing/payment-history";
import { api, ApiRequestError } from "@/lib/api/client";

interface LineItem { description: string; quantity: number | string; unit_price: string; tax_rate: string; }
interface InvoiceDetail {
  id: string; patient: string; patient_name: string; invoice_number: string;
  status: string; line_items: LineItem[]; subtotal: string; tax_total: string;
  discount_total: string; grand_total: string; amount_paid: string; balance_due: string;
  is_paid: boolean; issued_date: string | null; due_date: string | null;
  paid_date: string | null; notes: string; internal_notes: string;
}

const METHODS = ["cash", "card", "transfer", "insurance", "other"];
const STATUS_BADGES: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700", issued: "bg-blue-100 text-blue-700",
  partially_paid: "bg-yellow-100 text-yellow-700", paid: "bg-green-100 text-green-700",
  overdue: "bg-red-100 text-red-700", cancelled: "bg-gray-100 text-gray-500",
};

export default function InvoiceDetailPage() {
  const router = useRouter(); const params = useParams();
  const invoiceId = params.id as string;
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [invoice, setInvoice] = useState<InvoiceDetail | null>(null);
  const [loadError, setLoadError] = useState(""); const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false); const [actionError, setActionError] = useState("");
  const [payAmount, setPayAmount] = useState(""); const [payMethod, setPayMethod] = useState("cash"); const [payReference, setPayReference] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => { if (!authLoading && !isAuthenticated) router.push("/login"); }, [authLoading, isAuthenticated, router]);
  useEffect(() => { if (isAuthenticated && invoiceId) load(); }, [isAuthenticated, invoiceId]);

  const load = async () => {
    setLoading(true); setLoadError("");
    try { const d = await api.get<InvoiceDetail>(`/billing/invoices/${invoiceId}/`); setInvoice(d); setPayAmount(d.balance_due); }
    catch { setLoadError("Failed to load invoice."); } finally { setLoading(false); }
  };

  const issue = async () => {
    setBusy(true); setActionError("");
    try { await api.post(`/billing/invoices/${invoiceId}/issue/`, {}); await load(); }
    catch (err) { setActionError(err instanceof ApiRequestError ? err.message : "Failed."); }
    finally { setBusy(false); }
  };

  const recordPayment = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setActionError("");
    if (!invoice) return;
    const amt = Number(payAmount);
    if (!amt || amt <= 0) { setActionError("Enter a payment amount."); setBusy(false); return; }
    try {
      await api.post("/billing/payments/", {
        patient: invoice.patient, amount: payAmount, method: payMethod, reference: payReference,
        payment_date: new Date().toISOString(),
        allocations: [{ invoice_id: invoice.id, amount: payAmount }],
      });
      setPayReference(""); await load();
    } catch (err) { setActionError(err instanceof ApiRequestError ? err.message : "Failed."); }
    finally { setBusy(false); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  const money = (v: string | number) => Number(v || 0).toFixed(2);
  const canIssue = invoice?.status === "draft";
  const canPay = invoice && !["draft", "paid", "cancelled", "void"].includes(invoice.status) && Number(invoice.balance_due) > 0;
  const canEdit = invoice?.status === "draft";

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-4xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/billing")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
        </Button>

        {loadError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{loadError} <Button variant="link" size="sm" onClick={load}>Retry</Button></div>}
        {loading && !invoice && <SkeletonCard />}

        {invoice && (
          <>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold">{invoice.invoice_number}</h1>
                  <span className={`rounded-full px-3 py-1 text-sm font-medium ${STATUS_BADGES[invoice.status] || ""}`}>
                    {invoice.status.replace("_", " ")}
                  </span>
                </div>
                <p className="text-muted-foreground">{invoice.patient_name}</p>
                <div className="flex gap-4 text-sm text-muted-foreground mt-1">
                  {invoice.issued_date && <span>Issued: {new Date(invoice.issued_date).toLocaleDateString()}</span>}
                  {invoice.due_date && <span>Due: {new Date(invoice.due_date).toLocaleDateString()}</span>}
                  {invoice.paid_date && <span>Paid: {new Date(invoice.paid_date).toLocaleDateString()}</span>}
                </div>
              </div>
              <div className="flex gap-2">
                {invoice.balance_due > 0 && (
                  <Button variant="outline" onClick={() => router.push(`/billing/checkout?invoice_id=${invoice.id}`)}>
                    <Icons.creditCard className="mr-2 h-4 w-4" /> Pay Online
                  </Button>
                )}
                {canEdit && <Button variant="outline" onClick={() => router.push(`/billing/${invoice.id}/edit`)}><Icons.settings className="mr-2 h-4 w-4" /> Edit</Button>}
                <Button variant="outline" onClick={() => window.print()}><Icons.fileText className="mr-2 h-4 w-4" /> PDF</Button>
              </div>
            </div>

            {actionError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{actionError}</div>}

            <Card>
              <CardHeader><CardTitle className="text-lg">Line Items</CardTitle></CardHeader>
              <CardContent className="space-y-2 text-sm">
                {invoice.line_items?.map((l, i) => (
                  <div key={i} className="flex justify-between border-b pb-1 last:border-0">
                    <span>{l.description} <span className="text-muted-foreground">×{l.quantity}</span></span>
                    <span>${money(Number(l.unit_price) * Number(l.quantity))}</span>
                  </div>
                ))}
                <div className="space-y-1 pt-2">
                  <div className="flex justify-between"><span className="text-muted-foreground">Subtotal</span><span>${money(invoice.subtotal)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Tax</span><span>${money(invoice.tax_total)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Discount</span><span>-${money(invoice.discount_total)}</span></div>
                  <div className="flex justify-between border-t pt-1 font-semibold text-lg"><span>Total</span><span>${money(invoice.grand_total)}</span></div>
                  <div className="flex justify-between text-green-600"><span>Paid</span><span>${money(invoice.amount_paid)}</span></div>
                  <div className="flex justify-between font-semibold"><span>Balance due</span><span>${money(invoice.balance_due)}</span></div>
                </div>
              </CardContent>
            </Card>

            {canIssue && (
              <Card>
                <CardHeader><CardTitle className="text-lg">Draft</CardTitle></CardHeader>
                <CardContent>
                  <p className="mb-3 text-sm text-muted-foreground">Issue this invoice to make it official.</p>
                  <Button onClick={issue} disabled={busy}>{busy ? "Issuing..." : "Issue Invoice"}</Button>
                </CardContent>
              </Card>
            )}

            {canPay && (
              <Card>
                <CardHeader><CardTitle className="text-lg">Record Payment</CardTitle></CardHeader>
                <CardContent>
                  <form onSubmit={recordPayment} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                    <div className="space-y-1.5">
                      <Label>Amount</Label>
                      <Input type="number" min={0} step="0.01" value={payAmount} onChange={(e) => setPayAmount(e.target.value)} />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Method</Label>
                      <select value={payMethod} onChange={(e) => setPayMethod(e.target.value)}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                        {METHODS.map((m) => <option key={m} value={m}>{m}</option>)}
                      </select>
                    </div>
                    <div className="space-y-1.5">
                      <Label>Reference</Label>
                      <Input value={payReference} onChange={(e) => setPayReference(e.target.value)} placeholder="Txn #" />
                    </div>
                    <div className="sm:col-span-3">
                      <Button type="submit" disabled={busy}>{busy ? "Recording..." : "Record Payment"}</Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            <PaymentHistory patientId={invoice.patient} />

            {invoice.notes && (
              <Card>
                <CardHeader><CardTitle className="text-lg">Notes</CardTitle></CardHeader>
                <CardContent className="text-sm whitespace-pre-wrap">{invoice.notes}</CardContent>
              </Card>
            )}

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => router.push(`/patients/${invoice.patient}`)}>
                <Icons.users className="mr-2 h-4 w-4" /> View Patient
              </Button>
            </div>
          </>
        )}
      </div>
    </DashboardShell>
  );
}
