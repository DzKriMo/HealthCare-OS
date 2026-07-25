"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Icons } from "@/components/icons";

export default function PaymentCancelPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const invoiceId = searchParams.get("invoice_id");
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  if (authLoading || !user) return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-lg py-12">
        <Card>
          <CardContent className="flex flex-col items-center py-12 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-yellow-100">
              <Icons.x className="h-8 w-8 text-yellow-600" />
            </div>
            <h2 className="text-2xl font-bold">Payment Cancelled</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Your payment was not processed. No charges were made.
            </p>
            <div className="mt-6 flex gap-3">
              {invoiceId && (
                <Button onClick={() => router.push(`/billing/checkout?invoice_id=${invoiceId}`)}>
                  Try Again
                </Button>
              )}
              <Button variant="outline" onClick={() => router.push("/billing")}>
                Go to Billing
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
