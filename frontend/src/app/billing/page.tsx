"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonTable } from "@/components/ui/skeleton";
import { RevenueWidgets } from "@/components/billing/revenue-widgets";
import { api } from "@/lib/api/client";

interface InvoiceSummary {
  id: string; patient_name: string; invoice_number: string;
  status: string; grand_total: string; amount_paid: string;
  balance_due: string; due_date: string | null; created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700", issued: "bg-blue-100 text-blue-700",
  partially_paid: "bg-yellow-100 text-yellow-700", paid: "bg-green-100 text-green-700",
  overdue: "bg-red-100 text-red-700", cancelled: "bg-gray-100 text-gray-500",
  void: "bg-gray-100 text-gray-500",
};

const STATUSES = ["", "draft", "issued", "partially_paid", "paid", "overdue", "cancelled"];

export default function BillingPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [invoices, setInvoices] = useState<InvoiceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchPatient, setSearchPatient] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => { if (isAuthenticated) load(); }, [isAuthenticated, statusFilter]);

  const load = async () => {
    setLoading(true);
    try {
      const q = statusFilter ? `?status=${statusFilter}` : "";
      const data = await api.get<{ results: InvoiceSummary[] }>(`/billing/invoices/${q}`);
      setInvoices(data.results);
    } catch { setPageError("Failed to load invoices."); }
    finally { setLoading(false); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  const money = (v: string | number) => Number(v || 0).toFixed(2);
  const selectCls = "flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm";

  const filtered = searchPatient
    ? invoices.filter((i) => i.patient_name.toLowerCase().includes(searchPatient.toLowerCase()))
    : invoices;

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Billing</h1>
            <p className="text-muted-foreground">{invoices.length} invoices</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/billing/pos")}>
              <Icons.creditCard className="mr-2 h-4 w-4" /> POS
            </Button>
            <Button onClick={() => router.push("/billing/new")}>
              <Icons.plus className="mr-2 h-4 w-4" /> New Invoice
            </Button>
          </div>
        </div>

        <RevenueWidgets />

        {pageError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>}

        <div className="flex gap-2 flex-wrap">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className={selectCls}>
            {STATUSES.map((s) => <option key={s} value={s}>{s || "All statuses"}</option>)}
          </select>
          <Input placeholder="Search by patient name..." value={searchPatient} onChange={(e) => setSearchPatient(e.target.value)} className="max-w-xs" />
        </div>

        {loading ? <SkeletonTable rows={8} /> : (
          <div className="space-y-2">
            {filtered.map((inv) => (
              <Card key={inv.id} className="cursor-pointer transition-colors hover:border-primary" onClick={() => router.push(`/billing/${inv.id}`)}>
                <CardContent className="flex items-center justify-between p-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{inv.invoice_number}</span>
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[inv.status] || ""}`}>
                        {inv.status.replace("_", " ")}
                      </span>
                    </div>
                    <p className="truncate text-sm text-muted-foreground">{inv.patient_name}</p>
                    {inv.due_date && <p className="text-xs text-muted-foreground">Due {new Date(inv.due_date).toLocaleDateString()}</p>}
                  </div>
                  <div className="ml-4 text-right">
                    <p className="font-semibold">${money(inv.grand_total)}</p>
                    {Number(inv.balance_due) > 0 && <p className="text-xs text-muted-foreground">Due: ${money(inv.balance_due)}</p>}
                  </div>
                </CardContent>
              </Card>
            ))}
            {filtered.length === 0 && (
              <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground">
                <Icons.creditCard className="mx-auto mb-3 h-8 w-8" />
                <p>No invoices found.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
