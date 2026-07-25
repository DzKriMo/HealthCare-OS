"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";

interface InvoiceSummary {
  id: string;
  patient: string;
  patient_name: string;
  invoice_number: string;
  status: string;
  grand_total: string;
  amount_paid: string;
  balance_due: string;
  due_date: string | null;
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-muted text-muted-foreground",
  issued: "bg-blue-100 text-blue-700",
  partially_paid: "bg-yellow-100 text-yellow-700",
  paid: "bg-green-100 text-green-700",
  overdue: "bg-red-100 text-red-700",
  cancelled: "bg-muted text-muted-foreground",
  void: "bg-muted text-muted-foreground",
};

export default function BillingPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } =
    useAuthStore();

  const [invoices, setInvoices] = useState<InvoiceSummary[]>([]);
  const [pageError, setPageError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const load = async () => {
    try {
      const data = await api.get<{ results: InvoiceSummary[] }>("/billing/invoices/");
      setInvoices(data.results);
    } catch {
      setPageError("Failed to load invoices.");
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

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Billing</h1>
            <p className="text-muted-foreground">Invoices and payments</p>
          </div>
          <Button onClick={() => router.push("/billing/new")}>
            <Icons.plus className="mr-2 h-4 w-4" /> New invoice
          </Button>
        </div>

        {pageError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>
        )}

        {invoices.length === 0 && !pageError && (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              No invoices yet.{" "}
              <button className="underline" onClick={() => router.push("/billing/new")}>
                Create one
              </button>
            </CardContent>
          </Card>
        )}

        <div className="space-y-2">
          {invoices.map((inv) => (
            <Card
              key={inv.id}
              className="cursor-pointer transition-colors hover:bg-muted/50"
              onClick={() => router.push(`/billing/${inv.id}`)}
            >
              <CardContent className="flex items-center justify-between py-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{inv.invoice_number}</span>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[inv.status] ?? "bg-muted text-muted-foreground"}`}>
                      {inv.status.replace("_", " ")}
                    </span>
                  </div>
                  <p className="truncate text-sm text-muted-foreground">{inv.patient_name}</p>
                  {inv.due_date && (
                    <p className="text-xs text-muted-foreground">
                      Due {new Date(inv.due_date).toLocaleDateString()}
                    </p>
                  )}
                </div>
                <div className="ml-4 text-right">
                  <p className="font-semibold">{money(inv.grand_total)}</p>
                  {Number(inv.balance_due) > 0 && (
                    <p className="text-xs text-muted-foreground">
                      Balance: {money(inv.balance_due)}
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </DashboardShell>
  );
}
