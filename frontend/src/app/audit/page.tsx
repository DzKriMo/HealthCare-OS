"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardContent } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { Input } from "@/components/ui/input";
import { SkeletonTable } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";

export default function AuditPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } = useAuthStore();
  const [events, setEvents] = useState<{ id: string; action: string; entity_type: string; created_at: string; actor_name?: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) {
      api.get<{ results: typeof events }>("/audit/")
        .then((d) => setEvents(d.results))
        .catch(() => setError("Failed to load audit log."))
        .finally(() => setLoading(false));
    }
  }, [isAuthenticated]);

  if (isLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  return (
    <DashboardShell user={user} onLogout={logout} breadcrumbs={[{ label: "Audit Logs" }]}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Audit Logs</h1>
          <p className="text-muted-foreground">Immutable record of all sensitive actions</p>
        </div>
        <Input placeholder="Search audit log..." className="max-w-md" />
        {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}
        {loading ? <SkeletonTable rows={5} /> : (
          <div className="space-y-1">
            {events.map((ev) => (
              <Card key={ev.id}>
                <CardContent className="flex items-center gap-4 py-3 text-sm">
                  <Icons.shield className="h-4 w-4 text-muted-foreground shrink-0" />
                  <span className="font-mono text-xs text-muted-foreground w-32 shrink-0">
                    {new Date(ev.created_at).toLocaleString()}
                  </span>
                  <span className="font-medium capitalize">{ev.action.replace("_", " ")}</span>
                  <span className="text-muted-foreground">{ev.entity_type}</span>
                  <span className="text-muted-foreground ml-auto">{ev.actor_name || "—"}</span>
                </CardContent>
              </Card>
            ))}
            {events.length === 0 && (
              <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground">
                <Icons.shield className="mx-auto mb-3 h-8 w-8" />
                <p>No audit events recorded yet.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
