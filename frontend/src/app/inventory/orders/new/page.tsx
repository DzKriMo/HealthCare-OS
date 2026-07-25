"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Icons } from "@/components/icons";
import { PurchaseOrderForm } from "@/components/inventory/purchase-order-form";
import { api, ApiRequestError } from "@/lib/api/client";

export default function NewPurchaseOrderPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  const handleSubmit = async (data: Parameters<typeof api.post>[1]) => {
    setSubmitting(true); setError("");
    try {
      const created = await api.post<{ id: string }>("/inventory/orders/", data);
      router.push(`/inventory/orders/${created.id}`);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Failed to create order.");
    } finally { setSubmitting(false); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-3xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/inventory/orders")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
        </Button>

        <div>
          <h1 className="text-3xl font-bold tracking-tight">New Purchase Order</h1>
          <p className="text-muted-foreground">Create a purchase order to replenish stock.</p>
        </div>

        {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}

        <PurchaseOrderForm onSubmit={handleSubmit} loading={submitting} />
      </div>
    </DashboardShell>
  );
}
