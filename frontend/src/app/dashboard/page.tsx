"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, user, fetchCurrentUser, logout } =
    useAuthStore();

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back, {user.first_name}. Here&apos;s your clinic at a glance.
          </p>
        </div>

        {/* Dashboard widgets — Sprint 6 */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <WidgetCard
            title="Today's Appointments"
            value="12"
            description="3 arriving soon"
          />
          <WidgetCard
            title="Patients Today"
            value="28"
            description="+5 from yesterday"
          />
          <WidgetCard
            title="Pending Invoices"
            value="$4,250"
            description="8 invoices overdue"
          />
          <WidgetCard
            title="Lab Results"
            value="3"
            description="Awaiting review"
          />
        </div>

        {/* Placeholder for role-aware widgets (Sprint 6) */}
        <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
          <p className="text-sm">
            Dashboard widgets will be configured per role in Sprint 6.
          </p>
          <p className="text-xs mt-1">
            Tenant: {user.tenant_slug} · Role: {user.role_name}
          </p>
        </div>
      </div>
    </DashboardShell>
  );
}

function WidgetCard({
  title,
  value,
  description,
}: {
  title: string;
  value: string;
  description: string;
}) {
  return (
    <div className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
      <div className="text-sm font-medium text-muted-foreground">{title}</div>
      <div className="mt-2 text-2xl font-bold">{value}</div>
      <div className="mt-1 text-xs text-muted-foreground">{description}</div>
    </div>
  );
}
