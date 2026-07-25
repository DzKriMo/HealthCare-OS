"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";
import { format } from "date-fns";

interface InvoiceData {
  id: string; invoice_number: string; grand_total: string;
  balance_due: string; status: string; patient_name: string;
}

export default function CheckoutPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const invoiceId = searchParams.get("invoice_id");
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [invoice, setInvoice] = useState<InvoiceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated && invoiceId) loadInvoice();
  }, [isAuthenticated, invoiceId]);

  const loadInvoice = async () => {
    try {
      const data = await api.get<InvoiceData>(`/billing/invoices/${invoiceId}/`);
      setInvoice(data);
    } catch { setError("Invoice not found."); }
    finally { setLoading(false); }
  };

  const handleStripeCheckout = async () => {
    if (!invoice) return;
    setProcessing(true);
    setError("");
    try {
      const res = await api.post("/billing/checkout/", {
        invoice_id: invoice.id,
        gateway: "stripe",
        success_url: `${window.location.origin}/billing/success?invoice_id=${invoice.id}`,
        cancel_url: `${window.location.origin}/billing/cancel?invoice_id=${invoice.id}`,
      });
      if (res.checkout_url) {
        window.location.href = res.checkout_url;
      } else {
        setError("Failed to create checkout session.");
      }
    } catch {
      setError("Payment gateway error. Please try again.");
    } finally { setProcessing(false); }
  };

  if (authLoading || !user) return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-lg space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push(invoiceId ? `/billing/${invoiceId}` : "/billing")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
        </Button>

        <Card>
          <CardHeader><CardTitle>Checkout</CardTitle></CardHeader>
          <CardContent className="space-y-6">
            {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}

            {loading ? (
              <div className="h-40 animate-pulse rounded-lg bg-muted" />
            ) : invoice ? (
              <>
                <div className="rounded-lg border p-4 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Invoice</span>
                    <span className="text-sm font-medium">{invoice.invoice_number}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Patient</span>
                    <span className="text-sm">{invoice.patient_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Status</span>
                    <span className="text-sm capitalize">{invoice.status.replace("_", " ")}</span>
                  </div>
                  <div className="border-t pt-2 flex justify-between">
                    <span className="font-semibold">Amount Due</span>
                    <span className="text-xl font-bold">${parseFloat(invoice.balance_due).toFixed(2)}</span>
                  </div>
                </div>

                <div className="space-y-3">
                  <Button className="w-full" size="lg" onClick={handleStripeCheckout} disabled={processing}>
                    {processing ? (
                      <>Processing...</>
                    ) : (
                      <><Icons.creditCard className="mr-2 h-5 w-5" /> Pay with Card (Stripe)</>
                    )}
                  </Button>
                  <p className="text-center text-xs text-muted-foreground">
                    Secure payment processed by Stripe. Your card details are never stored on our servers.
                  </p>
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Invoice not found.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
